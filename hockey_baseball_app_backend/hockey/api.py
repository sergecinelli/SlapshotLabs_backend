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
from django.core.exceptions import ValidationError
from faker import Faker
import faker.providers
from faker_animals import AnimalsProvider

from hockey.utils.constants import (GOALIE_POSITION_NAME, NO_GOALIE_FIRST_NAME, NO_GOALIE_LAST_NAME, ApiDocTags,
                                    EventName, GameEventSystemStatus, GameStatus, GoalType, get_constant_class_int_choices,
                                    ApiDocTags)
from hockey.utils.event_analysis_serializer import serialize_game, serialize_game_event
from users.utils.roles import is_user_admin, is_user_coach

from .schemas import (ArenaOut, ArenaRinkOut, ArenaRinkExtendedOut, DefensiveZoneExitIn, DefensiveZoneExitOut, GameBannerOut, GameDashboardOut,
                      GameEventIn, GameEventOut, GameExtendedOut, GameGoalieOut,
                      GameIn, GameLiveDataOut, GameOut, GamePeriodOut, GamePlayerOut, GamePlayersIn, GamePlayersOut,
                      GameSprayChartFilters, GameTypeOut, GameTypeRecordOut, GoalieBaseOut, GoalieSeasonOut,
                      GoalieSeasonsGet, GoalieSprayChartFilters, GoalieTeamSeasonOut, HighlightIn, HighlightOut, HighlightReelIn, HighlightReelUpdateIn,
                      HighlightReelListOut, HighlightReelOut, ObjectIdName, Message, ObjectId, OffensiveZoneEntryIn,
                      OffensiveZoneEntryOut, PlayerBaseOut, PlayerPositionOut, GoalieIn,
                      GoalieOut, PlayerIn, PlayerOut, PlayerSeasonOut, PlayerSeasonsGet, PlayerSprayChartFilters, PlayerTeamSeasonOut, SeasonIn,
                      SeasonOut, ShotsIn, ShotsOut, SprayChartFilters,
                      TeamIn, TeamOut, TeamSeasonOut, TurnoversIn, TurnoversOut, VideoLibraryIn, VideoLibraryOut)
from .models import (Arena, ArenaRink, CustomEvents, DefensiveZoneExit, Division, Game, GameEventName, GameEvents, GameEventsAnalysisQueue,
                     GameGoalie, GamePeriod, GamePlayer, GameType, Goalie, GoalieSeason, GoalieTeamSeason, Highlight, HighlightReel, OffensiveZoneEntry, Player,
                     PlayerPosition, PlayerSeason, PlayerTeamSeason, PlayerTransaction, Season, ShotType, Shots, Team, TeamLevel, TeamSeason, GameTypeName,
                     Turnovers, VideoLibrary)
from .utils import api_response_templates as resp
from .utils.db_utils import (create_highlight, form_game_goalie_out, form_game_dashboard_game_out, form_game_player_out, form_goalie_out,
                             form_player_out, get_current_season,
                             get_game_current_goalies, get_no_goalie, is_no_goalie_dict, is_no_goalie_object, update_game_faceoffs_from_event,
                             update_game_shots_from_event, update_game_turnovers_from_event)

router = Router()

User = get_user_model()

# region Goalie and player

@router.get('/player-position/list', response=list[PlayerPositionOut], tags=[ApiDocTags.PLAYER])
def get_player_positions(request: HttpRequest):
    positions = PlayerPosition.objects.exclude(name=GOALIE_POSITION_NAME).all()
    return positions

@router.get('/goalie/list', response=list[GoalieOut], tags=[ApiDocTags.PLAYER])
def get_goalies(request: HttpRequest, team_id: int | None = None):
    current_season = get_current_season()
    goalies_out: list[GoalieOut] = []
    goalies = Goalie.objects.filter(player__is_archived=False)
    if team_id is not None:
        goalies = goalies.filter(player__team_id=team_id)
    for goalie in goalies:
        goalies_out.append(form_goalie_out(goalie, current_season))
    return goalies_out

@router.post("/goalie/seasons", response=list[GoalieSeasonOut], tags=[ApiDocTags.PLAYER, ApiDocTags.STATS])
def get_goalie_seasons(request: HttpRequest, data: GoalieSeasonsGet):
    return GoalieSeason.objects.prefetch_related('season').filter(goalie_id=data.goalie_id, season_id__in=data.season_ids).\
        order_by('-season__start_date').all()

@router.get('/goalie/{goalie_id}', response=GoalieOut, tags=[ApiDocTags.PLAYER])
def get_goalie(request: HttpRequest, goalie_id: int):
    goalie = get_object_or_404(Goalie, pk=goalie_id)
    current_season = get_current_season()
    return form_goalie_out(goalie, current_season)

@router.get('/goalie/{goalie_id}/photo', response=bytes, tags=[ApiDocTags.PLAYER])
def get_goalie_photo(request: HttpRequest, goalie_id: int):
    goalie = get_object_or_404(Player, id=goalie_id, position__name=GOALIE_POSITION_NAME)
    return FileResponse(goalie.photo.open())

@router.post('/goalie', response={200: ObjectId, 400: Message, 403: Message, 503: Message}, tags=[ApiDocTags.PLAYER])
def add_goalie(request: HttpRequest, data: GoalieIn, photo: File[UploadedFile] = None):
    if not is_user_coach(request.user, data.team_id):
        return 403, {"message": "You are not authorized to add a goalie."}
    if is_no_goalie_object(data):
        return 400, {"message": "This goalie is used in case of no goalie in net, so it cannot be added."}
    try:
        with transaction.atomic(using='hockey'):
            goalie = Player(position=PlayerPosition.objects.get(name=GOALIE_POSITION_NAME), **data.dict())
            goalie.photo = photo
            goalie.save()
            Goalie.objects.create(player=goalie)
    except IntegrityError as e:
        return resp.entry_already_exists("Goalie", str(e))
    return {"id": goalie.id}

@router.patch("/goalie/{goalie_id}", response={204: None, 400: Message, 403: Message}, tags=[ApiDocTags.PLAYER])
def update_goalie(request: HttpRequest, goalie_id: int, data: PatchDict[GoalieIn], photo: File[UploadedFile] = None):
    goalie = get_object_or_404(Player, id=goalie_id, position__name=GOALIE_POSITION_NAME)
    if not is_user_coach(request.user, goalie.team_id):
        return 403, {"message": "You are not authorized to update this goalie."}
    if is_no_goalie_object(goalie):
        return 403, {"message": "This goalie is used in case of no goalie in net, so it cannot be updated."}
    old_team_id = goalie.team_id
    for attr, value in data.items():
        setattr(goalie, attr, value)
    if is_no_goalie_object(goalie):
        return 400, {"message": "This name is used in case of no goalie in net, so it cannot be set."}
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

