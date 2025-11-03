import datetime

from django.db import IntegrityError

from hockey.models import Game, GameEvents, GameGoalie, GamePlayer, Goalie, GoalieSeason, Player, PlayerSeason, Season, ShotType, Team
from hockey.schemas import GameEventIn, GameGoalieOut, GamePlayerOut, GoalieOut, PlayerOut


def get_current_season(date: datetime.date | None = None) -> Season | None:
    """Get the current season based on the date. If no date is provided, use the current date."""
    if date is None:
        date = datetime.datetime.now(datetime.timezone.utc).date()
    seasons = Season.objects.filter(start_date__lte=date).exclude(start_date__gt=date).order_by('-start_date').first()
    return seasons

def get_no_goalie() -> Goalie:
    """Gets the default goalie to be used if no goalie in net."""
    no_goalie, _ = Goalie.objects.get_or_create(first_name="No Goalie")
    return no_goalie

def get_game_current_goalies(game: Game) -> tuple[int, int]:
    home_goalie = GameGoalie.objects.filter(game=game, goalie__team=game.home_team).order_by('-start_period_id', '-start_time').first()
    away_goalie = GameGoalie.objects.filter(game=game, goalie__team=game.away_team).order_by('-start_period_id', '-start_time').first()
    return (home_goalie.goalie_id, away_goalie.goalie_id)

# region Form outputs

def form_goalie_out(goalie: Goalie, season: Season) -> GoalieOut:
    goalie_season: GoalieSeason
    goalie_season, _ = GoalieSeason.objects.get_or_create(goalie=goalie, season=season)
    goalie_out = GoalieOut(
        id=goalie.id,
        first_name=goalie.player.first_name,
        last_name=goalie.player.last_name,
        birth_year=goalie.player.birth_year,
        player_bio=goalie.player.player_bio,
        birthplace_country=goalie.player.birthplace_country,
        address_country=goalie.player.address_country,
        address_region=goalie.player.address_region,
        address_city=goalie.player.address_city,
        address_street=goalie.player.address_street,
        address_postal_code=goalie.player.address_postal_code,
        height=goalie.player.height,
        weight=goalie.player.weight,
        shoots=goalie.player.shoots,
        jersey_number=goalie.player.number,
        shots_on_goal = goalie_season.shots_on_goal,
        saves = goalie_season.saves,
        goals_against = goalie_season.goals_against,
        games_played = goalie_season.games_played,
        wins = goalie_season.wins,
        losses = goalie_season.losses,
        goals = goalie_season.goals,
        assists = goalie_season.assists,
        penalty_minutes = goalie_season.penalty_minutes,
        save_percents = goalie_season.save_percents,
        short_handed_goals_against = goalie_season.short_handed_goals_against,
        power_play_goals_against = goalie_season.power_play_goals_against,
        shots_on_goal_per_game = goalie_season.shots_on_goal_per_game,
        points = goalie_season.points
    )
    return goalie_out

def form_player_out(player: Player, season: Season) -> PlayerOut:
    player_season: PlayerSeason
    player_season, _ = PlayerSeason.objects.get_or_create(player=player, season=season)
    player_out = PlayerOut.from_orm(player)
    player_out.shots_on_goal = player_season.shots_on_goal
    player_out.games_played = player_season.games_played
    player_out.goals = player_season.goals
    player_out.assists = player_season.assists
    player_out.scoring_chances = player_season.scoring_chances
    player_out.blocked_shots = player_season.blocked_shots
    player_out.power_play_goals_diff = player_season.power_play_goals_diff
    player_out.penalty_kill_diff = player_season.penalty_kill_diff
    player_out.five_on_five_diff = player_season.five_on_five_diff
    player_out.overall_diff = player_season.overall_diff
    player_out.penalties_drawn = player_season.penalties_drawn
    player_out.penalty_minutes = player_season.penalty_minutes
    player_out.faceoff_win_percents = player_season.faceoff_win_percents
    player_out.short_handed_goals = player_season.short_handed_goals
    player_out.power_play_goals = player_season.power_play_goals
    player_out.faceoffs = player_season.faceoffs
    player_out.faceoffs_won = player_season.faceoffs_won
    player_out.turnovers = player_season.turnovers
    player_out.shots_on_goal_per_game = player_season.shots_on_goal_per_game
    player_out.points = player_season.points
    return player_out

def form_game_goalie_out(game_goalie: GameGoalie) -> GameGoalieOut:
    return GameGoalieOut(
        id=game_goalie.id,
        first_name=game_goalie.goalie.first_name,
        last_name=game_goalie.goalie.last_name,
        goals_against=game_goalie.goals_against,
        shots_against=game_goalie.shots_against,
        saves=game_goalie.saves,
        save_percents=game_goalie.save_percents
    )

def form_game_player_out(game_player: GamePlayer) -> GamePlayerOut:
    return GamePlayerOut(
        id=game_player.id,
        first_name=game_player.player.first_name,
        last_name=game_player.player.last_name,
        goals=game_player.goals,
        assists=game_player.assists,
        shots_on_goal=game_player.shots_on_goal,
        scoring_chances=game_player.scoring_chances,
        penalty_minutes=game_player.penalty_minutes,
        turnovers=game_player.turnovers,
        faceoffs=game_player.faceoffs,
        points=game_player.points
    )

