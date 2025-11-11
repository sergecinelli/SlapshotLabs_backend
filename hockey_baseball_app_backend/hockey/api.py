import datetime
import os
import re
from django.conf import settings
from django.db.models import Q
from django.db.models.deletion import RestrictedError
from django.forms.models import model_to_dict
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from ninja import File, Router, PatchDict
from ninja.files import UploadedFile
from django.contrib.auth import get_user_model
from django.http import HttpRequest, FileResponse
from django.core.files import File as FileSaver
from django.core.files.storage import default_storage
from faker import Faker
import faker.providers
from faker_animals import AnimalsProvider

from hockey.utils.constants import GOALIE_POSITION_NAME, NO_GOALIE_NAME, EventName, GameStatus, get_constant_class_int_choices

from .schemas import (ArenaOut, ArenaRinkOut, DefensiveZoneExitIn, DefensiveZoneExitOut, GameDashboardOut, GameEventIn, GameEventOut, GameExtendedOut, GameGoalieOut,
                      GameIn, GameLiveDataOut, GameOut, GamePeriodOut, GamePlayerOut, GamePlayersIn, GamePlayersOut, GameTypeOut, GameTypeRecordOut, GoalieSeasonOut,
                      GoalieSeasonsGet, HighlightIn, HighlightOut, HighlightReelIn, HighlightReelFullIn, HighlightReelListOut, HighlightReelOut, ObjectIdName, Message, ObjectId, OffensiveZoneEntryIn, OffensiveZoneEntryOut, PlayerPositionOut, GoalieIn,
                      GoalieOut, PlayerIn, PlayerOut, PlayerSeasonOut, PlayerSeasonsGet, SeasonIn, SeasonOut, ShotsIn, ShotsOut,
                      TeamIn, TeamOut, TeamSeasonIn, TeamSeasonOut, TurnoversIn, TurnoversOut)
from .models import (Arena, ArenaRink, CustomEvents, DefensiveZoneExit, Division, Game, GameEventName, GameEvents, GameEventsAnalysisQueue,
                     GameGoalie, GamePeriod, GamePlayer, GameType, Goalie, GoalieSeason, Highlight, HighlightReel, OffensiveZoneEntry, Player,
                     PlayerPosition, PlayerSeason, PlayerTransaction, Season, ShotType, Shots, Team, TeamLevel, TeamSeason, GameTypeName, Turnovers)
from .utils import api_response_templates as resp
from .utils.db_utils import (create_highlight, form_game_goalie_out, form_game_dashboard_game_out, form_game_player_out, form_goalie_out, form_player_out, get_current_season,
                             get_game_current_goalies, get_no_goalie, update_game_faceoffs_from_event,
                             update_game_shots_from_event, update_game_turnovers_from_event)

router = Router(tags=["Hockey"])

User = get_user_model()

# region Goalie, player

@router.get('/player-position/list', response=list[PlayerPositionOut])
def get_player_positions(request: HttpRequest):
    positions = PlayerPosition.objects.exclude(name=GOALIE_POSITION_NAME).all()
    return positions

@router.get('/goalie/list', response=list[GoalieOut])
def get_goalies(request: HttpRequest, team_id: int | None = None):
    current_season = get_current_season()
    goalies_out: list[GoalieOut] = []
    goalies = Goalie.objects.all()
    if team_id is not None:
        goalies = goalies.filter(player__team_id=team_id)
    for goalie in goalies:
        goalies_out.append(form_goalie_out(goalie, current_season))
    return goalies_out

@router.get('/goalie/{goalie_id}', response=GoalieOut)
def get_goalie(request: HttpRequest, goalie_id: int):
    goalie = get_object_or_404(Goalie, pk=goalie_id)
    current_season = get_current_season()
    return form_goalie_out(goalie, current_season)

@router.get('/goalie/{goalie_id}/photo', response=bytes)
def get_goalie_photo(request: HttpRequest, goalie_id: int):
    goalie = get_object_or_404(Player, id=goalie_id, position__name=GOALIE_POSITION_NAME)
    return FileResponse(goalie.photo.open())

@router.post('/goalie', response={200: ObjectId, 400: Message, 503: Message})
def add_goalie(request: HttpRequest, data: GoalieIn, photo: File[UploadedFile] = None):
    try:
        with transaction.atomic(using='hockey'):
            goalie = Player(position=PlayerPosition.objects.get(name=GOALIE_POSITION_NAME), **data.dict())
            goalie.photo = photo
            goalie.save()
            Goalie.objects.create(player=goalie)
    except IntegrityError as e:
        return resp.entry_already_exists("Goalie", str(e))
    return {"id": goalie.id}

@router.patch("/goalie/{goalie_id}", response={204: None, 403: Message})
def update_goalie(request: HttpRequest, goalie_id: int, data: PatchDict[GoalieIn], photo: File[UploadedFile] = None):
    goalie = get_object_or_404(Player, id=goalie_id, position__name=GOALIE_POSITION_NAME)
    if goalie.first_name == NO_GOALIE_NAME:
        return 403, {"message": "This goalie is used in case of no goalie in net, so it cannot be updated."}
    old_team_id = goalie.team_id
    for attr, value in data.items():
        setattr(goalie, attr, value)
    if photo is not None:
        goalie.photo = photo
    try:
        with transaction.atomic(using='hockey'):
            if old_team_id != goalie.team_id:
                PlayerTransaction.objects.create(player=goalie, season=get_current_season(), team=goalie.team,
                    number=goalie.number, description=f"Transferred to \"{(goalie.team.name if goalie.team is not None else 'free agent')}\"",
                    date=datetime.datetime.now(datetime.timezone.utc).date())
            goalie.save()
    except IntegrityError:
        return resp.entry_already_exists("Goalie")
    return 204, None

