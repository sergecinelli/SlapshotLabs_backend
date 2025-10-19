import datetime
import os
from django.conf import settings
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
from .schemas import (ArenaOut, ArenaRinkOut, DefensiveZoneExitIn, GameEventIn, GameEventOut, GameGoalieIn, GameGoalieOut, GameIn, GameOut, GamePlayerIn, GamePlayerOut, GamePlayersIn, GamePlayersOut, ObjectIdName, Message, ObjectId, OffensiveZoneEntryIn, PlayerPositionOut, GoalieIn, GoalieOut, PlayerIn, PlayerOut, SeasonIn, SeasonOut, ShotsIn,
                      TeamIn, TeamOut, TeamSeasonIn, TeamSeasonOut, TurnoversIn)
from .models import Arena, ArenaRink, DefensiveZoneExit, Division, Game, GameEventName, GameEvents, GameGoalie, GamePeriod, GamePlayer, GameType, Goalie, OffensiveZoneEntry, Player, PlayerPosition, Season, Shots, Team, TeamLevel, TeamSeason, Turnovers
from .utils import api_response_templates as resp

router = Router(tags=["Hockey"])

# region Goalie, player

@router.get('/player-position/list', response=list[PlayerPositionOut])
def get_player_positions(request: HttpRequest):
    positions = PlayerPosition.objects.all()
    return positions

@router.get('/goalie/list', response=list[GoalieOut])
def get_goalies(request: HttpRequest, team_id: int | None = None):
    goalies = Goalie.objects.all()
    if team_id is not None:
        goalies = goalies.filter(team_id=team_id)
    return goalies

@router.get('/goalie/{goalie_id}', response=GoalieOut)
def get_goalie(request: HttpRequest, goalie_id: int):
    goalie = get_object_or_404(Goalie, id=goalie_id)
    return goalie

@router.post('/goalie', response={200: ObjectId, 400: Message, 503: Message})
def add_goalie(request: HttpRequest, data: GoalieIn, photo: File[UploadedFile] = None):
    goalie_position = PlayerPosition.objects.filter(name__iexact="goalie")
    if len(goalie_position) == 0:
        return 503, {'message': "Can't reconcile dependencies. Please try again later."}
    position_id = goalie_position[0].id
    try:
        goalie = Goalie(position_id=position_id, **data.dict())
        goalie.photo = photo
        goalie.save()
    except IntegrityError as e:
        return resp.entry_already_exists("Goalie", str(e))
    return {"id": goalie.id}

@router.patch("/goalie/{goalie_id}", response={204: None})
def update_goalie(request: HttpRequest, goalie_id: int, data: PatchDict[GoalieIn]):
    goalie = get_object_or_404(Goalie, id=goalie_id)
    for attr, value in data.items():
        setattr(goalie, attr, value)
    goalie.save()
    return 204, None

@router.delete("/goalie/{goalie_id}", response={204: None})
def delete_goalie(request: HttpRequest, goalie_id: int):
    goalie = get_object_or_404(Goalie, id=goalie_id)
    goalie.delete()
    return 204, None

@router.get('/player/list', response=list[PlayerOut])
def get_players(request: HttpRequest, team_id: int | None = None):
    players = Player.objects.all()
    if team_id is not None:
        players = players.filter(team_id=team_id)
    return players

@router.get('/player/{player_id}', response=PlayerOut)
def get_player(request: HttpRequest, player_id: int):
    player = get_object_or_404(Player, id=player_id)
    return player

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
def update_player(request: HttpRequest, player_id: int, data: PatchDict[PlayerIn]):
    player = get_object_or_404(Player, id=player_id)
    for attr, value in data.items():
        setattr(player, attr, value)
    player.save()
    return 204, None

@router.delete("/player/{player_id}", response={204: None})
def delete_player(request: HttpRequest, player_id: int):
    player = get_object_or_404(Player, id=player_id)
    player.delete()
    return 204, None

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

@router.post('/season', response=ObjectId)
def add_season(request: HttpRequest, data: SeasonIn):
    try:
        season = Season.objects.create(**data.dict())
    except IntegrityError as e:
        return resp.entry_already_exists("Season", str(e))
    return {"id": season.id}

@router.patch("/season/{season_id}", response={204: None})
def update_season(request: HttpRequest, season_id: int, data: PatchDict[SeasonIn]):
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