@router.delete("/goalie/{goalie_id}", response={200: Message, 403: Message}, tags=[ApiDocTags.PLAYER])
def delete_goalie(request: HttpRequest, goalie_id: int):
    goalie = get_object_or_404(Player, id=goalie_id, position__name=GOALIE_POSITION_NAME)
    if not is_user_coach(request.user, goalie.team_id):
        return 403, {"message": "You are not authorized to delete this goalie."}
    if is_no_goalie_object(goalie):
        return 403, {"message": "This goalie is used in case of no goalie in net, so they cannot be deleted."}
    try:
        goalie.delete()
    except RestrictedError as e:
        goalie.is_archived = True
        goalie.save()
        return 200, {"message": "Archived."}
    return 200, {"message": "Deleted."}

@router.post("/goalie/{goalie_id}/spray-chart", response={200: list[GameEventOut], 400: Message}, tags=[ApiDocTags.PLAYER, ApiDocTags.SPRAY_CHART])
def get_goalie_spray_chart(request: HttpRequest, goalie_id: int, filters: GoalieSprayChartFilters):
    if (filters.season_id is not None) and (filters.game_id is not None):
        return 400, {"message": "season_id and game_id cannot be provided at the same time."}
    
    events = GameEvents.objects.filter(goalie_id=goalie_id)

    if filters.season_id is not None:
        events = events.prefetch_related('game').filter(game__season_id=filters.season_id)
    if filters.game_id is not None:
        events = events.filter(game_id=filters.game_id)

    if filters.shot_type_id is not None:
        events = events.prefetch_related('event_name').filter(event_name__name=EventName.SHOT, shot_type_id=filters.shot_type_id)

    return events.all()

@router.get("/goalie/{goalie_id}/team-seasons", response=list[GoalieTeamSeasonOut], tags=[ApiDocTags.PLAYER, ApiDocTags.STATS])
def get_goalie_team_seasons(request: HttpRequest, goalie_id: int, limit: int = 3):
    return GoalieTeamSeason.objects.prefetch_related('season').filter(goalie_id=goalie_id)\
        .order_by('-season__start_date')[:limit]

@router.get('/player/list', response=list[PlayerOut], tags=[ApiDocTags.PLAYER])
def get_players(request: HttpRequest, team_id: int | None = None):
    current_season = get_current_season()
    players_out: list[PlayerOut] = []
    players = Player.objects.exclude(position__name=GOALIE_POSITION_NAME).filter(is_archived=False)
    if team_id is not None:
        players = players.filter(team_id=team_id)
    for player in players:
        players_out.append(form_player_out(player, current_season))
    return players_out

@router.post("/player/seasons", response=list[PlayerSeasonOut], tags=[ApiDocTags.PLAYER, ApiDocTags.STATS])
def get_player_seasons(request: HttpRequest, data: PlayerSeasonsGet):
    return PlayerSeason.objects.filter(player_id=data.player_id, season_id__in=data.season_ids)

@router.get('/player/{player_id}', response=PlayerOut, tags=[ApiDocTags.PLAYER])
def get_player(request: HttpRequest, player_id: int):
    player = get_object_or_404(Player.objects.exclude(position__name=GOALIE_POSITION_NAME), id=player_id)
    current_season = get_current_season()
    return form_player_out(player, current_season)

@router.get('/player/{player_id}/photo', response=bytes, tags=[ApiDocTags.PLAYER])
def get_player_photo(request: HttpRequest, player_id: int):
    player = get_object_or_404(Player.objects.exclude(position__name=GOALIE_POSITION_NAME), id=player_id)
    return FileResponse(player.photo.open())

@router.post('/player', response={200: ObjectId, 400: Message, 403: Message}, tags=[ApiDocTags.PLAYER])
def add_player(request: HttpRequest, data: PlayerIn, photo: File[UploadedFile] = None):
    if not is_user_coach(request.user, data.team_id):
        return 403, {"message": "You are not authorized to add a player."}
    try:
        if data.position_id == PlayerPosition.objects.get(name=GOALIE_POSITION_NAME).id or is_no_goalie_object(data):
            return 400, {"message": "Goalies are not added through this endpoint."}
        player = Player(**data.dict())
        player.photo = photo
        player.save()
    except IntegrityError as e:
        return resp.entry_already_exists("Player", str(e))
    return {"id": player.id}

@router.patch("/player/{player_id}", response={204: None, 400: Message, 403: Message}, tags=[ApiDocTags.PLAYER])
def update_player(request: HttpRequest, player_id: int, data: PatchDict[PlayerIn], photo: File[UploadedFile] = None):
    if data.get('position_id') == PlayerPosition.objects.get(name=GOALIE_POSITION_NAME).id:
        return 400, {"message": "Goalies are not updated through this endpoint."}
    player = get_object_or_404(Player.objects.exclude(position__name=GOALIE_POSITION_NAME), id=player_id)
    if not is_user_coach(request.user, player.team_id):
        return 403, {"message": "You are not authorized to update this player."}
    old_team_id = player.team_id
    for attr, value in data.items():
        setattr(player, attr, value)
    if is_no_goalie_object(player):
        return 400, {"message": "Goalies are not updated through this endpoint."}
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

@router.delete("/player/{player_id}", response={200: Message, 403: Message}, tags=[ApiDocTags.PLAYER])
def delete_player(request: HttpRequest, player_id: int):
    player = get_object_or_404(Player.objects.exclude(position__name=GOALIE_POSITION_NAME), id=player_id)
    if not is_user_coach(request.user, player.team_id):
        return 403, {"message": "You are not authorized to delete this player."}
    try:
        player.delete()
    except RestrictedError as e:
        player.is_archived = True
        player.save()
        return 200, {"message": "Archived."}
    return 200, {"message": "Deleted."}

@router.post("/player/{player_id}/spray-chart", response={200: list[GameEventOut], 400: Message}, tags=[ApiDocTags.PLAYER, ApiDocTags.SPRAY_CHART])
def get_player_spray_chart(request: HttpRequest, player_id: int, filters: PlayerSprayChartFilters):
    if (filters.season_id is not None) and (filters.game_id is not None):
        return 400, {"message": "season_id and game_id cannot be provided at the same time."}

    events = GameEvents.objects.filter(player_id=player_id)

    if filters.season_id is not None:
        events = events.prefetch_related('game').filter(game__season_id=filters.season_id)
    if filters.game_id is not None:
        events = events.filter(game_id=filters.game_id)

    if filters.event_name is not None:
        events = events.prefetch_related('event_name').filter(event_name__name=filters.event_name)
    if filters.shot_type_id is not None:
        events = events.prefetch_related('shot_type').filter(shot_type_id=filters.shot_type_id)
    if filters.is_scoring_chance is not None:
        events = events.filter(is_scoring_chance=filters.is_scoring_chance)
    if filters.goal_type is not None:
        events = events.filter(goal_type=filters.goal_type)

    return events.all()