@router.delete("/goalie/{goalie_id}", response={204: None, 403: Message})
def delete_goalie(request: HttpRequest, goalie_id: int):
    goalie = get_object_or_404(Player, id=goalie_id, position__name=GOALIE_POSITION_NAME)
    if goalie.first_name == NO_GOALIE_NAME:
        return 403, {"message": "This goalie is used in case of no goalie in net, so they cannot be deleted."}
    try:
        goalie.delete()
    except RestrictedError as e:
        return 403, {"message": "This goalie is used in games, so they cannot be deleted.", "details": str(e)}
    return 204, None

@router.post("/goalie/seasons", response=list[GoalieSeasonOut])
def get_goalie_seasons(request: HttpRequest, data: GoalieSeasonsGet):
    return GoalieSeason.objects.filter(goalie_id=data.goalie_id, season_id__in=data.season_ids)

@router.get('/player/list', response=list[PlayerOut])
def get_players(request: HttpRequest, team_id: int | None = None):
    current_season = get_current_season()
    players_out: list[PlayerOut] = []
    players = Player.objects.exclude(position__name=GOALIE_POSITION_NAME)
    if team_id is not None:
        players = players.filter(team_id=team_id)
    for player in players:
        players_out.append(form_player_out(player, current_season))
    return players_out

@router.get('/player/{player_id}', response=PlayerOut)
def get_player(request: HttpRequest, player_id: int):
    player = get_object_or_404(Player.objects.exclude(position__name=GOALIE_POSITION_NAME), id=player_id)
    current_season = get_current_season()
    return form_player_out(player, current_season)

@router.get('/player/{player_id}/photo', response=bytes)
def get_player_photo(request: HttpRequest, player_id: int):
    player = get_object_or_404(Player.objects.exclude(position__name=GOALIE_POSITION_NAME), id=player_id)
    return FileResponse(player.photo.open())

@router.post('/player', response={200: ObjectId, 400: Message})
def add_player(request: HttpRequest, data: PlayerIn, photo: File[UploadedFile] = None):
    try:
        if data.position_id == PlayerPosition.objects.get(name=GOALIE_POSITION_NAME).id:
            return 400, {"message": "Goalies are not added through this endpoint."}
        player = Player(**data.dict())
        player.photo = photo
        player.save()
    except IntegrityError as e:
        return resp.entry_already_exists("Player", str(e))
    return {"id": player.id}

@router.patch("/player/{player_id}", response={204: None})
def update_player(request: HttpRequest, player_id: int, data: PatchDict[PlayerIn], photo: File[UploadedFile] = None):
    player = get_object_or_404(Player.objects.exclude(position__name=GOALIE_POSITION_NAME), id=player_id)
    old_team_id = player.team_id
    for attr, value in data.items():
        setattr(player, attr, value)
    if photo is not None:
        player.photo = photo
    try:
        with transaction.atomic(using='hockey'):
            if old_team_id != player.team_id:
                PlayerTransaction.objects.create(player=player, season=get_current_season(), team=player.team,
                number=player.number, description=f"Transferred to \"{(player.team.name if player.team is not None else 'free agent')}\"",
                date=datetime.datetime.now(datetime.timezone.utc).date())
            player.save()
    except IntegrityError:
        return resp.entry_already_exists("Player")
    return 204, None

@router.delete("/player/{player_id}", response={204: None, 403: Message})
def delete_player(request: HttpRequest, player_id: int):
    player = get_object_or_404(Player.objects.exclude(position__name=GOALIE_POSITION_NAME), id=player_id)
    try:
        player.delete()
    except RestrictedError as e:
        return 403, {"message": "This player is used in games, so they cannot be deleted.", "details": str(e)}
    return 204, None

@router.post("/player/seasons", response=list[PlayerSeasonOut])
def get_player_seasons(request: HttpRequest, data: PlayerSeasonsGet):
    return PlayerSeason.objects.filter(player_id=data.player_id, season_id__in=data.season_ids)

# endregion

# region Team, season

@router.get('/division/list', response=list[ObjectIdName])
def get_divisions(request: HttpRequest):
    divisions = Division.objects.all()
    return divisions

@router.get('/team-level/list', response=list[ObjectIdName])
def get_team_levels(request: HttpRequest):
    levels = TeamLevel.objects.all()
    return levels

@router.get('/team/list', response=list[TeamOut])
def get_teams(request: HttpRequest):
    teams = Team.objects.all()
    return teams

@router.get('/team/{team_id}', response=TeamOut)
def get_team(request: HttpRequest, team_id: int):
    team = get_object_or_404(Team, id=team_id)
    return team

@router.get('/team/{team_id}/logo', response=bytes)
def get_team_logo(request: HttpRequest, team_id: int):
    team = get_object_or_404(Team, id=team_id)
    return FileResponse(team.logo.open())

@router.post('/team', response={200: ObjectId, 400: Message})
def add_team(request: HttpRequest, data: TeamIn, logo: File[UploadedFile] = None):
    try:
        team = Team(**data.dict())
        team.logo = logo
        team.save()
    except IntegrityError as e:
        return resp.entry_already_exists("Team")
    return {"id": team.id}

