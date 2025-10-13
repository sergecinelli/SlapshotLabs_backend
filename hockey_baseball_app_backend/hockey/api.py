from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from ninja import File, Router, PatchDict
from ninja.files import UploadedFile
from django.contrib.auth import get_user_model
from django.http import HttpRequest, FileResponse
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