@router.get("/player/{player_id}/team-seasons", response=list[PlayerTeamSeasonOut], tags=[ApiDocTags.PLAYER, ApiDocTags.STATS])
def get_player_team_seasons(request: HttpRequest, player_id: int, limit: int = 3):
    return PlayerTeamSeason.objects.prefetch_related('season').filter(player_id=player_id)\
        .order_by('-season__start_date')[:limit]

# endregion

# region Team, season

@router.get('/division/list', response=list[ObjectIdName], tags=[ApiDocTags.TEAM])
def get_divisions(request: HttpRequest):
    divisions = Division.objects.all()
    return divisions

@router.get('/team-level/list', response=list[ObjectIdName], tags=[ApiDocTags.TEAM])
def get_team_levels(request: HttpRequest):
    levels = TeamLevel.objects.all()
    return levels

@router.get('/team/list', response=list[TeamOut], tags=[ApiDocTags.TEAM])
def get_teams(request: HttpRequest):
    teams = Team.objects.filter(is_archived=False)
    return teams

@router.get('/team/{team_id}', response=TeamOut, tags=[ApiDocTags.TEAM])
def get_team(request: HttpRequest, team_id: int):
    team = get_object_or_404(Team, id=team_id)
    return team

@router.get('/team/{team_id}/logo', response=bytes, tags=[ApiDocTags.TEAM])
def get_team_logo(request: HttpRequest, team_id: int):
    team = get_object_or_404(Team, id=team_id)
    return FileResponse(team.logo.open())

@router.post('/team', response={200: ObjectId, 400: Message, 403: Message}, tags=[ApiDocTags.TEAM])
def add_team(request: HttpRequest, data: TeamIn, logo: File[UploadedFile] = None):
    if not is_user_admin(request.user):
        return 403, {"message": "You are not authorized to add a team."}
    try:
        with transaction.atomic(using='hockey'):
            team = Team(**data.dict())
            team.logo = logo
            team.save()
            get_no_goalie(team.id) # Creates the no goalie for the team if it doesn't exist.
    except IntegrityError as e:
        return resp.entry_already_exists("Team")
    return {"id": team.id}

@router.patch("/team/{team_id}", response={204: None, 400: Message, 403: Message}, tags=[ApiDocTags.TEAM])
def update_team(request: HttpRequest, team_id: int, data: PatchDict[TeamIn], logo: File[UploadedFile] = None):
    if not is_user_coach(request.user, team_id):
        return 403, {"message": "You are not authorized to update this team."}
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

@router.delete("/team/{team_id}", response={200: Message, 403: Message}, tags=[ApiDocTags.TEAM])
def delete_team(request: HttpRequest, team_id: int):
    if not is_user_admin(request.user):
        return 403, {"message": "You are not authorized to delete this team."}
    team = get_object_or_404(Team, id=team_id)
    try:
        with transaction.atomic(using='hockey'):
            get_no_goalie(team.id).player.delete() # Deletes the no goalie for the team.
            team.delete()
    except RestrictedError as e:
        team.is_archived = True
        team.save()
        return 200, {"message": "Archived."}
    return 200, {"message": "Deleted."}

@router.get('/season/list', response=list[SeasonOut], tags=[ApiDocTags.TEAM])
def get_seasons(request: HttpRequest):
    seasons = Season.objects.all()
    return seasons

@router.get('/season/{season_id}', response=SeasonOut, tags=[ApiDocTags.TEAM])
def get_season(request: HttpRequest, season_id: int):
    season = get_object_or_404(Season, id=season_id)
    return season

@router.post('/season', response={200: ObjectId, 400: Message, 403: Message}, tags=[ApiDocTags.TEAM])
def add_season(request: HttpRequest, data: SeasonIn):
    if not is_user_admin(request.user):
        return 403, {"message": "You are not authorized to add a season."}
    try:
        if not re.match(r'^\d{4} / \d{4}$', data.name):
            return 400, {"message": "Season name must be in the format 'YYYY / YYYY'."}
        season = Season.objects.create(**data.dict())
    except IntegrityError as e:
        return resp.entry_already_exists("Season", str(e))
    return {"id": season.id}

@router.patch("/season/{season_id}", response={204: None, 403: Message}, tags=[ApiDocTags.TEAM])
def update_season(request: HttpRequest, season_id: int, data: PatchDict[SeasonIn]):
    if not is_user_admin(request.user):
        return 403, {"message": "You are not authorized to update this season."}
    if not re.match(r'^\d{4} / \d{4}$', data.name):
        return 400, {"message": "Season name must be in the format 'YYYY / YYYY'."}
    season = get_object_or_404(Season, id=season_id)
    for attr, value in data.items():
        setattr(season, attr, value)
    season.save()
    return 204, None

@router.delete("/season/{season_id}", response={204: None, 403: Message}, tags=[ApiDocTags.TEAM])
def delete_season(request: HttpRequest, season_id: int):
    if not is_user_admin(request.user):
        return 403, {"message": "You are not authorized to delete this season."}
    season = get_object_or_404(Season, id=season_id)
    season.delete()
    return 204, None

@router.get('/team-season/list', response=list[TeamSeasonOut],
            description="Returns the last `limit` team season results for the given team, or for all teams if no team is specified.", tags=[ApiDocTags.TEAM, ApiDocTags.STATS])
def get_team_seasons(request: HttpRequest, team_id: int | None = None, limit: int = 2):
    team_seasons = TeamSeason.objects.exclude(season__start_date__gt=datetime.datetime.now(datetime.timezone.utc).date())
    if team_id is not None:
        team_seasons = team_seasons.filter(team_id=team_id)
    team_seasons = team_seasons.order_by('-season__start_date')[:limit]
    return team_seasons

@router.get('/team-season/{team_season_id}', response=TeamSeasonOut, tags=[ApiDocTags.TEAM, ApiDocTags.STATS])
def get_team_season(request: HttpRequest, team_season_id: int):
    team_season = get_object_or_404(TeamSeason, id=team_season_id)
    return team_season

# endregion

# region Game

@router.get('/arena/list', response=list[ArenaOut], tags=[ApiDocTags.GAME])
def get_arenas(request: HttpRequest):
    arenas = Arena.objects.all()
    return arenas

@router.get('/arena-rink/list', response=list[ArenaRinkOut], tags=[ApiDocTags.GAME])
def get_arena_rinks(request: HttpRequest):
    arena_rinks = ArenaRink.objects.all()
    return arena_rinks