@router.patch("/team/{team_id}", response={204: None})
def update_team(request: HttpRequest, team_id: int, data: PatchDict[TeamIn], logo: File[UploadedFile] = None):
    team = get_object_or_404(Team, id=team_id)
    for attr, value in data.items():
        setattr(team, attr, value)
    if logo is not None:
        team.logo = logo
    try:
        team.save()
    except IntegrityError:
        return resp.entry_already_exists("Team")
    return 204, None

@router.delete("/team/{team_id}", response={204: None})
def delete_team(request: HttpRequest, team_id: int):
    team = get_object_or_404(Team, id=team_id)
    team.delete()
    return 204, None

@router.get('/season/list', response=list[SeasonOut])
def get_seasons(request: HttpRequest):
    seasons = Season.objects.all()
    return seasons

@router.get('/season/{season_id}', response=SeasonOut)
def get_season(request: HttpRequest, season_id: int):
    season = get_object_or_404(Season, id=season_id)
    return season

@router.post('/season', response={200: ObjectId, 400: Message})
def add_season(request: HttpRequest, data: SeasonIn):
    try:
        if not re.match(r'^\d{4} / \d{4}$', data.name):
            return 400, {"message": "Season name must be in the format 'YYYY / YYYY'."}
        season = Season.objects.create(**data.dict())
    except IntegrityError as e:
        return resp.entry_already_exists("Season", str(e))
    return {"id": season.id}

@router.patch("/season/{season_id}", response={204: None})
def update_season(request: HttpRequest, season_id: int, data: PatchDict[SeasonIn]):
    if not re.match(r'^\d{4} / \d{4}$', data.name):
        return 400, {"message": "Season name must be in the format 'YYYY / YYYY'."}
    season = get_object_or_404(Season, id=season_id)
    for attr, value in data.items():
        setattr(season, attr, value)
    season.save()
    return 204, None

@router.delete("/season/{season_id}", response={204: None})
def delete_season(request: HttpRequest, season_id: int):
    season = get_object_or_404(Season, id=season_id)
    season.delete()
    return 204, None

@router.get('/team-season/list', response=list[TeamSeasonOut],
            description="Returns the last `limit` team season results for the given team, or for all teams if no team is specified.")
def get_team_seasons(request: HttpRequest, team_id: int | None = None, limit: int = 2):
    team_seasons = TeamSeason.objects.exclude(season__start_date__gt=datetime.datetime.now(datetime.timezone.utc).date())
    if team_id is not None:
        team_seasons = team_seasons.filter(team_id=team_id)
    team_seasons = team_seasons.order_by('-season__start_date')[:limit]
    return team_seasons

@router.get('/team-season/{team_season_id}', response=TeamSeasonOut)
def get_team_season(request: HttpRequest, team_season_id: int):
    team_season = get_object_or_404(TeamSeason, id=team_season_id)
    return team_season

@router.post('/team-season', response=ObjectId)
def add_team_season(request: HttpRequest, data: TeamSeasonIn):
    try:
        team_season = TeamSeason.objects.create(**data.dict())
    except IntegrityError as e:
        return resp.entry_already_exists("Team season", str(e))
    return {"id": team_season.id}

@router.patch("/team-season/{team_season_id}", response={204: None})
def update_team_season(request: HttpRequest, team_season_id: int, data: PatchDict[TeamSeasonIn]):
    team_season = get_object_or_404(TeamSeason, id=team_season_id)
    for attr, value in data.items():
        setattr(team_season, attr, value)
    team_season.save()
    return 204, None

@router.delete("/team-season/{team_season_id}", response={204: None})
def delete_team_season(request: HttpRequest, team_season_id: int):
    team_season = get_object_or_404(TeamSeason, id=team_season_id)
    team_season.delete()
    return 204, None

# endregion

# region Game

@router.get('/arena/list', response=list[ArenaOut])
def get_arenas(request: HttpRequest):
    arenas = Arena.objects.all()
    return arenas

@router.get('/arena-rink/list', response=list[ArenaRinkOut])
def get_arena_rinks(request: HttpRequest):
    arena_rinks = ArenaRink.objects.all()
    return arena_rinks

@router.get('/game-type/list', response=list[GameTypeOut])
def get_game_types(request: HttpRequest):
    game_types = GameType.objects.all()
    game_types_out = []
    for game_type in game_types:
        game_type_out = GameTypeOut(id=game_type.id, name=game_type.name, game_type_names=[
            ObjectIdName(id=game_type_name.id, name=game_type_name.name)
            for game_type_name in game_type.gametypename_set.filter(is_actual=True)])
        game_types_out.append(game_type_out)
    return game_types_out

@router.get('/game-period/list', response=list[GamePeriodOut])
def get_game_periods(request: HttpRequest):
    game_periods = GamePeriod.objects.order_by('order')
    return game_periods

@router.get('/game/list', response=list[GameOut])
def get_games(request: HttpRequest, on_now: bool = False):
    games = Game.objects.exclude(is_deprecated=True).select_related('rink', 'game_type_name')
    if on_now:
        games = games.filter(status=2)
    return games.order_by('-date').all()

@router.get('/game/list/dashboard', response=GameDashboardOut)
def get_games_dashboard(request: HttpRequest, limit: int = 5, team_id: int | None = None):
    upcoming_games_qs = Game.objects.exclude(is_deprecated=True).filter(status=1).select_related('rink', 'game_type_name').order_by('date')
    previous_games_qs = Game.objects.exclude(is_deprecated=True).filter(status=3).select_related('rink', 'game_type_name').order_by('-date')

    if team_id is not None:
        upcoming_games_qs = upcoming_games_qs.filter(Q(home_team_id=team_id) | Q(away_team_id=team_id))
        previous_games_qs = previous_games_qs.filter(Q(home_team_id=team_id) | Q(away_team_id=team_id))

    upcoming_games = [form_game_dashboard_game_out(game) for game in upcoming_games_qs[:limit]]
    previous_games = [form_game_dashboard_game_out(game) for game in previous_games_qs[:limit]]

    return GameDashboardOut(upcoming_games=upcoming_games, previous_games=previous_games)

