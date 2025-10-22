import datetime

from django.db import IntegrityError

from hockey.models import Goalie, GoalieSeason, Player, PlayerSeason, Season
from hockey.schemas import GoalieOut, PlayerOut


def get_current_season() -> Season | None:
    if datetime.datetime.now(datetime.timezone.utc).month < 10:
        seasons = Season.objects.filter(name__startswith=f'{datetime.datetime.now(datetime.timezone.utc).year - 1}')
    else:
        seasons = Season.objects.filter(name__startswith=f'{datetime.datetime.now(datetime.timezone.utc).year}')

    if len(seasons) == 0:
        if datetime.datetime.now(datetime.timezone.utc).month < 10:
            season = Season.objects.create(name=f'{datetime.datetime.now(datetime.timezone.utc).year - 1} / {datetime.datetime.now(datetime.timezone.utc).year}')
        else:
            season = Season.objects.create(name=f'{datetime.datetime.now(datetime.timezone.utc).year} / {datetime.datetime.now(datetime.timezone.utc).year + 1}')
        return season

    return seasons[0]

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