@router.get('/arena-rink/{arena_rink_id}', response=ArenaRinkExtendedOut, tags=[ApiDocTags.GAME])
def get_arena_rink(request: HttpRequest, arena_rink_id: int):
    arena_rink = get_object_or_404(ArenaRink, id=arena_rink_id)
    return ArenaRinkExtendedOut(id=arena_rink.id, name=arena_rink.name, arena_id=arena_rink.arena_id, arena_name=arena_rink.arena.name)

@router.get('/game-type/list', response=list[GameTypeOut], tags=[ApiDocTags.GAME])
def get_game_types(request: HttpRequest):
    game_types = GameType.objects.all()
    game_types_out = []
    for game_type in game_types:
        game_type_out = GameTypeOut(id=game_type.id, name=game_type.name, game_type_names=[
            ObjectIdName(id=game_type_name.id, name=game_type_name.name)
            for game_type_name in game_type.gametypename_set.filter(is_actual=True)])
        game_types_out.append(game_type_out)
    return game_types_out

@router.get('/game-period/list', response=list[GamePeriodOut], tags=[ApiDocTags.GAME])
def get_game_periods(request: HttpRequest):
    game_periods = GamePeriod.objects.order_by('order')
    return game_periods

@router.get('/game/list', response=list[GameOut], tags=[ApiDocTags.GAME])
def get_games(request: HttpRequest, on_now: bool = False):
    games = Game.objects.select_related('rink', 'game_type_name')
    if on_now:
        games = games.filter(status=2)
    return games.order_by('-date').all()

@router.get('/game/list/banner', response=list[GameBannerOut], description="Returns a list of current games for the banner.", tags=[ApiDocTags.GAME])
def get_games_banner(request: HttpRequest):
    now = datetime.datetime.now(datetime.timezone.utc)
    games = Game.objects.\
        select_related('rink', 'game_type_name', 'game_period', 'home_team', 'away_team').\
        filter(Q(status=2) | (Q(status=1) & Q(date__gte=now.date()) & Q(date__lte=(now + datetime.timedelta(days=1)).date()))).order_by('date')
    games_out = []
    for game in games:
        games_out.append(GameBannerOut(id=game.id, home_team_id=game.home_team_id, away_team_id=game.away_team_id,
            home_team_name=game.home_team.name, away_team_name=game.away_team.name,
            home_team_abbreviation=game.home_team.abbreviation, away_team_abbreviation=game.away_team.abbreviation,
            date=game.date, time=game.time, game_type_name=(game.game_type_name.name if game.game_type_name is not None else None),
            arena_name=game.rink.arena.name, rink_name=game.rink.name, game_period_name=(game.game_period.name if game.game_period is not None else None),
            home_goals=game.home_goals, away_goals=game.away_goals, status=game.status))
    return games_out

@router.get('/game/list/dashboard', response=GameDashboardOut, tags=[ApiDocTags.GAME])
def get_games_dashboard(request: HttpRequest, limit: int = 5, team_id: int | None = None):
    upcoming_games_qs = Game.objects.filter(status=1).select_related('rink', 'game_type_name').order_by('date')
    previous_games_qs = Game.objects.filter(status=3).select_related('rink', 'game_type_name').order_by('-date')

    if team_id is not None:
        upcoming_games_qs = upcoming_games_qs.filter(Q(home_team_id=team_id) | Q(away_team_id=team_id))
        previous_games_qs = previous_games_qs.filter(Q(home_team_id=team_id) | Q(away_team_id=team_id))

    upcoming_games = [form_game_dashboard_game_out(game) for game in upcoming_games_qs[:limit]]
    previous_games = [form_game_dashboard_game_out(game) for game in previous_games_qs[:limit]]

    return GameDashboardOut(upcoming_games=upcoming_games, previous_games=previous_games)

@router.get('/game/{game_id}', response=GameOut, tags=[ApiDocTags.GAME])
def get_game(request: HttpRequest, game_id: int):
    game = get_object_or_404(Game.objects.select_related('rink', 'game_type_name'), id=game_id)
    return game

@router.get('/game/{game_id}/extra', response=GameExtendedOut, tags=[ApiDocTags.GAME])
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

@router.post('/game', response={200: GameOut, 400: Message, 403: Message, 503: Message}, tags=[ApiDocTags.GAME])
def add_game(request: HttpRequest, data: GameIn):
    if not is_user_coach(request.user, data.home_team_id) and not is_user_coach(request.user, data.away_team_id):
        return 403, {"message": "You are not authorized to add a game."}
    try:
        game_season = get_current_season(data.date)
        if game_season is None:
            return 503, {"message": "No current season found."}
        if data.status not in [status[0] for status in get_constant_class_int_choices(GameStatus)]:
            return 400, {"message": f"Invalid status: {data.status}"}
        if data.game_type_id in [game_type.id for game_type in GameType.objects.filter(gametypename__is_actual=True)] and data.game_type_name_id is None:
            return 400, {"message": "If game type has names, game type name must be provided."}
        with transaction.atomic(using='hockey'):
            home_no_goalie = get_no_goalie(data.home_team_id)
            away_no_goalie = get_no_goalie(data.away_team_id)
            if home_no_goalie not in data.home_goalies:
                data.home_goalies.append(home_no_goalie)
            if away_no_goalie not in data.away_goalies:
                data.away_goalies.append(away_no_goalie)
            home_defensive_zone_exit = DefensiveZoneExit.objects.create()
            home_offensive_zone_entry = OffensiveZoneEntry.objects.create()
            home_shots = Shots.objects.create()
            home_turnovers = Turnovers.objects.create()
            away_defensive_zone_exit = DefensiveZoneExit.objects.create()
            away_offensive_zone_entry = OffensiveZoneEntry.objects.create()
            away_shots = Shots.objects.create()
            away_turnovers = Turnovers.objects.create()
            if data.home_start_goalie_id is None:
                data.home_start_goalie_id = home_no_goalie.player_id
            if data.away_start_goalie_id is None:
                data.away_start_goalie_id = away_no_goalie.player_id
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
            game.full_clean()
            game.save()

            if data.status == GameStatus.GAME_OVER.id:
                GameEventsAnalysisQueue.objects.create(payload=serialize_game(game), status=GameEventSystemStatus.NEW)

    except ValidationError as e:
        return 400, {"message": str(e)}
    except IntegrityError as e:
        return resp.entry_already_exists("Game", str(e))
    game = Game.objects.get(id=game.id)
    return game

