import datetime
from typing import Any

from django.db import IntegrityError
from django.db.models.query import QuerySet

from hockey.models import CustomEvents, Game, GameEventName, GameEvents, GameGoalie, GamePlayer, Goalie, GoalieSeason, Highlight, HighlightReel, Player, PlayerPosition, PlayerSeason, Season, ShotType, Team
from hockey.schemas import GameDashboardGameOut, GameEventIn, GameGoalieOut, GameOut, GamePlayerOut, GoalieOut, HighlightIn, PlayerOut
from hockey.utils.constants import GOALIE_POSITION_NAME, NO_GOALIE_FIRST_NAME, NO_GOALIE_LAST_NAME, EventName, GoalType


def get_current_season(date: datetime.date | None = None) -> Season | None:
    """Get the current season based on the date. If no date is provided, use the current date."""
    if date is None:
        date = datetime.datetime.now(datetime.timezone.utc).date()
    seasons = Season.objects.filter(start_date__lte=date).exclude(start_date__gt=date).order_by('-start_date').first()
    return seasons

def get_game_current_goalies(game: Game) -> tuple[int, int]:
    goalie_change_event_name = GameEventName.objects.get(name=EventName.GOALIE_CHANGE)
    home_goalie = GameEvents.objects.filter(game=game, event_name=goalie_change_event_name, team=game.home_team).order_by('-period_id', 'time').first()
    if home_goalie is None:
        home_goalie = game.home_start_goalie
    away_goalie = GameEvents.objects.filter(game=game, event_name=goalie_change_event_name, team=game.away_team).order_by('-period_id', 'time').first()
    if away_goalie is None:
        away_goalie = game.away_start_goalie
    return (home_goalie.player_id, away_goalie.player_id)

# region No goalie

def is_no_goalie_object(player: Any) -> bool:
    return (player.first_name == NO_GOALIE_FIRST_NAME and player.last_name == NO_GOALIE_LAST_NAME)

def is_no_goalie_dict(player: dict[str, Any]) -> bool:
    return (player.get('first_name') == NO_GOALIE_FIRST_NAME and player.get('last_name') == NO_GOALIE_LAST_NAME)

def get_no_goalie(team_id: int) -> Goalie:
    """Gets or creates the default goalie to be used if no goalie in net."""
    no_goalie = Goalie.objects.filter(player__team_id=team_id, player__first_name=NO_GOALIE_FIRST_NAME, player__last_name=NO_GOALIE_LAST_NAME).first()
    if no_goalie is None:
        no_goalie_player = Player.objects.create(position=PlayerPosition.objects.get(name=GOALIE_POSITION_NAME),
            first_name=NO_GOALIE_FIRST_NAME, last_name=NO_GOALIE_LAST_NAME, team_id=team_id, number=100, height=60, weight=90, shoots='L',
            birth_year=datetime.date(2001, 1, 1), birthplace_country="Canada", address_country="Canada", address_region="Ontario",
            address_city="Ottawa", address_street=f"Team {team_id}", address_postal_code="111111", player_bio="Empty Net")
        no_goalie = Goalie.objects.create(player=no_goalie_player)
    return no_goalie

# endregion No goalie

# region Form outputs

