import json
from hockey.models import Game, GameEvents


def game_to_dict(game: Game) -> dict:
    return {
        "type": "game",
        "id": game.id,
        "home_team_id": game.home_team_id,
        "away_team_id": game.away_team_id,
        "home_start_goalie_id": game.home_start_goalie_id,
        "away_start_goalie_id": game.away_start_goalie_id,
        "home_goals": game.home_goals,
        "away_goals": game.away_goals,
        "home_goalies": [goalie.player_id for goalie in game.home_goalies.all()],
        "away_goalies": [goalie.player_id for goalie in game.away_goalies.all()],
        "home_players": [player.id for player in game.home_players.all()],
        "away_players": [player.id for player in game.away_players.all()],
        "season_id": game.season_id,
        "events": [game_event_to_dict(event) for event in game.gameevents_set.order_by("period__order", "-time").all()],
    }

def game_event_to_dict(game_event: GameEvents) -> dict:
    return {
        "type": "game_event",
        "id": game_event.id,
        "game_id": game_event.game_id,
        "game_season_id": game_event.game.season_id,
        "event_name": game_event.event_name.name.lower(),
        "time": (game_event.time.strftime('%H:%M:%S') if game_event.time else None),
        "period": game_event.period.order,
        "team_id": game_event.team_id,
        "team_2_id": (game_event.game.away_team_id if game_event.team_id == game_event.game.home_team_id else game_event.game.home_team_id),
        "player_id": (game_event.player_id if game_event.player else None),
        "player_2_id": (game_event.player_2_id if game_event.player_2 else None),
        "goalie_id": (game_event.goalie_id if game_event.goalie else None),
        "shot_type": (game_event.shot_type.name.lower() if game_event.shot_type else None),
        "goal_type": game_event.goal_type,
        "zone": game_event.zone,
        "time_length": (game_event.time_length.total_seconds() if game_event.time_length else None),
        "is_scoring_chance": game_event.is_scoring_chance,
    }

def serialize_game(game: Game) -> str:
    return json.dumps(game_to_dict(game))

def serialize_game_event(game_event: GameEvents) -> str:
    return json.dumps(game_event_to_dict(game_event))
