import datetime
import os
import re
from django.conf import settings
from django.db.models import Q
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

from .schemas import (ArenaOut, ArenaRinkOut, DefensiveZoneExitIn, GameDashboardOut, GameEventIn, GameEventOut, GameGoalieOut,
                      GameIn, GameOut, GamePlayerOut, GamePlayersIn, GamePlayersOut, GoalieSeasonOut,
                      GoalieSeasonsGet, ObjectIdName, Message, ObjectId, OffensiveZoneEntryIn, PlayerPositionOut, GoalieIn,
                      GoalieOut, PlayerIn, PlayerOut, PlayerSeasonOut, PlayerSeasonsGet, SeasonIn, SeasonOut, ShotsIn,
                      TeamIn, TeamOut, TeamSeasonIn, TeamSeasonOut, TurnoversIn)
from .models import (Arena, ArenaRink, DefensiveZoneExit, Division, Game, GameEventName, GameEvents, GameEventsAnalysisQueue,
                     GameGoalie, GamePeriod, GamePlayer, GameType, Goalie, GoalieSeason, OffensiveZoneEntry, Player,
                     PlayerPosition, PlayerSeason, Season, Shots, Team, TeamLevel, TeamSeason, Turnovers)
from .utils import api_response_templates as resp
from .utils.db_utils import form_game_goalie_out, form_game_player_out, form_goalie_out, form_player_out, get_current_season

router = Router(tags=["Hockey"])

# region Goalie, player

@router.get('/player-position/list', response=list[PlayerPositionOut])
def get_player_positions(request: HttpRequest):
    positions = PlayerPosition.objects.all()
    return positions

@router.get('/goalie/list', response=list[GoalieOut])
def get_goalies(request: HttpRequest, team_id: int | None = None):
    current_season = get_current_season()
    goalies_out: list[GoalieOut] = []
    goalies = Goalie.objects.all()
    if team_id is not None:
        goalies = goalies.filter(team_id=team_id)
    for goalie in goalies:
        goalies_out.append(form_goalie_out(goalie, current_season))
    return goalies_out

@router.get('/goalie/{goalie_id}', response=GoalieOut)
def get_goalie(request: HttpRequest, goalie_id: int):
    goalie = get_object_or_404(Goalie, id=goalie_id)
    current_season = get_current_season()
    return form_goalie_out(goalie, current_season)

@router.get('/goalie/{goalie_id}/photo', response=bytes)
def get_goalie_photo(request: HttpRequest, goalie_id: int):
    goalie = get_object_or_404(Goalie, id=goalie_id)
    return FileResponse(goalie.photo.open())

@router.post('/goalie', response={200: ObjectId, 400: Message, 503: Message})
def add_goalie(request: HttpRequest, data: GoalieIn, photo: File[UploadedFile] = None):
    try:
        goalie = Goalie(**data.dict())
        goalie.photo = photo
        goalie.save()
    except IntegrityError as e:
        return resp.entry_already_exists("Goalie", str(e))
    return {"id": goalie.id}

@router.patch("/goalie/{goalie_id}", response={204: None})
def update_goalie(request: HttpRequest, goalie_id: int, data: PatchDict[GoalieIn], photo: File[UploadedFile] = None):
    goalie = get_object_or_404(Goalie, id=goalie_id)
    for attr, value in data.items():
        setattr(goalie, attr, value)
    if photo is not None:
        goalie.photo = photo
    try:
        goalie.save()
    except IntegrityError:
        return resp.entry_already_exists("Goalie")
    return 204, None

@router.delete("/goalie/{goalie_id}", response={204: None})
def delete_goalie(request: HttpRequest, goalie_id: int):
    goalie = get_object_or_404(Goalie, id=goalie_id)
    goalie.delete()
    return 204, None

@router.post("/goalie/seasons", response=list[GoalieSeasonOut])
def get_goalie_seasons(request: HttpRequest, data: GoalieSeasonsGet):
    return GoalieSeason.objects.filter(goalie_id=data.goalie_id, season_id__in=data.season_ids)

@router.get('/player/list', response=list[PlayerOut])
def get_players(request: HttpRequest, team_id: int | None = None):
    current_season = get_current_season()
    players_out: list[PlayerOut] = []
    players = Player.objects.all()
    if team_id is not None:
        players = players.filter(team_id=team_id)
    for player in players:
        players_out.append(form_player_out(player, current_season))
    return players_out

@router.get('/player/{player_id}', response=PlayerOut)
def get_player(request: HttpRequest, player_id: int):
    player = get_object_or_404(Player, id=player_id)
    current_season = get_current_season()
    return form_player_out(player, current_season)

@router.get('/player/{player_id}/photo', response=bytes)
def get_player_photo(request: HttpRequest, player_id: int):
    player = get_object_or_404(Player, id=player_id)
    return FileResponse(player.photo.open())

@router.post('/player', response={200: ObjectId, 400: Message})
def add_player(request: HttpRequest, data: PlayerIn, photo: File[UploadedFile] = None):
    try:
        player = Player(**data.dict())
        player.photo = photo
        player.save()
    except IntegrityError as e:
        return resp.entry_already_exists("Player", str(e))
    return {"id": player.id}