@router.get('/team-season/list', response=list[TeamSeasonOut])
def get_team_seasons(request: HttpRequest):
    team_seasons = TeamSeason.objects.all()
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
def get_games(request: HttpRequest):
    games = Game.objects.all()
    return games

@router.get('/game/{game_id}', response=GameOut)
def get_game(request: HttpRequest, game_id: int):
    game = get_object_or_404(Game, id=game_id)
    return game

@router.post('/game', response={200: GameOut, 400: Message, 503: Message})
def add_game(request: HttpRequest, data: GameIn):
    try:
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
                        **data.dict())
    except IntegrityError as e:
        return resp.entry_already_exists("Game", str(e))
    game = Game.objects.get(id=game.id)
    return game

@router.patch("/game/{game_id}", response={204: None})
def update_game(request: HttpRequest, game_id: int, data: PatchDict[GameIn]):
    game = get_object_or_404(Game, id=game_id)
    for attr, value in data.items():
        setattr(game, attr, value)
    game.save()
    return 204, None

@router.delete("/game/{game_id}", response={204: None})
def delete_game(request: HttpRequest, game_id: int):
    game = get_object_or_404(Game, id=game_id)
    game.delete()
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

@router.get('/game-player/list', response=GamePlayersOut)
def get_game_players(request: HttpRequest, game_id: int):
    game = get_object_or_404(Game, id=game_id)
    home_goalies = []
    home_players = []
    away_goalies = []
    away_players = []
    for game_goalie in game.game_goalie_set:
        home_away = (home_goalies if game_goalie.goalie.team_id == game.home_team_id else away_goalies)
        home_away.append(GameGoalieOut(
            first_name=game_goalie.goalie.first_name,
            last_name=game_goalie.goalie.last_name,
            goals_against=game_goalie.goals_against,
            saves=game_goalie.saves
        ))
    for game_player in game.game_player_set:
        home_away = (home_players if game_player.player.team_id == game.home_team_id else away_players)
        home_away.append(GamePlayerOut(
            first_name=game_player.player.first_name,
            last_name=game_player.player.last_name,
            goals=game_player.goals,
            assists=game_player.assists,
            shots=game_player.shots
        ))
    return GamePlayersOut(home_goalies=home_goalies, home_players=home_players, away_goalies=away_goalies, away_players=away_players)

@router.post('/game-player/list', response={204: None})
def set_game_players(request: HttpRequest, game_id: int, data: GamePlayersIn):
    with transaction.atomic():
        for goalie_id in data.goalie_ids:
            GameGoalie.objects.create(game_id=game_id, goalie_id=goalie_id)
        for player_id in data.player_ids:
            GamePlayer.objects.create(game_id=game_id, player_id=player_id)
    return 204, None

@router.patch("/game-player/goalie/{game_goalie_id}", response={204: None})
def update_game_goalie(request: HttpRequest, game_goalie_id: int, data: PatchDict[GameGoalieIn]):
    goalie = get_object_or_404(GameGoalie, id=game_goalie_id)
    for attr, value in data.items():
        setattr(goalie, attr, value)
    goalie.save()
    return 204, None

@router.patch("/game-player/player/{game_player_id}", response={204: None})
def update_game_player(request: HttpRequest, game_player_id: int, data: PatchDict[GamePlayerIn]):
    player = get_object_or_404(GamePlayer, id=game_player_id)
    for attr, value in data.items():
        setattr(player, attr, value)
    player.save()
    return 204, None

# endregion

# region Game events

@router.get('/game-event-name/list', response=list[ObjectIdName])
def get_game_event_names(request: HttpRequest):
    game_event_names = GameEventName.objects.all()
    return game_event_names

@router.get('/game-event/list', response=list[GameEventOut])
def get_game_events(request: HttpRequest, game_id: int | None = None):
    game_events = GameEvents.objects.prefetch_related('players')
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
        if data.goalie_id is None and len(data.players) == 0:
            return 400, {"message": "Please specify goalie ID or player IDs."}
        # players = Player.objects.filter(id__in=data.players)
        data_new = data.dict()
        del data_new['players']
        previous_event = GameEvents.objects.filter(game_id=data.game_id).order_by('-number').first()
        data_new['number'] = (1 if previous_event is None else (previous_event.number + 1))
        with transaction.atomic():
            game_event = GameEvents.objects.create(**data_new)
            game_event.players.set(data.players)
            game_event.save()
    except IntegrityError as e:
        return resp.entry_already_exists("Game event", str(e))
    return {"id": game_event.id}