@router.patch("/game/{game_id}", response={204: None, 400: Message, 403: Message}, tags=[ApiDocTags.GAME])
def update_game(request: HttpRequest, game_id: int, data: PatchDict[GameIn]):
    game = get_object_or_404(Game, id=game_id)
    if not is_user_coach(request.user, game.home_team_id) and not is_user_coach(request.user, game.away_team_id):
        return 403, {"message": "You are not authorized to update this game."}
    game_status = game.status
    data_status = data.get('status')
    if data_status is not None and data_status not in [status[0] for status in get_constant_class_int_choices(GameStatus)]:
        return 400, {"message": f"Invalid status: {data_status}"}
    if data.get('game_type_id') in [game_type.id for game_type in GameType.objects.filter(gametypename__is_actual=True)] and data.get('game_type_name_id') is None:
        return 400, {"message": "If game type has names, game type name must be provided."}
    try:
        with transaction.atomic(using='hockey'):

            if game_status != data_status and data_status == GameStatus.GAME_OVER.id:
                # Game has finished, add its data to statistics.
                pass
            elif data_status is not None and game_status == GameStatus.GAME_OVER.id and data_status != GameStatus.GAME_OVER.id:
                # Game finish has been undone, remove its data from statistics.
                GameEventsAnalysisQueue.objects.create(payload=serialize_game(game), status=GameEventSystemStatus.DEPRECATED)
            elif game_status == GameStatus.GAME_OVER.id and data_status in [GameStatus.GAME_OVER.id, None] and len(data) > 0:
                # If game has been modified after finishing, re-apply its data to statistics.
                GameEventsAnalysisQueue.objects.create(payload=serialize_game(game), status=GameEventSystemStatus.DEPRECATED)

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

            game.full_clean()
            game.save()

            game = Game.objects.get(id=game_id)

            if game_status != data_status and data_status == GameStatus.GAME_OVER.id:
                # Game has finished, add its data to statistics.
                GameEventsAnalysisQueue.objects.create(payload=serialize_game(game), status=GameEventSystemStatus.NEW)
            elif data_status is not None and game_status == GameStatus.GAME_OVER.id and data_status != GameStatus.GAME_OVER.id:
                # Game finish has been undone, remove its data from statistics.
                pass
            elif game_status == GameStatus.GAME_OVER.id and data_status in [GameStatus.GAME_OVER.id, None] and len(data) > 0:
                # If game has been modified after finishing, re-apply its data to statistics.
                GameEventsAnalysisQueue.objects.create(payload=serialize_game(game), status=GameEventSystemStatus.NEW)
                
    except ValidationError as e:
        return 400, {"message": str(e)}
    return 204, None

@router.delete("/game/{game_id}", response={204: None, 403: Message}, tags=[ApiDocTags.GAME])
def delete_game(request: HttpRequest, game_id: int):
    game = get_object_or_404(Game, id=game_id)
    if not is_user_coach(request.user, game.home_team_id) and not is_user_coach(request.user, game.away_team_id):
        return 403, {"message": "You are not authorized to delete this game."}
    with transaction.atomic(using='hockey'):
        if game.status == GameStatus.GAME_OVER.id:
            GameEventsAnalysisQueue.objects.create(payload=serialize_game(game), status=GameEventSystemStatus.DEPRECATED)
        game.delete()
    return 204, None

@router.get("/game/defensive-zone-exit/{defensive_zone_exit_id}", response=DefensiveZoneExitOut, tags=[ApiDocTags.GAME])
def get_game_defensive_zone_exit(request: HttpRequest, defensive_zone_exit_id: int):
    defensive_zone_exit = get_object_or_404(DefensiveZoneExit, id=defensive_zone_exit_id)
    return defensive_zone_exit

@router.patch("/game/defensive-zone-exit/{defensive_zone_exit_id}", response={204: None, 403: Message}, tags=[ApiDocTags.GAME])
def update_game_defensive_zone_exit(request: HttpRequest, defensive_zone_exit_id: int, data: PatchDict[DefensiveZoneExitIn]):
    defensive_zone_exit = get_object_or_404(DefensiveZoneExit, id=defensive_zone_exit_id)
    if not is_user_coach(request.user, defensive_zone_exit.game.home_team_id) and not is_user_coach(request.user, defensive_zone_exit.game.away_team_id):
        return 403, {"message": "You are not authorized to update this game."}
    for attr, value in data.items():
        setattr(defensive_zone_exit, attr, value)
    defensive_zone_exit.save()
    return 204, None

@router.get("/game/offensive-zone-entry/{offensive_zone_entry_id}", response=OffensiveZoneEntryOut, tags=[ApiDocTags.GAME])
def get_game_offensive_zone_entry(request: HttpRequest, offensive_zone_entry_id: int):
    offensive_zone_entry = get_object_or_404(OffensiveZoneEntry, id=offensive_zone_entry_id)
    return offensive_zone_entry

@router.patch("/game/offensive-zone-entry/{offensive_zone_entry_id}", response={204: None, 403: Message}, tags=[ApiDocTags.GAME])
def update_game_offensive_zone_entry(request: HttpRequest, offensive_zone_entry_id: int, data: PatchDict[OffensiveZoneEntryIn]):
    offensive_zone_entry = get_object_or_404(OffensiveZoneEntry, id=offensive_zone_entry_id)
    if not is_user_coach(request.user, offensive_zone_entry.game.home_team_id) and not is_user_coach(request.user, offensive_zone_entry.game.away_team_id):
        return 403, {"message": "You are not authorized to update this game."}
    for attr, value in data.items():
        setattr(offensive_zone_entry, attr, value)
    offensive_zone_entry.save()
    return 204, None

@router.get("/game/shots/{shots_id}", response=ShotsOut, tags=[ApiDocTags.GAME])
def get_game_shots(request: HttpRequest, shots_id: int):
    shots = get_object_or_404(Shots, id=shots_id)
    return shots

@router.get("/game/turnovers/{turnovers_id}", response=TurnoversOut, tags=[ApiDocTags.GAME])
def get_game_turnovers(request: HttpRequest, turnovers_id: int):
    turnovers = get_object_or_404(Turnovers, id=turnovers_id)
    return turnovers

@router.get("/game/{game_id}/live-data", response=GameLiveDataOut, tags=[ApiDocTags.GAME])
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
                           events=game.gameevents_set.order_by("period__order", "-time").all())

@router.get('/game/{game_id}/events', response=list[GameEventOut], tags=[ApiDocTags.GAME])
def get_game_events(request: HttpRequest, game_id: int):
    game_events = GameEvents.objects.filter(game_id=game_id).order_by("period__order", "-time").all()
    return game_events

@router.post('/game/{game_id}/spray-chart', response=list[GameEventOut], tags=[ApiDocTags.GAME, ApiDocTags.SPRAY_CHART])
def get_game_spray_chart(request: HttpRequest, game_id: int, filters: GameSprayChartFilters):
    events = GameEvents.objects.filter(game_id=game_id)
    if filters.event_name is not None:
        events = events.prefetch_related('event_name').filter(event_name__name=filters.event_name)
    return events.all()

# endregion

# region Game players

