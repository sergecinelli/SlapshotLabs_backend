import datetime

from django.db import IntegrityError

from hockey.models import GameGoalie, GamePlayer, Goalie, GoalieSeason, Player, PlayerSeason, Season
from hockey.schemas import GameGoalieOut, GamePlayerOut, GoalieOut, PlayerOut


def get_current_season() -> Season | None:
    seasons = Season.objects.filter(start_date__lte=datetime.datetime.now(datetime.timezone.utc).date()).\
        exclude(start_date__gt=datetime.datetime.now(datetime.timezone.utc).date()).order_by('-start_date').first()
    return seasons

def form_goalie_out(goalie: Goalie, season: Season) -> GoalieOut:
    goalie_season: GoalieSeason
    goalie_season, _ = GoalieSeason.objects.get_or_create(goalie=goalie, season=season)
    goalie_out = GoalieOut.from_orm(goalie)
    goalie_out.shots_on_goal = goalie_season.shots_on_goal
    goalie_out.saves = goalie_season.saves
    goalie_out.goals_against = goalie_season.goals_against
    goalie_out.games_played = goalie_season.games_played
    goalie_out.wins = goalie_season.wins
    goalie_out.losses = goalie_season.losses
    goalie_out.goals = goalie_season.goals
    goalie_out.assists = goalie_season.assists
    goalie_out.penalty_minutes = goalie_season.penalty_minutes
    goalie_out.save_percents = goalie_season.save_percents
    goalie_out.short_handed_goals_against = goalie_season.short_handed_goals_against
    goalie_out.power_play_goals_against = goalie_season.power_play_goals_against
    goalie_out.shots_on_goal_per_game = goalie_season.shots_on_goal_per_game
    goalie_out.points = goalie_season.points
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