def form_goalie_out(goalie: Goalie, season: Season) -> GoalieOut:
    goalie_season: GoalieSeason
    goalie_season, _ = GoalieSeason.objects.get_or_create(goalie=goalie, season=season)
    goalie_out = GoalieOut(
        id=goalie.player.id,
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
        number=goalie.player.number,
        team_id=goalie.player.team_id,
        analysis=goalie.player.analysis,
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
    player_out = PlayerOut(
        id=player.id,
        first_name=player.first_name,
        last_name=player.last_name,
        birth_year=player.birth_year,
        birthplace_country=player.birthplace_country,
        address_country=player.address_country,
        address_region=player.address_region,
        address_city=player.address_city,
        address_street=player.address_street,
        address_postal_code=player.address_postal_code,
        height=player.height,
        weight=player.weight,
        shoots=player.shoots,
        player_bio=player.player_bio,
        number=player.number,
        position_id=player.position_id,
        team_id=player.team_id,
        analysis=player.analysis,
        shots_on_goal=player_season.shots_on_goal,
        games_played=player_season.games_played,
        goals=player_season.goals,
        assists=player_season.assists,
        scoring_chances=player_season.scoring_chances,
        blocked_shots=player_season.blocked_shots,
        power_play_goals_diff=player_season.power_play_goals_diff,
        penalty_kill_diff=player_season.penalty_kill_diff,
        five_on_five_diff=player_season.five_on_five_diff,
        overall_diff=player_season.overall_diff,
        penalties_drawn=player_season.penalties_drawn,
        penalty_minutes=player_season.penalty_minutes,
        faceoff_win_percents=player_season.faceoff_win_percents,
        short_handed_goals=player_season.short_handed_goals,
        power_play_goals=player_season.power_play_goals,
        faceoffs=player_season.faceoffs,
        faceoffs_won=player_season.faceoffs_won,
        turnovers=player_season.turnovers,
        shots_on_goal_per_game=player_season.shots_on_goal_per_game,
        points=player_season.points
    )
    return player_out

def form_game_goalie_out(game_goalie: GameGoalie) -> GameGoalieOut:
    return GameGoalieOut(
        id=game_goalie.goalie_id,
        first_name=game_goalie.goalie.player.first_name,
        last_name=game_goalie.goalie.player.last_name,
        goals_against=game_goalie.goals_against,
        shots_against=game_goalie.shots_on_goal,
        saves=game_goalie.saves,
        save_percents=game_goalie.save_percents
    )

def form_game_player_out(game_player: GamePlayer) -> GamePlayerOut:
    return GamePlayerOut(
        id=game_player.player_id,
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

def form_game_dashboard_game_out(game: Game) -> GameDashboardGameOut:
    return GameDashboardGameOut(
        id=game.id,
        home_team_id=game.home_team_id,
        home_start_goalie_id=game.home_start_goalie_id,
        home_goals=game.home_goals,
        away_team_id=game.away_team_id,
        away_start_goalie_id=game.away_start_goalie_id,
        away_goals=game.away_goals,
        game_type_id=game.game_type_id,
        game_type_name=game.game_type_name_str,
        status=game.status,
        date=game.date,
        time=game.time,
        season_id=game.season_id,
        arena_id=game.arena_id,
        rink_id=game.rink_id,
        game_period_id=game.game_period_id,
    )

# endregion Form outputs

# region Game events updates

def update_game_shots_from_event(game: Game, data: GameEventIn | None = None, event: GameEvents | None = None, is_deleted: bool = False) -> str | None:
    if data is not None:
        shot_type = ShotType.objects.get(id=data.shot_type_id) if data.shot_type_id is not None else None
        goal_type = data.goal_type
    else:
        shot_type = event.shot_type
        goal_type = event.goal_type

    if shot_type is None:
        return "Shot type ID is required"

    shot_type_name = shot_type.name.lower()
    shot_team = Team.objects.get(id=(data.team_id if data is not None else event.team_id))

    if shot_team is None or shot_team != game.home_team and shot_team != game.away_team:
        return "Invalid team"

    if ((data is not None and data.is_scoring_chance is None) or (event is not None and event.is_scoring_chance is None)):
        return "Is scoring chance field is required for shot events"

    if shot_type_name != "goal" and goal_type is not None:
        return "Goal type is only allowed for goal events"

    if shot_type_name == "goal" and goal_type is None:
        goal_type = GoalType.EVEN_STRENGTH

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
    faceoff_team = Team.objects.get(id=(data.team_id if data is not None else event.team_id))
    if faceoff_team is None or (faceoff_team != game.home_team and faceoff_team != game.away_team):
        return "Invalid team"

    value_to_add = (1 if not is_deleted else -1)

    if faceoff_team == game.home_team:
        game.home_faceoffs_won_count += value_to_add

    game.faceoffs_count += value_to_add

    game.save()
    return None

# endregion Game events updates

# region Create complex items

def create_highlight(data: HighlightIn, highlight_reel: HighlightReel, user_id: int) -> Highlight:
    if data.order is None:
        raise ValueError("Order is required for highlights.")
    if data.game_event_id is None:
        if data.event_name is None or data.note is None:
            raise ValueError("Event name and note are required for custom events.")
        game_event_id = None
        custom_event = CustomEvents.objects.create(event_name=data.event_name, note=data.note, youtube_link=data.youtube_link,
                                                   date=data.date, time=data.time, user_id=user_id)
    else:
        if data.event_name is not None or data.note is not None or data.youtube_link is not None or data.date is not None or data.time is not None:
            raise ValueError("If game event ID is provided, none of the other fields except order should be provided.")
        game_event_id = data.game_event_id
        custom_event = None
    highlight = Highlight(game_event_id=game_event_id, custom_event=custom_event, highlight_reel_id=highlight_reel.id, order=data.order, user_id=user_id)
    highlight.full_clean()
    highlight.save()
    return highlight

# endregion Create complex items
