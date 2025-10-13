import datetime
import os
from django.conf import settings
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from ninja import File, Router, PatchDict
from ninja.files import UploadedFile
from django.contrib.auth import get_user_model
from django.http import HttpRequest, FileResponse
from django.core.files import File as FileSaver
from faker import Faker
import faker.providers
from faker_animals import AnimalsProvider
from .schemas import (DivisionOut, Message, ObjectId, PlayerPositionOut, GoalieIn, GoalieOut, PlayerIn, PlayerUpdate, PlayerOut, SeasonIn, SeasonOut,
                      TeamIn, TeamLevelOut, TeamOut, TeamSeasonIn, TeamSeasonOut)
from .models import Division, Goalie, Player, PlayerPosition, Season, Team, TeamLevel, TeamSeason
from .utils import api_response_templates as resp

router = Router(tags=["Hockey"])

# region Goalie, player

@router.get('/player-position/list', response=list[PlayerPositionOut])
def get_player_positions(request: HttpRequest):
    positions = PlayerPosition.objects.all()
    return positions

@router.get('/goalie/list', response=list[GoalieOut])
def get_goalies(request: HttpRequest):
    goalies = Goalie.objects.all()
    return goalies

@router.get('/goalie/{goalie_id}', response=GoalieOut)
def get_goalie(request: HttpRequest, goalie_id: int):
    goalie = get_object_or_404(Goalie, id=goalie_id)
    return goalie

@router.post('/goalie', response={200: ObjectId, 400: Message, 503: Message})
def add_goalie(request: HttpRequest, data: GoalieIn):
    goalie_position = PlayerPosition.objects.filter(name__iexact="goalie")
    if len(goalie_position) == 0:
        return 503, {'message': "Can't reconcile dependencies. Please try again later."}
    position_id = goalie_position[0].id
    try:
        goalie = Goalie.objects.create(position_id=position_id, **data.dict())
    except IntegrityError as e:
        return resp.entry_already_exists("Goalie", str(e))
    return {"id": goalie.id}

@router.put("/goalie/{goalie_id}", response={204: None})
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
def get_players(request: HttpRequest):
    players = Player.objects.all()
    return players

@router.get('/player/{player_id}', response=PlayerOut)
def get_player(request: HttpRequest, player_id: int):
    player = get_object_or_404(Player, id=player_id)
    return player

@router.post('/player', response={200: ObjectId, 400: Message})
def add_player(request: HttpRequest, data: PlayerIn):
    try:
        player = Player.objects.create(**data)
    except IntegrityError as e:
        return resp.entry_already_exists("Player", str(e))
    return {"id": player.id}

@router.put("/player/{player_id}", response={204: None})
def update_player(request: HttpRequest, player_id: int, data: PatchDict[PlayerUpdate]):
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

@router.get('/division/list', response=list[DivisionOut])
def get_divisions(request: HttpRequest):
    divisions = Division.objects.all()
    return divisions

@router.get('/team-level/list', response=list[TeamLevelOut])
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

@router.put("/team/{team_id}", response={204: None})
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

@router.put("/season/{season_id}", response={204: None})
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

@router.put("/team-season/{team_season_id}", response={204: None})
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

        with open(os.path.join(settings.MEDIA_ROOT,
                               f"fakes/team{fake.random_int(1, 2)}.png"), "rb") as img_file:
            img_to_store = FileSaver(img_file)
            team.logo.save(f"{team.name}.png", img_to_store)
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