@router.get('/game/{game_id}', response=GameOut)
def get_game(request: HttpRequest, game_id: int):
    game = get_object_or_404(Game.objects.select_related('rink', 'game_type_name'), id=game_id)
    return game

@router.get('/game/{game_id}/extra', response=GameExtendedOut)
def get_game_extra(request: HttpRequest, game_id: int):
    """Returns a game with extra information for the Live Dashboard."""
    game = get_object_or_404(Game.objects.select_related('rink', 'game_type_name'), id=game_id)
    game_type_games = Game.objects.filter(game_type=game.game_type, season=game.season).\
        filter(Q(home_team_id=game.home_team_id) | Q(away_team_id=game.away_team_id)).exclude(id=game_id)
    if game.game_type_name is not None:
        game_type_games = game_type_games.filter(game_type_name=game.game_type_name)
    home_team_record = GameTypeRecordOut(wins=0, losses=0, ties=0)
    away_team_record = GameTypeRecordOut(wins=0, losses=0, ties=0)
    for game_type_game in game_type_games:
        if game_type_game.home_team_id == game.home_team_id:
            if game_type_game.home_goals > game_type_game.away_goals:
                home_team_record.wins += 1
            elif game_type_game.home_goals < game_type_game.away_goals:
                home_team_record.losses += 1
            else:
                home_team_record.ties += 1
        elif game_type_game.away_team_id == game.away_team_id:
            if game_type_game.away_goals > game_type_game.home_goals:
                away_team_record.wins += 1
            elif game_type_game.away_goals < game_type_game.home_goals:
                away_team_record.losses += 1
            else:
                away_team_record.ties += 1
    return GameExtendedOut(id=game.id, home_team_id=game.home_team_id, home_start_goalie_id=game.home_start_goalie_id,
                           home_goals=game.home_goals, away_team_id=game.away_team_id, away_start_goalie_id=game.away_start_goalie_id,
                           away_goals=game.away_goals,
                           game_type_id=game.game_type_id, game_period_id=game.game_period_id,
                           game_type_name=game.game_type_name_str, status=game.status,
                           date=game.date, time=game.time, season_id=game.season_id, rink_id=game.rink_id, arena_id=game.arena_id,
                           home_team_game_type_record=home_team_record, away_team_game_type_record=away_team_record)

@router.post('/game', response={200: GameOut, 400: Message, 503: Message})
def add_game(request: HttpRequest, data: GameIn):
    try:
        game_season = get_current_season(data.date)
        if game_season is None:
            return 503, {"message": "No current season found."}
        if data.status not in [status[0] for status in get_constant_class_int_choices(GameStatus)]:
            return 400, {"message": f"Invalid status: {data.status}"}
        if data.game_type_id in [game_type.id for game_type in GameType.objects.filter(gametypename__is_actual=True)] and data.game_type_name_id is None:
            return 400, {"message": "If game type has names, game type name must be provided."}
        with transaction.atomic(using='hockey'):
            home_defensive_zone_exit = DefensiveZoneExit.objects.create()
            home_offensive_zone_entry = OffensiveZoneEntry.objects.create()
            home_shots = Shots.objects.create()
            home_turnovers = Turnovers.objects.create()
            away_defensive_zone_exit = DefensiveZoneExit.objects.create()
            away_offensive_zone_entry = OffensiveZoneEntry.objects.create()
            away_shots = Shots.objects.create()
            away_turnovers = Turnovers.objects.create()
            if data.home_start_goalie_id is None:
                data.home_start_goalie_id = get_no_goalie().player_id
            if data.away_start_goalie_id is None:
                data.away_start_goalie_id = get_no_goalie().player_id
            game = Game.objects.create(home_defensive_zone_exit=home_defensive_zone_exit,
                        home_offensive_zone_entry=home_offensive_zone_entry,
                        home_shots=home_shots,
                        home_turnovers=home_turnovers,
                        away_defensive_zone_exit=away_defensive_zone_exit,
                        away_offensive_zone_entry=away_offensive_zone_entry,
                        away_shots=away_shots,
                        away_turnovers=away_turnovers,
                        season=game_season,
                        **{k: v for k, v in data.dict().items() if k not in ["home_goalies", "away_goalies", "home_players", "away_players"]})
            game.home_goalies.set(data.home_goalies)
            game.away_goalies.set(data.away_goalies)
            game.home_players.set(data.home_players)
            game.away_players.set(data.away_players)
            game.save()
            # if data.status == 3:
            #     GameEventsAnalysisQueue.objects.create(game=game, action=1)
    except IntegrityError as e:
        return resp.entry_already_exists("Game", str(e))
    game = Game.objects.get(id=game.id)
    return game