@router.patch("/player/{player_id}", response={204: None})
def update_player(request: HttpRequest, player_id: int, data: PatchDict[PlayerIn], photo: File[UploadedFile] = None):
    player = get_object_or_404(Player, id=player_id)
    for attr, value in data.items():
        setattr(player, attr, value)
    if photo is not None:
        player.photo = photo
    try:
        player.save()
    except IntegrityError:
        return resp.entry_already_exists("Player")
    return 204, None

@router.delete("/player/{player_id}", response={204: None})
def delete_player(request: HttpRequest, player_id: int):
    player = get_object_or_404(Player, id=player_id)
    player.delete()
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

@router.get('/game-type/list', response=list[ObjectIdName])
def get_game_types(request: HttpRequest):
    game_types = GameType.objects.all()
    return game_types

@router.get('/game-period/list', response=list[ObjectIdName])
def get_game_periods(request: HttpRequest):
    game_periods = GamePeriod.objects.all()
    return game_periods

@router.get('/game/list', response=list[GameOut])
def get_games(request: HttpRequest, on_now: bool = False):
    games = Game.objects.exclude(is_deprecated=True)
    if on_now:
        games = games.filter(status=2)
    return games.order_by('-date').all()

@router.get('/game/list/dashboard', response=GameDashboardOut)
def get_games_dashboard(request: HttpRequest, limit: int = 5, team_id: int | None = None):
    upcoming_games = Game.objects.exclude(is_deprecated=True).filter(status=1).order_by('date')
    previous_games = Game.objects.exclude(is_deprecated=True).filter(status=3).order_by('-date')

    if team_id is not None:
        upcoming_games = upcoming_games.filter(Q(home_team_id=team_id) | Q(away_team_id=team_id))
        previous_games = previous_games.filter(Q(home_team_id=team_id) | Q(away_team_id=team_id))

    return GameDashboardOut(upcoming_games=upcoming_games[:limit], previous_games=previous_games[:limit])

@router.get('/game/{game_id}', response=GameOut)
def get_game(request: HttpRequest, game_id: int):
    game = get_object_or_404(Game, id=game_id)
    return game

@router.post('/game', response={200: GameOut, 400: Message, 503: Message})
def add_game(request: HttpRequest, data: GameIn):
    try:
        if data.date.month <= 9:
            season_start = data.date.year - 1
        else:
            season_start = data.date.year
        game_season = Season.objects.filter(name__startswith=season_start)
        with transaction.atomic():
            home_defensive_zone_exit = DefensiveZoneExit.objects.create()
            home_offensive_zone_entry = OffensiveZoneEntry.objects.create()
            home_shots = Shots.objects.create()
            home_turnovers = Turnovers.objects.create()
            away_defensive_zone_exit = DefensiveZoneExit.objects.create()
            away_offensive_zone_entry = OffensiveZoneEntry.objects.create()
            away_shots = Shots.objects.create()
            away_turnovers = Turnovers.objects.create()
            game = Game.objects.create(home_defensive_zone_exit=home_defensive_zone_exit,
                        home_offensive_zone_entry=home_offensive_zone_entry,
                        home_shots=home_shots,
                        home_turnovers=home_turnovers,
                        away_defensive_zone_exit=away_defensive_zone_exit,
                        away_offensive_zone_entry=away_offensive_zone_entry,
                        away_shots=away_shots,
                        away_turnovers=away_turnovers,
                        season=game_season,
                        **data.dict())
            if data.status == 3:
                GameEventsAnalysisQueue.objects.create(game=game, action=1)
    except IntegrityError as e:
        return resp.entry_already_exists("Game", str(e))
    game = Game.objects.get(id=game.id)
    return game

@router.patch("/game/{game_id}", response={204: None})
def update_game(request: HttpRequest, game_id: int, data: PatchDict[GameIn]):
    game = get_object_or_404(Game, id=game_id)
    data_status = data['status']
    with transaction.atomic():
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
            
        for attr, value in data.items():
            setattr(game, attr, value)
        game.save()
    return 204, None

@router.delete("/game/{game_id}", response={204: None})
def delete_game(request: HttpRequest, game_id: int):
    game = get_object_or_404(Game, id=game_id)
    with transaction.atomic():
        GameEventsAnalysisQueue.objects.create(game=game, action=3)
        game.is_deprecated = True
        game.save()
    return 204, None

@router.patch("/game/defensive-zone-exit/{defensive_zone_exit_id}", response={204: None})
def update_game_defensive_zone_exit(request: HttpRequest, defensive_zone_exit_id: int, data: PatchDict[DefensiveZoneExitIn]):
    defensive_zone_exit = get_object_or_404(DefensiveZoneExit, id=defensive_zone_exit_id)
    for attr, value in data.items():
        setattr(defensive_zone_exit, attr, value)
    defensive_zone_exit.save()
    return 204, None