@router.get('/game-player/game/{game_id}', response=GamePlayersOut, tags=[ApiDocTags.GAME_PLAYER])
def get_game_players(request: HttpRequest, game_id: int):
    game = get_object_or_404(Game, id=game_id)
    home_goalies = []
    home_players = []
    away_goalies = []
    away_players = []
    for home_goalie in game.home_goalies.all():
        home_goalies.append(GoalieBaseOut(id=home_goalie.player_id, first_name=home_goalie.player.first_name, last_name=home_goalie.player.last_name))
    for away_goalie in game.away_goalies.all():
        away_goalies.append(GoalieBaseOut(id=away_goalie.player_id, first_name=away_goalie.player.first_name, last_name=away_goalie.player.last_name))
    for home_player in game.home_players.all():
        home_players.append(PlayerBaseOut(id=home_player.id, first_name=home_player.first_name, last_name=home_player.last_name))
    for away_player in game.away_players.all():
        away_players.append(PlayerBaseOut(id=away_player.id, first_name=away_player.first_name, last_name=away_player.last_name))
    return GamePlayersOut(home_goalies=home_goalies, home_players=home_players, away_goalies=away_goalies, away_players=away_players)

@router.get('/game-player/goalie/{goalie_id}', response=list[GameGoalieOut], tags=[ApiDocTags.GAME_PLAYER, ApiDocTags.STATS])
def get_goalie_games(request: HttpRequest, goalie_id: int, limit: int = 5):
    goalie_games = GameGoalie.objects.filter(goalie_id=goalie_id).order_by('-game__date')[:limit]
    games: list[GameGoalieOut] = []
    for game_goalie in goalie_games:
        games.append(form_game_goalie_out(game_goalie))
    return games

@router.get('/game-player/player/{player_id}', response=list[GamePlayerOut], tags=[ApiDocTags.GAME_PLAYER, ApiDocTags.STATS])
def get_player_games(request: HttpRequest, player_id: int, limit: int = 5):
    player_games = GamePlayer.objects.filter(player_id=player_id).order_by('-game__date')[:limit]
    games: list[GamePlayerOut] = []
    for game_player in player_games:
        games.append(form_game_player_out(game_player))
    return games

# endregion

# region Game events

@router.get('/game-event-name/list', response=list[ObjectIdName], tags=[ApiDocTags.GAME_EVENT])
def get_game_event_names(request: HttpRequest):
    game_event_names = GameEventName.objects.all()
    return game_event_names

@router.get('/shot-type/list', response=list[ObjectIdName], tags=[ApiDocTags.GAME_EVENT])
def get_shot_types(request: HttpRequest):
    shot_types = ShotType.objects.order_by('name').all()
    return shot_types

@router.get('/game-event/{game_event_id}', response=GameEventOut, tags=[ApiDocTags.GAME_EVENT])
def get_game_event(request: HttpRequest, game_event_id: int):
    game_event = get_object_or_404(GameEvents, id=game_event_id)
    return game_event

@router.post('/game-event', response={200: ObjectId, 400: Message, 403: Message}, tags=[ApiDocTags.GAME_EVENT])
def add_game_event(request: HttpRequest, data: GameEventIn):
    try:

        game: Game = get_object_or_404(Game, id=data.game_id)

        if not is_user_coach(request.user, game.home_team_id) and not is_user_coach(request.user, game.away_team_id):
            return 403, {"message": "You are not authorized to add a game event."}

        with transaction.atomic(using='hockey'):

            event_name = GameEventName.objects.filter(id=data.event_name_id).first()

            if event_name.name == EventName.GOALIE_CHANGE and data.goalie_id is None:
                data.goalie_id = get_no_goalie(data.team_id).pk

            if data.goalie_id is None and data.player_id is None and data.player_2_id is None:
                raise ValueError("Please specify goalie ID and/or player ID(s).")

            data_new = data.dict()

            if game.status == GameStatus.GAME_OVER.id:
                old_game_stats = serialize_game(game)
            else:
                old_game_stats = None

            game_event = GameEvents.objects.create(**data_new)

            if event_name is None:
                raise ValueError(f"event_name_id {data.event_name_id} not found.")

            if game_event.shot_type is not None and event_name.name != EventName.SHOT:
                raise ValueError(f"Shot type is only allowed for '{EventName.SHOT}' events.")

            affect_stats_level = None

            if event_name.name == EventName.SHOT:
                error = update_game_shots_from_event(game, data=data, is_deleted=False)
                if error is not None:
                    raise ValueError(error)
                elif game_event.shot_type.name.lower() == 'goal':
                    affect_stats_level = 'game'
                else:
                    affect_stats_level = 'game_event'
            elif event_name.name == EventName.TURNOVER:
                error = update_game_turnovers_from_event(game, data=data, is_deleted=False)
                if error is not None:
                    raise ValueError(error)
                else:
                    affect_stats_level = 'game_event'
            elif event_name.name == EventName.FACEOFF:
                error = update_game_faceoffs_from_event(game, data=data, is_deleted=False)
                if error is not None:
                    raise ValueError(error)
                else:
                    affect_stats_level = 'game_event'
            elif event_name.name == EventName.PENALTY:
                affect_stats_level = 'game_event'
            elif event_name.name == EventName.GOALIE_CHANGE:
                affect_stats_level = 'game'

            if game.status == GameStatus.GAME_OVER.id:
                if affect_stats_level == 'game':
                    if old_game_stats is None:
                        raise Exception("Game stats are not available.")
                    GameEventsAnalysisQueue.objects.create(payload=old_game_stats, status=GameEventSystemStatus.DEPRECATED)
                    GameEventsAnalysisQueue.objects.create(payload=serialize_game(game), status=GameEventSystemStatus.NEW)
                elif affect_stats_level == 'game_event':
                    GameEventsAnalysisQueue.objects.create(payload=serialize_game_event(game_event), status=GameEventSystemStatus.NEW)

    except ValueError as e:
        return 400, {"message": str(e)}
    except IntegrityError as e:
        return resp.entry_already_exists("Game event", str(e))
    return {"id": game_event.id}