@router.patch("/game/{game_id}", response={204: None, 400: Message})
def update_game(request: HttpRequest, game_id: int, data: PatchDict[GameIn]):
    game = get_object_or_404(Game, id=game_id)
    data_status = data.get('status')
    if data_status is not None and data_status not in [status[0] for status in get_constant_class_int_choices(GameStatus)]:
        return 400, {"message": f"Invalid status: {data_status}"}
    if data.get('game_type_id') in [game_type.id for game_type in GameType.objects.filter(gametypename__is_actual=True)] and data.get('game_type_name_id') is None:
        return 400, {"message": "If game type has names, game type name must be provided."}
    with transaction.atomic(using='hockey'):
        if data_status is not None and game.status != data_status and data_status == 3:
            # Game has finished, add its data to statistics.
            GameEventsAnalysisQueue.objects.create(game=game, action=1)
        elif data_status is not None and game.status == 3 and data_status != 3:
            # Game finish has been undone, remove its data from statistics.
            GameEventsAnalysisQueue.objects.create(game=game, action=2)
        elif data_status is not None and game.status == data_status and data_status == 3:
            # Game has been updated after finishing, re-apply its data to statistics.
            GameEventsAnalysisQueue.objects.create(game=game, action=3)
            GameEventsAnalysisQueue.objects.create(game=game, action=1)

        if (data.get('home_team_goalie_id') is not None or data.get('away_team_goalie_id') is not None) and game.status > 1:
            transaction.set_rollback(True, using='hockey')
            return 400, {"message": f"Goalies can only be set here before the game starts. After the game starts, goalies can only be added by the '{EventName.GOALIE_CHANGE}' event."}

        if data.get('home_team_goalie_id') is not None:
            GameGoalie.objects.filter(game=game, goalie__team=game.home_team).delete()
            GameGoalie.objects.create(game=game, goalie_id=data.get('home_team_goalie_id'), start_period_id=1, start_time=datetime.time(0, 0, 0))
        if data.get('away_team_goalie_id') is not None:
            GameGoalie.objects.filter(game=game, goalie__team=game.away_team).delete()
            GameGoalie.objects.create(game=game, goalie_id=data.get('away_team_goalie_id'), start_period_id=1, start_time=datetime.time(0, 0, 0))

        if data.get('date') is not None and game.date != data.get('date'):
            game.season = get_current_season(data.get('date'))

        for attr, value in {k: v for k, v in data.items() if k not in ["home_goalies", "away_goalies", "home_players", "away_players"]}.items():
            setattr(game, attr, value)
        if data.get('home_goalies') is not None:
            game.home_goalies.set(data['home_goalies'])
        if data.get('away_goalies') is not None:
            game.away_goalies.set(data['away_goalies'])
        if data.get('home_players') is not None:
            game.home_players.set(data['home_players'])
        if data.get('away_players') is not None:
            game.away_players.set(data['away_players'])
        game.save()
    return 204, None

@router.delete("/game/{game_id}", response={204: None})
def delete_game(request: HttpRequest, game_id: int):
    game = get_object_or_404(Game, id=game_id)
    with transaction.atomic(using='hockey'):
        GameEventsAnalysisQueue.objects.create(game=game, action=3)
        game.is_deprecated = True
        game.save()
    return 204, None

@router.get("/game/defensive-zone-exit/{defensive_zone_exit_id}", response=DefensiveZoneExitOut)
def get_game_defensive_zone_exit(request: HttpRequest, defensive_zone_exit_id: int):
    defensive_zone_exit = get_object_or_404(DefensiveZoneExit, id=defensive_zone_exit_id)
    return defensive_zone_exit

@router.patch("/game/defensive-zone-exit/{defensive_zone_exit_id}", response={204: None})
def update_game_defensive_zone_exit(request: HttpRequest, defensive_zone_exit_id: int, data: PatchDict[DefensiveZoneExitIn]):
    defensive_zone_exit = get_object_or_404(DefensiveZoneExit, id=defensive_zone_exit_id)
    for attr, value in data.items():
        setattr(defensive_zone_exit, attr, value)
    defensive_zone_exit.save()
    return 204, None

@router.get("/game/offensive-zone-entry/{offensive_zone_entry_id}", response=OffensiveZoneEntryOut)
def get_game_offensive_zone_entry(request: HttpRequest, offensive_zone_entry_id: int):
    offensive_zone_entry = get_object_or_404(OffensiveZoneEntry, id=offensive_zone_entry_id)
    return offensive_zone_entry

@router.patch("/game/offensive-zone-entry/{offensive_zone_entry_id}", response={204: None})
def update_game_offensive_zone_entry(request: HttpRequest, offensive_zone_entry_id: int, data: PatchDict[OffensiveZoneEntryIn]):
    offensive_zone_entry = get_object_or_404(OffensiveZoneEntry, id=offensive_zone_entry_id)
    for attr, value in data.items():
        setattr(offensive_zone_entry, attr, value)
    offensive_zone_entry.save()
    return 204, None

@router.get("/game/shots/{shots_id}", response=ShotsOut)
def get_game_shots(request: HttpRequest, shots_id: int):
    shots = get_object_or_404(Shots, id=shots_id)
    return shots

@router.get("/game/turnovers/{turnovers_id}", response=TurnoversOut)
def get_game_turnovers(request: HttpRequest, turnovers_id: int):
    turnovers = get_object_or_404(Turnovers, id=turnovers_id)
    return turnovers