@router.patch("/game/offensive-zone-entry/{offensive_zone_entry_id}", response={204: None})
def update_game_offensive_zone_entry(request: HttpRequest, offensive_zone_entry_id: int, data: PatchDict[OffensiveZoneEntryIn]):
    offensive_zone_entry = get_object_or_404(OffensiveZoneEntry, id=offensive_zone_entry_id)
    for attr, value in data.items():
        setattr(offensive_zone_entry, attr, value)
    offensive_zone_entry.save()
    return 204, None

@router.patch("/game/shots/{shots_id}", response={204: None})
def update_game_shots(request: HttpRequest, shots_id: int, data: PatchDict[ShotsIn]):
    shots = get_object_or_404(Shots, id=shots_id)
    for attr, value in data.items():
        setattr(shots, attr, value)
    shots.save()
    return 204, None

@router.patch("/game/turnovers/{turnovers_id}", response={204: None})
def update_turnovers(request: HttpRequest, turnovers_id: int, data: PatchDict[TurnoversIn]):
    turnovers = get_object_or_404(Turnovers, id=turnovers_id)
    for attr, value in data.items():
        setattr(turnovers, attr, value)
    turnovers.save()
    return 204, None

# endregion

# region Game players

@router.get('/game-player/game/{game_id}', response=GamePlayersOut)
def get_game_players(request: HttpRequest, game_id: int):
    game = get_object_or_404(Game, id=game_id)
    home_goalies = []
    home_players = []
    away_goalies = []
    away_players = []
    for game_goalie in game.game_goalie_set:
        home_away = (home_goalies if game_goalie.goalie.team_id == game.home_team_id else away_goalies)
        home_away.append(form_game_goalie_out(game_goalie))
    for game_player in game.game_player_set:
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
    with transaction.atomic():
        for goalie_id in data.goalie_ids:
            GameGoalie.objects.create(game_id=game_id, goalie_id=goalie_id)
        for player_id in data.player_ids:
            GamePlayer.objects.create(game_id=game_id, player_id=player_id)
    return 204, None

# endregion

# region Game events

@router.get('/game-event-name/list', response=list[ObjectIdName])
def get_game_event_names(request: HttpRequest):
    game_event_names = GameEventName.objects.all()
    return game_event_names

@router.get('/game-event/list', response=list[GameEventOut])
def get_game_events(request: HttpRequest, game_id: int | None = None):
    game_events = GameEvents.objects.prefetch_related('players').exclude(is_deprecated=True)
    if game_id is not None:
        game_events = game_events.filter(game_id=game_id)
    game_events = game_events.order_by("number").all()
    return game_events

@router.get('/game-event/{game_event_id}', response=GameEventOut)
def get_game_event(request: HttpRequest, game_event_id: int):
    game_event = get_object_or_404(GameEvents.objects.prefetch_related('players'), id=game_event_id)
    return game_event

@router.post('/game-event', response={200: ObjectId, 400: Message})
def add_game_event(request: HttpRequest, data: GameEventIn):
    try:
        if data.goalie_id is None and data.player_id is None and data.player_2_id is None:
            return 400, {"message": "Please specify goalie ID or player IDs."}
        data_new = data.dict()
        previous_event = GameEvents.objects.filter(game_id=data.game_id).order_by('-number').first()
        data_new['number'] = (1 if previous_event is None else (previous_event.number + 1))
        game_event = GameEvents.objects.create(**data_new)
    except IntegrityError as e:
        return resp.entry_already_exists("Game event", str(e))
    return {"id": game_event.id}

@router.patch("/game-event/{game_event_id}", response={204: None, 400: Message})
def update_game_event(request: HttpRequest, game_event_id: int, data: PatchDict[GameEventIn]):
    with transaction.atomic():

        game_event = get_object_or_404(GameEvents, id=game_event_id)
        game_event.is_deprecated = True
        game_event.save()

        GameEventsAnalysisQueue.objects.create(game_event=game_event, action=3)

        # Create the copy without deprecation.
        game_event.pk = None
        game_event._state.adding = True
        game_event.save()

        game_event.is_deprecated = False

        for attr, value in data.items():
            setattr(game_event, attr, value)
        if game_event.goalie is None and game_event.player is None and game_event.player_2 is None:
            return 400, {"message": "Please specify goalie ID or player IDs."}
        game_event.save()

        GameEventsAnalysisQueue.objects.create(game_event=game_event, action=1)

    return 204, None

@router.delete("/game-event/{game_event_id}", response={204: None})
def delete_game_event(request: HttpRequest, game_event_id: int):
    game_event = get_object_or_404(GameEvents, id=game_event_id)
    last_event = GameEvents.objects.filter(game_id=game_event.game_id).order_by('-number').first()
    with transaction.atomic():
        if last_event.number != game_event.number:
            # We are deleting event from middle of list: recalculate event numbers for this game.
            events = GameEvents.objects.filter(game_id=game_event.game_id).exclude(id=game_event_id).order_by('number')
            for i, evt in enumerate(events):
                evt.number = i + 1
                evt.save()
        game_event.is_deprecated = True
        game_event.save()
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