@router.patch("/game-event/{game_event_id}", response={204: None, 400: Message, 403: Message}, tags=[ApiDocTags.GAME_EVENT])
def update_game_event(request: HttpRequest, game_event_id: int, data: PatchDict[GameEventIn]):

    game_event = get_object_or_404(GameEvents, id=game_event_id)
    game: Game = game_event.game

    if not is_user_coach(request.user, game.home_team_id) and not is_user_coach(request.user, game.away_team_id):
        return 403, {"message": "You are not authorized to update this game event."}

    try:
        with transaction.atomic(using='hockey'):

            if game.status == GameStatus.GAME_OVER.id:
                old_game_stats = serialize_game(game)
                old_game_event_stats = serialize_game_event(game_event)
            else:
                old_game_stats = None
                old_game_event_stats = None

            affect_stats_level = None

            # Undo old shot/turnover data.
            if game_event.event_name.name == EventName.SHOT:
                error = update_game_shots_from_event(game, event=game_event, is_deleted=True)
                if error is not None:
                    raise ValueError(error)
                elif game_event.shot_type.name.lower() == 'goal':
                    affect_stats_level = 'game'
                else:
                    affect_stats_level = 'game_event'
            elif game_event.event_name.name == EventName.TURNOVER:
                error = update_game_turnovers_from_event(game, event=game_event, is_deleted=True)
                if error is not None:
                    raise ValueError(error)
                else:
                    affect_stats_level = 'game_event'
            elif game_event.event_name.name == EventName.FACEOFF:
                error = update_game_faceoffs_from_event(game, event=game_event, is_deleted=True)
                if error is not None:
                    raise ValueError(error)
                else:
                    affect_stats_level = 'game_event'
            elif game_event.event_name.name == EventName.PENALTY:
                affect_stats_level = 'game_event'
            elif game_event.event_name.name == EventName.GOALIE_CHANGE:
                affect_stats_level = 'game'

            game_event.save()

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
                elif game_event.shot_type.name.lower() == 'goal':
                    affect_stats_level = 'game'
                elif affect_stats_level is None:
                    affect_stats_level = 'game_event'
            elif game_event.event_name.name == EventName.TURNOVER:
                error = update_game_turnovers_from_event(game, event=game_event, is_deleted=False)
                if error is not None:
                    raise ValueError(error)
                elif affect_stats_level is None:
                    affect_stats_level = 'game_event'
            elif game_event.event_name.name == EventName.FACEOFF:
                error = update_game_faceoffs_from_event(game, event=game_event, is_deleted=False)
                if error is not None:
                    raise ValueError(error)
                elif affect_stats_level is None:
                    affect_stats_level = 'game_event'
            elif game_event.event_name.name == EventName.PENALTY:
                if affect_stats_level is None:
                    affect_stats_level = 'game_event'
            elif game_event.event_name.name == EventName.GOALIE_CHANGE:
                affect_stats_level = 'game'

            if game.status == GameStatus.GAME_OVER.id:
                if affect_stats_level == 'game':
                    if old_game_stats is None:
                        raise Exception("Game stats are not available.")
                    GameEventsAnalysisQueue.objects.create(payload=old_game_stats, status=GameEventSystemStatus.DEPRECATED)
                    GameEventsAnalysisQueue.objects.create(payload=serialize_game(game), status=GameEventSystemStatus.NEW)
                elif affect_stats_level == 'game_event':
                    if old_game_event_stats is None:
                        raise Exception("Game event stats are not available.")
                    GameEventsAnalysisQueue.objects.create(payload=old_game_event_stats, status=GameEventSystemStatus.DEPRECATED)
                    GameEventsAnalysisQueue.objects.create(payload=serialize_game_event(game_event), status=GameEventSystemStatus.NEW)

    except ValueError as e:
        return 400, {"message": str(e)}

    return 204, None

@router.delete("/game-event/{game_event_id}", response={204: None, 403: Message}, tags=[ApiDocTags.GAME_EVENT])
def delete_game_event(request: HttpRequest, game_event_id: int):
    game_event = get_object_or_404(GameEvents, id=game_event_id)
    game: Game = game_event.game

    if not is_user_coach(request.user, game.home_team_id) and not is_user_coach(request.user, game.away_team_id):
        return 403, {"message": "You are not authorized to delete this game event."}

    if game.status == GameStatus.GAME_OVER.id:
        old_game_stats = serialize_game(game)
        old_game_event_stats = serialize_game_event(game_event)
    else:
        old_game_stats = None
        old_game_event_stats = None

    try:
        with transaction.atomic(using='hockey'):

            affect_stats_level = None

            if game_event.event_name.name == EventName.SHOT:
                error = update_game_shots_from_event(game_event.game, event=game_event, is_deleted=True)
                if error is not None:
                    raise ValueError(error)
                elif game_event.shot_type.name.lower() == 'goal':
                    affect_stats_level = 'game'
                else:
                    affect_stats_level = 'game_event'
            elif game_event.event_name.name == EventName.TURNOVER:
                error = update_game_turnovers_from_event(game_event.game, event=game_event, is_deleted=True)
                if error is not None:
                    raise ValueError(error)
                else:
                    affect_stats_level = 'game_event'
            elif game_event.event_name.name == EventName.FACEOFF:
                error = update_game_faceoffs_from_event(game_event.game, event=game_event, is_deleted=True)
                if error is not None:
                    raise ValueError(error)
                else:
                    affect_stats_level = 'game_event'
            elif game_event.event_name.name == EventName.PENALTY:
                affect_stats_level = 'game_event'
            elif game_event.event_name.name == EventName.GOALIE_CHANGE:
                affect_stats_level = 'game'

            game_event.delete()

            if game_event.game.status == GameStatus.GAME_OVER.id:
                if affect_stats_level == 'game':
                    if old_game_stats is None:
                        raise Exception("Game stats are not available.")
                    GameEventsAnalysisQueue.objects.create(payload=old_game_stats, status=GameEventSystemStatus.DEPRECATED)
                    GameEventsAnalysisQueue.objects.create(payload=serialize_game(game), status=GameEventSystemStatus.NEW)
                elif affect_stats_level == 'game_event':
                    if old_game_event_stats is None:
                        raise Exception("Game event stats are not available.")
                    GameEventsAnalysisQueue.objects.create(payload=old_game_event_stats, status=GameEventSystemStatus.DEPRECATED)

    except ValueError as e:
        return 400, {"message": str(e)}

    return 204, None

# endregion

# region Highlight reels

@router.get('/highlight-reels', response=list[HighlightReelListOut], tags=[ApiDocTags.HIGHLIGHT_REEL])
def get_highlight_reels(request: HttpRequest):
    highlight_reels = HighlightReel.objects.all() # TODO: filter by current user
    highlight_reels_out = []
    
    user_ids = list(set([reel.user_id for reel in highlight_reels if reel.user_id is not None]))
    users = {user.id: user for user in User.objects.using('default').filter(id__in=user_ids)} if user_ids else {}
    
    for reel in highlight_reels:
        user = users.get(reel.user_id) if reel.user_id else None
        created_by = f'{user.first_name} {user.last_name}' if user is not None else "?"
        highlight_reels_out.append(HighlightReelListOut(id=reel.id, name=reel.name, description=reel.description,
                                                        date=reel.date, created_by=created_by))
    return highlight_reels_out