@router.get("/game/{game_id}/live-data", response=GameLiveDataOut)
def get_game_live_data(request: HttpRequest, game_id: int):
    game = get_object_or_404(Game, id=game_id)
    home_goalie_id, away_goalie_id = get_game_current_goalies(game)
    home_faceoff_win = (round((game.home_faceoffs_won_count / game.faceoffs_count) * 100) if game.faceoffs_count > 0 else 0)
    away_faceoff_win = ((100 - home_faceoff_win) if game.faceoffs_count > 0 else 0)
    return GameLiveDataOut(game_period_id=game.game_period_id,
                           home_goalie_id=home_goalie_id,
                           away_goalie_id=away_goalie_id,
                           home_goals=game.home_goals, away_goals=game.away_goals,
                           home_faceoff_win=home_faceoff_win,
                           away_faceoff_win=away_faceoff_win,
                           home_defensive_zone_exit=game.home_defensive_zone_exit,
                           away_defensive_zone_exit=game.away_defensive_zone_exit,
                           home_offensive_zone_entry=game.home_offensive_zone_entry,
                           away_offensive_zone_entry=game.away_offensive_zone_entry,
                           home_shots=game.home_shots,
                           away_shots=game.away_shots,
                           home_turnovers=game.home_turnovers,
                           away_turnovers=game.away_turnovers,
                           events=game.gameevents_set.exclude(is_deprecated=True).order_by("period", "-time").all())

@router.get('/game/{game_id}/events', response=list[GameEventOut])
def get_game_events(request: HttpRequest, game_id: int):
    game_events = GameEvents.objects.filter(game_id=game_id).exclude(is_deprecated=True).order_by("period", "-time").all()
    return game_events

# endregion

# region Game players

@router.get('/game-player/game/{game_id}', response=GamePlayersOut)
def get_game_players(request: HttpRequest, game_id: int):
    game = get_object_or_404(Game, id=game_id)
    home_goalies = []
    home_players = []
    away_goalies = []
    away_players = []
    for game_goalie in game.gamegoalie_set.all():
        home_away = (home_goalies if game_goalie.goalie.team_id == game.home_team_id else away_goalies)
        home_away.append(form_game_goalie_out(game_goalie))
    for game_player in game.gameplayer_set.all():
        home_away = (home_players if game_player.player.team_id == game.home_team_id else away_players)
        home_away.append(form_game_player_out(game_player))
    return GamePlayersOut(home_goalies=home_goalies, home_players=home_players, away_goalies=away_goalies, away_players=away_players)

@router.get('/game-player/goalie/{goalie_id}', response=list[GameGoalieOut])
def get_goalie_games(request: HttpRequest, goalie_id: int, limit: int = 5):
    goalie_games = GameGoalie.objects.filter(goalie_id=goalie_id).order_by('-game__date')[:limit]
    games: list[GameGoalieOut] = []
    for game_goalie in goalie_games:
        games.append(form_game_goalie_out(game_goalie))
    return games

@router.get('/game-player/player/{player_id}', response=list[GamePlayerOut])
def get_player_games(request: HttpRequest, player_id: int, limit: int = 5):
    player_games = GamePlayer.objects.filter(player_id=player_id).order_by('-game__date')[:limit]
    games: list[GamePlayerOut] = []
    for game_player in player_games:
        games.append(form_game_player_out(game_player))
    return games

@router.post('/game-player/list', response={204: None})
def set_game_players(request: HttpRequest, game_id: int, data: GamePlayersIn):
    # TODO: asked about necessity of this function. If necessary, write a logic to remove only disappeared players and add new ones.
    with transaction.atomic(using='hockey'):
        GamePlayer.objects.filter(game_id=game_id).delete()
        for player_id in data.player_ids:
            GamePlayer.objects.create(game_id=game_id, player_id=player_id)
    return 204, None

# endregion

# region Game events

@router.get('/game-event-name/list', response=list[ObjectIdName])
def get_game_event_names(request: HttpRequest):
    game_event_names = GameEventName.objects.all()
    return game_event_names

@router.get('/shot-type/list', response=list[ObjectIdName])
def get_shot_types(request: HttpRequest):
    shot_types = ShotType.objects.order_by('name').all()
    return shot_types

@router.get('/game-event/{game_event_id}', response=GameEventOut)
def get_game_event(request: HttpRequest, game_event_id: int):
    game_event = get_object_or_404(GameEvents.objects, id=game_event_id)
    return game_event

@router.post('/game-event', response={200: ObjectId, 400: Message})
def add_game_event(request: HttpRequest, data: GameEventIn):
    try:
        with transaction.atomic(using='hockey'):

            event_name = GameEventName.objects.filter(id=data.event_name_id).first()

            if event_name.name == EventName.GOALIE_CHANGE and data.goalie_id is None:
                data.goalie_id = get_no_goalie().pk

            if data.goalie_id is None and data.player_id is None and data.player_2_id is None:
                raise ValueError("Please specify goalie ID and/or player ID(s).")

            data_new = data.dict()

            game_event = GameEvents.objects.create(**data_new)

            if event_name is None:
                raise ValueError(f"event_name_id {data.event_name_id} not found.")

            if game_event.shot_type is not None and event_name.name != EventName.SHOT:
                raise ValueError(f"Shot type is only allowed for '{EventName.SHOT}' events.")

            game: Game = game_event.game

            if event_name.name == EventName.SHOT:
                error = update_game_shots_from_event(game, data=data, is_deleted=False)
                if error is not None:
                    raise ValueError(error)
            elif event_name.name == EventName.TURNOVER:
                error = update_game_turnovers_from_event(game, data=data, is_deleted=False)
                if error is not None:
                    raise ValueError(error)
            elif event_name.name == EventName.FACEOFF:
                error = update_game_faceoffs_from_event(game, data=data, is_deleted=False)
                if error is not None:
                    raise ValueError(error)

    except ValueError as e:
        return 400, {"message": str(e)}
    except IntegrityError as e:
        return resp.entry_already_exists("Game event", str(e))
    return {"id": game_event.id}