@router.patch("/game-event/{game_event_id}", response={204: None, 400: Message})
def update_game_event(request: HttpRequest, game_event_id: int, data: PatchDict[GameEventIn]):
    game_event = get_object_or_404(GameEvents, id=game_event_id)
    for attr, value in data.items():
        setattr(game_event, attr, value)
    if game_event.goalie is None and len(game_event.players) == 0:
        return 400, {"message": "Please specify goalie ID or player IDs."}
    game_event.save()
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
        game_event.delete()
    return 204, None

# endregion

# region FAKES

@router.get("/fake/teams")
def add_fake_teams(request):
    fake = Faker('en_US')
    fake.add_provider(faker.providers.address)
    fake.add_provider(AnimalsProvider)

    team_levels = [team_lvl.id for team_lvl in TeamLevel.objects.all()]
    team_divisions = [division.id for division in Division.objects.all()]

    birth_year_from = datetime.date(1970, 1, 1)
    birth_year_to = datetime.date(2015, 1, 1)

    # Team

    Team.objects.all().delete()

    for _ in range(10):
        fake_city = fake.city()

        team = Team(
            name=f"{fake_city} {fake.animal_name()}s",
            age_group=f"{fake.random_int(5, 22)}U",
            level_id=fake.random_element(team_levels),
            division_id=fake.random_element(team_divisions),
            city=fake_city
        )

        if settings.DEBUG:
            with open(os.path.join(settings.MEDIA_ROOT,
                                f"fakes/team{fake.random_int(1, 2)}.png"), "rb") as img_file:
                img_to_store = FileSaver(img_file)
                team.logo.save(f"{team.name}.png", img_to_store)
                team.save()
        else:
            with default_storage.open(f"fakes/team{fake.random_int(1, 2)}.png", "rb") as img_file:
                # img_to_store = FileSaver(img_file)
                team.logo.save(f"{team.name}.png", img_file)
                team.save()

    teams = [team.id for team in Team.objects.all()]
    positions = [pos.id for pos in PlayerPosition.objects.exclude(name__iexact="goalie")]

    # Goalie

    Goalie.objects.all().delete()

    goalie_position = (PlayerPosition.objects.filter(name__iexact="goalie"))[0].id

    for _ in range(20):
        goalie = Goalie.objects.create(
            team_id=fake.random_element(teams),
            position_id=goalie_position,
            height=fake.random_int(63, 82),
            weight=fake.random_int(154, 242),
            shoots=fake.random_element(['R', 'L']),
            jersey_number=fake.random_int(1, 50),
            first_name=fake.first_name_male(),
            last_name=fake.last_name_male(),
            birth_year=fake.date_between_dates(birth_year_from, birth_year_to),
            wins=fake.random_int(0, 100),
            losses=fake.random_int(0, 100)
        )

    # Player

    Player.objects.all().delete()

    for _ in range(100):
        player = Player.objects.create(
            team_id=fake.random_element(teams),
            position_id=fake.random_element(positions),
            height=fake.random_int(63, 82),
            weight=fake.random_int(154, 242),
            shoots=fake.random_element(['R', 'L']),
            number=fake.random_int(1, 50),
            first_name=fake.first_name_male(),
            last_name=fake.last_name_male(),
            birth_year=fake.date_between_dates(birth_year_from, birth_year_to),
            penalties_drawn=fake.random_int(0, 100),
            penalties_taken=fake.random_int(0, 100)
        )

    # Season, TeamSeason

    Season.objects.all().delete()
    TeamSeason.objects.all().delete()

    for year in [2020, 2021, 2022, 2023, 2024, 2025]:
        season = Season.objects.create(name=f"{year} / {year + 1}")
        for team_id in teams:
            games_played = fake.random_int(14, 15)
            ties = fake.random_int(0, int((games_played / 2)))
            wins = fake.random_int(0, ties)
            losses = games_played - wins
            TeamSeason.objects.create(
                team_id=team_id,
                season=season,
                games_played=games_played,
                goals_for=fake.random_int(0, 40),
                goals_against=fake.random_int(0, 40),
                wins=wins,
                losses=losses,
                ties=ties
            )

    # 


# endregion