@router.post('/highlight-reels', response={200: ObjectId, 400: Message},
             description=("Create a new highlight reel and add highlights to it.\n\n"
             "Each highlight should have either a game event ID or a custom event fields filled in."), tags=[ApiDocTags.HIGHLIGHT_REEL])
def add_highlight_reel(request: HttpRequest, data: HighlightReelIn):
    try:
        with transaction.atomic(using='hockey'):
            highlight_reel = HighlightReel.objects.create(name=data.name, description=data.description, user_id=request.user.id)
            for highlight in data.highlights:
                create_highlight(highlight, highlight_reel, request.user.id)
    except ValueError as e:
        return 400, {"message": str(e)}
    return {"id": highlight_reel.id}

@router.put('/highlight-reels/{highlight_reel_id}', response={204: None, 400: Message, 403: Message},
    description=("Update a highlight reel.\n\n"
                 "If id is provided for a highlight, it will be updated, otherwise a new highlight will be created.\n\n"
                 "Not provided highlights will be deleted."), tags=[ApiDocTags.HIGHLIGHT_REEL])
def update_highlight_reel(request: HttpRequest, highlight_reel_id: int, data: HighlightReelUpdateIn):
    highlight_reel = get_object_or_404(HighlightReel, id=highlight_reel_id)
    if highlight_reel.user_id != request.user.id and not is_user_admin(request.user):
        return 403, {"message": "You are not authorized to update this highlight reel."}
    highlight_reel.name = data.name
    highlight_reel.description = data.description
    keep_highlights = []
    for highlight in data.highlights:
        if highlight.id is not None:
            keep_highlights.append(highlight.id)
    highlights_to_delete = highlight_reel.highlights.exclude(id__in=keep_highlights)
    try:
        with transaction.atomic(using='hockey'):
            for highlight in highlights_to_delete:
                highlight.delete()
            for highlight_data in data.highlights:
                if highlight_data.id is None:
                    create_highlight(highlight_data, highlight_reel, request.user.id)
                else:
                    highlight = get_object_or_404(Highlight, id=highlight_data.id)
                    # This returns only fields that were explicitly set in the request
                    provided_fields = highlight_data.dict(exclude_unset=True)
                    if "order" in provided_fields:
                        highlight.order = highlight_data.order
                    if ((provided_fields.get("event_name") is not None or provided_fields.get("note") is not None) and
                        provided_fields.get("game_event_id") is not None):
                        raise ValueError("If game event ID is provided, none of the other fields except order should be provided.")
                    if "game_event_id" in provided_fields:
                        if highlight.custom_event is not None:
                            highlight.custom_event.delete()
                        highlight.game_event_id = highlight_data.game_event_id
                    if "event_name" in provided_fields and "note" in provided_fields:
                        highlight.game_event_id = None
                        highlight.custom_event = CustomEvents.objects.create(event_name=highlight_data.event_name, note=highlight_data.note,
                            youtube_link=highlight_data.youtube_link, date=highlight_data.date, time=highlight_data.time, user_id=request.user.id)
                        highlight.save()
                highlight_reel.save()
    except ValueError as e:
        return 400, {"message": str(e)}
    return 204, None

@router.delete('/highlight-reels/{highlight_reel_id}', response={204: None, 403: Message}, tags=[ApiDocTags.HIGHLIGHT_REEL])
def delete_highlight_reel(request: HttpRequest, highlight_reel_id: int):
    highlight_reel = get_object_or_404(HighlightReel, id=highlight_reel_id)
    if highlight_reel.user_id != request.user.id and not is_user_admin(request.user):
        return 403, {"message": "You are not authorized to delete this highlight reel."}
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

@router.get('/highlight-reels/{highlight_reel_id}/highlights', response=list[HighlightOut], tags=[ApiDocTags.HIGHLIGHT_REEL])
def get_highlight_reel_highlights(request: HttpRequest, highlight_reel_id: int):
    highlight_reel = get_object_or_404(HighlightReel, id=highlight_reel_id)
    return highlight_reel.highlights.order_by('order').all()

@router.post('/highlight-reels/{highlight_reel_id}/highlights', response={200: ObjectId, 400: Message}, tags=[ApiDocTags.HIGHLIGHT_REEL])
def add_highlight(request: HttpRequest, highlight_reel_id: int, data: HighlightIn):
    highlight_reel = get_object_or_404(HighlightReel, id=highlight_reel_id)
    if highlight_reel.user_id != request.user.id and not is_user_admin(request.user):
        return 403, {"message": "You are not authorized to add a highlight to this highlight reel."}
    try:
        with transaction.atomic(using='hockey'):
            highlight = create_highlight(data, highlight_reel, request.user.id)
    except ValueError as e:
        return 400, {"message": str(e)}
    return {"id": highlight.id}

@router.delete('/highlights/{highlight_id}', response={204: None, 400: Message}, tags=[ApiDocTags.HIGHLIGHT_REEL])
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

# region Video Library

@router.get('/video-library', response=list[VideoLibraryOut], tags=[ApiDocTags.VIDEO_LIBRARY])
def get_video_library(request: HttpRequest):
    video_library = VideoLibrary.objects.all()
    video_library_out = []
    user_ids = list(set([video.user_id for video in video_library if video.user_id is not None]))
    users = {user.id: user for user in User.objects.using('default').filter(id__in=user_ids)} if user_ids else {}
    for video in video_library:
        user = users.get(video.user_id) if video.user_id else None
        added_by = f'{user.first_name} {user.last_name}' if user is not None else "?"
        video_library_out.append(VideoLibraryOut(id=video.id, name=video.name, description=video.description,
            youtube_link=video.youtube_link, added_by=added_by, date=video.date))
    return video_library_out

@router.post('/video-library', response={200: ObjectId, 400: Message}, tags=[ApiDocTags.VIDEO_LIBRARY])
def add_video_library(request: HttpRequest, data: VideoLibraryIn):
    video_library = VideoLibrary.objects.create(name=data.name, description=data.description, youtube_link=data.youtube_link, user_id=request.user.id)
    return {"id": video_library.id}

@router.patch('/video-library/{video_library_id}', response={204: None, 400: Message}, tags=[ApiDocTags.VIDEO_LIBRARY])
def update_video_library(request: HttpRequest, video_library_id: int, data: PatchDict[VideoLibraryIn]):
    video_library = get_object_or_404(VideoLibrary, id=video_library_id)
    for attr, value in data.items():
        setattr(video_library, attr, value)
    video_library.save()
    return 204, None

@router.delete('/video-library/{video_library_id}', response={204: None, 400: Message}, tags=[ApiDocTags.VIDEO_LIBRARY])
def delete_video_library(request: HttpRequest, video_library_id: int):
    video_library = get_object_or_404(VideoLibrary, id=video_library_id)
    video_library.delete()
    return 204, None

# endregion