@router.patch("/game-event/{game_event_id}", response={204: None, 400: Message})
def update_game_event(request: HttpRequest, game_event_id: int, data: PatchDict[GameEventIn]):

    game_event = get_object_or_404(GameEvents, id=game_event_id)
    game: Game = game_event.game

    try:
        with transaction.atomic(using='hockey'):

            # Create the copy with deprecation.

            # game_event.pk = None
            # game_event._state.adding = True
            # game_event.is_deprecated = True
            # game_event.save()

            # Undo old shot/turnover data.
            if game_event.event_name.name == EventName.SHOT:
                error = update_game_shots_from_event(game, event=game_event, is_deleted=True)
                if error is not None:
                    raise ValueError(error)
            elif game_event.event_name.name == EventName.TURNOVER:
                error = update_game_turnovers_from_event(game, event=game_event, is_deleted=True)
                if error is not None:
                    raise ValueError(error)
            elif game_event.event_name.name == EventName.FACEOFF:
                error = update_game_faceoffs_from_event(game, event=game_event, is_deleted=True)
                if error is not None:
                    raise ValueError(error)

            game_event.save()

            # GameEventsAnalysisQueue.objects.create(game_event=game_event, action=3)

            # Update the original event.

            game_event = GameEvents.objects.get(id=game_event_id)

            for attr, value in data.items():
                setattr(game_event, attr, value)
            if game_event.goalie is None and game_event.player is None and game_event.player_2 is None:
                raise ValueError("Please specify goalie ID or player IDs.")
            if game_event.shot_type is not None and game_event.event_name.name != EventName.SHOT:
                game_event.shot_type = None
            game_event.save()

            # Apply new shot/turnover data.
            if game_event.event_name.name == EventName.SHOT:
                error = update_game_shots_from_event(game, event=game_event, is_deleted=False)
                if error is not None:
                    raise ValueError(error)
            elif game_event.event_name.name == EventName.TURNOVER:
                error = update_game_turnovers_from_event(game, event=game_event, is_deleted=False)
                if error is not None:
                    raise ValueError(error)
            elif game_event.event_name.name == EventName.FACEOFF:
                error = update_game_faceoffs_from_event(game, event=game_event, is_deleted=False)
                if error is not None:
                    raise ValueError(error)

            # GameEventsAnalysisQueue.objects.create(game_event=game_event, action=1)

    except ValueError as e:
        return 400, {"message": str(e)}

    return 204, None

@router.delete("/game-event/{game_event_id}", response={204: None})
def delete_game_event(request: HttpRequest, game_event_id: int):
    game_event = get_object_or_404(GameEvents, id=game_event_id)
    try:
        with transaction.atomic(using='hockey'):

            if game_event.event_name.name == EventName.SHOT:
                error = update_game_shots_from_event(game_event.game, event=game_event, is_deleted=True)
                if error is not None:
                    raise ValueError(error)
            elif game_event.event_name.name == EventName.TURNOVER:
                error = update_game_turnovers_from_event(game_event.game, event=game_event, is_deleted=True)
                if error is not None:
                    raise ValueError(error)
            elif game_event.event_name.name == EventName.FACEOFF:
                error = update_game_faceoffs_from_event(game_event.game, event=game_event, is_deleted=True)
                if error is not None:
                    raise ValueError(error)

            game_event.delete()

            # GameEventsAnalysisQueue.objects.create(game_event=game_event, action=3)

    except ValueError as e:
        return 400, {"message": str(e)}

    return 204, None

# endregion

# region Highlight reels

@router.get('/highlight-reels', response=list[HighlightReelListOut])
def get_highlight_reels(request: HttpRequest):
    highlight_reels = HighlightReel.objects.all() # TODO: filter by current user
    highlight_reels_users = list(set([reel.user_email for reel in highlight_reels]))
    users = User.objects.filter(email__in=highlight_reels_users)
    users_dict = {user.email: f'{user.first_name} {user.last_name}' for user in users}
    highlight_reels_out = []
    for reel in highlight_reels:
        highlight_reels_out.append(HighlightReelListOut(id=reel.id, name=reel.name, description=reel.description,
                                                        date=reel.date, created_by=users_dict[reel.user_email]))
    return highlight_reels_out

@router.post('/highlight-reels', response={200: ObjectId, 400: Message},
             description=("Create a new highlight reel and add highlights to it.\n\n"
             "Each highlight should have either a game event ID or a custom event fields filled in."))
def add_highlight_reel(request: HttpRequest, data: HighlightReelFullIn):
    try:
        with transaction.atomic(using='hockey'):
            highlight_reel = HighlightReel.objects.create(name=data.name, description=data.description,
                user_email=request.user.email)
            for highlight in data.highlights:
                create_highlight(highlight, highlight_reel, request.user.email)
    except ValueError as e:
        return 400, {"message": str(e)}
    return {"id": highlight_reel.id}

@router.patch('/highlight-reels/{highlight_reel_id}', response={204: None}, description="Update a highlight reel.")
def update_highlight_reel(request: HttpRequest, highlight_reel_id: int, data: PatchDict[HighlightReelIn]):
    highlight_reel = get_object_or_404(HighlightReel, id=highlight_reel_id)
    for attr, value in data.items():
        setattr(highlight_reel, attr, value)
    highlight_reel.save()
    return 204, None