# endregion Form outputs

# region Game events updates

def update_game_shots_from_event(game: Game, data: GameEventIn | None = None, event: GameEvents | None = None, is_deleted: bool = False) -> str | None:
    if data is not None:
        shot_type = ShotType.objects.get(id=data.shot_type_id) if data.shot_type_id is not None else None
    else:
        shot_type = event.shot_type

    if shot_type is None:
        return "Shot type ID is required"

    shot_type_name = shot_type.name.lower()
    shot_team = Team.objects.get(id=(data.team_id if data is not None else event.team_id))

    if shot_team is None or shot_team != game.home_team and shot_team != game.away_team:
        return "Invalid team"

    if ((data is not None and data.is_scoring_chance is None) or (event is not None and event.is_scoring_chance is None)):
        return "Is scoring chance field is required for shot events"

    value_to_add = (1 if not is_deleted else -1)

    if shot_type_name is not None:
        if shot_team == game.home_team:
            game.home_shots.shots_on_goal += value_to_add
        else:
            game.away_shots.shots_on_goal += value_to_add

    if ((data is not None and data.is_scoring_chance) or (event is not None and event.is_scoring_chance)):
        if shot_team == game.home_team:
            game.home_shots.scoring_chance += value_to_add
        else:
            game.away_shots.scoring_chance += value_to_add

    if shot_type_name == "goal":
        if shot_team == game.home_team:
            game.home_goals += value_to_add
        else:
            game.away_goals += value_to_add
    elif shot_type_name == "save":
        if shot_team == game.home_team:
            game.home_shots.saves += value_to_add
        else:
            game.away_shots.saves += value_to_add
    elif shot_type_name == "missed the net":
        if shot_team == game.home_team:
            game.home_shots.missed_net += value_to_add
        else:
            game.away_shots.missed_net += value_to_add
    elif shot_type_name == "blocked":
        if shot_team == game.home_team:
            game.home_shots.blocked += value_to_add
        else:
            game.away_shots.blocked += value_to_add
    else:
        return "Invalid shot type"

    game.home_shots.save()
    game.away_shots.save()
    game.save()
    return None

def update_game_turnovers_from_event(game: Game, data: GameEventIn | None = None, event: GameEvents | None = None, is_deleted: bool = False) -> str | None:
    if data is not None:
        zone = data.zone
    else:
        zone = event.zone

    if zone is None:
        return "Zone is required"

    zone_team = Team.objects.get(id=(data.team_id if data is not None else event.team_id))
    if zone_team is None or zone_team != game.home_team and zone_team != game.away_team:
        return "Invalid team"

    value_to_add = (1 if not is_deleted else -1)

    zone = zone.lower()
    if zone == "attacking":
        if zone_team == game.home_team:
            game.home_turnovers.off_zone += value_to_add
        else:
            game.away_turnovers.off_zone += value_to_add
    elif zone == "neutral":
        if zone_team == game.home_team:
            game.home_turnovers.neutral_zone += value_to_add
        else:
            game.away_turnovers.neutral_zone += value_to_add
    elif zone == "defending":
        if zone_team == game.home_team:
            game.home_turnovers.def_zone += value_to_add
        else:
            game.away_turnovers.def_zone += value_to_add
    else:
        return "Invalid zone"

    game.home_turnovers.save()
    game.away_turnovers.save()
    game.save()
    return None

def update_game_faceoffs_from_event(game: Game, data: GameEventIn | None = None, event: GameEvents | None = None, is_deleted: bool = False) -> str | None:
    if data is not None:
        is_faceoff_won = data.is_faceoff_won
    else:
        is_faceoff_won = event.is_faceoff_won

    if is_faceoff_won is None:
        return "Is faceoff won field is required"

    faceoff_team = Team.objects.get(id=(data.team_id if data is not None else event.team_id))
    if faceoff_team is None or faceoff_team != game.home_team and faceoff_team != game.away_team:
        return "Invalid team"

    value_to_add = (1 if not is_deleted else -1)

    if ((is_faceoff_won and faceoff_team == game.home_team) or (not is_faceoff_won and faceoff_team == game.away_team)):
        game.home_faceoffs_won_count += value_to_add

    game.faceoffs_count += value_to_add

    game.save()
    return None

def update_game_goalie_from_event(data: GameEventIn | None = None, event: GameEvents | None = None, is_deleted: bool = False) -> str | None:
    if data is not None:
        game_id = data.game_id
        goalie_id = data.goalie_id
        start_period_id = data.period_id
        start_time = data.time
    else:
        game_id = event.game_id
        goalie_id = event.goalie_id
        start_period_id = event.period_id
        start_time = event.time

    if start_time is None:
        return "Start time is required"
    
    if start_period_id is None:
        return "Start period is required"
    
    if goalie_id is None:
        return "Goalie ID is required"

    if is_deleted:
        GameGoalie.objects.filter(game_id=game_id, goalie_id=goalie_id, start_period_id=start_period_id, start_time=start_time).delete()
    else:
        GameGoalie.objects.create(game_id=game_id, goalie_id=goalie_id, start_period_id=start_period_id, start_time=start_time)

    return None
    
# endregion Game events updates