@router.delete('/highlight-reels/{highlight_reel_id}', response={204: None})
def delete_highlight_reel(request: HttpRequest, highlight_reel_id: int):
    highlight_reel = get_object_or_404(HighlightReel, id=highlight_reel_id)
    highlights = highlight_reel.highlights.all()
    try:
        with transaction.atomic(using='hockey'):
            for highlight in highlights:
                if highlight.custom_event is not None:
                    highlight.custom_event.delete()
                highlight.delete()
            highlight_reel.delete()
    except ValueError as e:
        return 400, {"message": str(e)}
    return 204, None

@router.get('/highlight-reels/{highlight_reel_id}/highlights', response=list[HighlightOut])
def get_highlight_reel_highlights(request: HttpRequest, highlight_reel_id: int):
    highlight_reel = get_object_or_404(HighlightReel, id=highlight_reel_id)
    return highlight_reel.highlights.order_by('order').all()

@router.post('/highlight-reels/{highlight_reel_id}/highlights', response={200: ObjectId, 400: Message})
def add_highlight(request: HttpRequest, highlight_reel_id: int, data: HighlightIn):
    highlight_reel = get_object_or_404(HighlightReel, id=highlight_reel_id)
    try:
        with transaction.atomic(using='hockey'):
            highlight = create_highlight(data, highlight_reel, request.user.email)
    except ValueError as e:
        return 400, {"message": str(e)}
    return {"id": highlight.id}

@router.delete('/highlights/{highlight_id}', response={204: None, 400: Message})
def delete_highlight(request: HttpRequest, highlight_id: int):
    highlight = get_object_or_404(Highlight, id=highlight_id)
    try:
        with transaction.atomic(using='hockey'):
            if highlight.custom_event is not None:
                highlight.custom_event.delete()
            highlight.delete()
    except ValueError as e:
        return 400, {"message": str(e)}
    return 204, None

# endregion

# region FAKES (DISABLED)

# @router.get("/fake/teams")
# def add_fake_teams(request):
#     fake = Faker('en_US')
#     fake.add_provider(faker.providers.address)
#     fake.add_provider(AnimalsProvider)

#     team_levels = [team_lvl.id for team_lvl in TeamLevel.objects.all()]
#     team_divisions = [division.id for division in Division.objects.all()]

#     birth_year_from = datetime.date(1970, 1, 1)
#     birth_year_to = datetime.date(2015, 1, 1)

#     # Team

#     Team.objects.all().delete()

#     for _ in range(10):
#         fake_city = fake.city()

#         team = Team(
#             name=f"{fake_city} {fake.animal_name()}s",
#             age_group=f"{fake.random_int(5, 22)}U",
#             level_id=fake.random_element(team_levels),
#             division_id=fake.random_element(team_divisions),
#             city=fake_city
#         )

#         if settings.USE_LOCAL_STORAGE:
#             with open(os.path.join(settings.MEDIA_ROOT,
#                                 f"fakes/team{fake.random_int(1, 2)}.png"), "rb") as img_file:
#                 img_to_store = FileSaver(img_file)
#                 team.logo.save(f"{team.name}.png", img_to_store)
#                 team.save()
#         else:
#             with default_storage.open(f"fakes/team{fake.random_int(1, 2)}.png", "rb") as img_file:
#                 # img_to_store = FileSaver(img_file)
#                 team.logo.save(f"{team.name}.png", img_file)
#                 team.save()

#     teams = [team.id for team in Team.objects.all()]
#     positions = [pos.id for pos in PlayerPosition.objects.exclude(name__iexact="goalie")]

#     # Goalie

#     Goalie.objects.all().delete()

#     goalie_position = (PlayerPosition.objects.filter(name__iexact="goalie"))[0].id

#     for _ in range(20):
#         goalie = Goalie.objects.create(
#             team_id=fake.random_element(teams),
#             position_id=goalie_position,
#             height=fake.random_int(63, 82),
#             weight=fake.random_int(154, 242),
#             shoots=fake.random_element(['R', 'L']),
#             jersey_number=fake.random_int(1, 50),
#             first_name=fake.first_name_male(),
#             last_name=fake.last_name_male(),
#             birth_year=fake.date_between_dates(birth_year_from, birth_year_to),
#             wins=fake.random_int(0, 100),
#             losses=fake.random_int(0, 100)
#         )

#     # Player

#     Player.objects.all().delete()

#     for _ in range(100):
#         player = Player.objects.create(
#             team_id=fake.random_element(teams),
#             position_id=fake.random_element(positions),
#             height=fake.random_int(63, 82),
#             weight=fake.random_int(154, 242),
#             shoots=fake.random_element(['R', 'L']),
#             number=fake.random_int(1, 50),
#             first_name=fake.first_name_male(),
#             last_name=fake.last_name_male(),
#             birth_year=fake.date_between_dates(birth_year_from, birth_year_to),
#             penalties_drawn=fake.random_int(0, 100),
#             penalties_taken=fake.random_int(0, 100)
#         )

#     # Season, TeamSeason

#     Season.objects.all().delete()
#     TeamSeason.objects.all().delete()

#     for year in [2020, 2021, 2022, 2023, 2024, 2025]:
#         season = Season.objects.create(name=f"{year} / {year + 1}")
#         for team_id in teams:
#             games_played = fake.random_int(14, 15)
#             ties = fake.random_int(0, int((games_played / 2)))
#             wins = fake.random_int(0, ties)
#             losses = games_played - wins
#             TeamSeason.objects.create(
#                 team_id=team_id,
#                 season=season,
#                 games_played=games_played,
#                 goals_for=fake.random_int(0, 40),
#                 goals_against=fake.random_int(0, 40),
#                 wins=wins,
#                 losses=losses,
#                 ties=ties
#             )

    # 

# endregion
