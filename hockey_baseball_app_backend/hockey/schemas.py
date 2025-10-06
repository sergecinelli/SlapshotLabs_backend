import datetime
from typing import Optional
from ninja import Field, Schema

class ObjectId(Schema):
    id: int

class GoalieIn(Schema):
    team_id: int
    height: int = Field(..., description="Height in inches.")
    weight: int = Field(..., description="Weight in lbs.")
    shoots: int = Field(..., description="\"R\" - Right Shot, \"L\" - Left Shot.")
    jersey_number: int
    first_name: str
    last_name: str
    birth_year: int
    wins: int
    losses: int
    saves_above_avg: int

class GoalieOut(GoalieIn):
    id: int
    position_id: int = 1
    shots_on_goal: int
    saves: int
    goals_against: int
    games_played: int
    goals: int
    assists: int

    short_handed_goals: int = Field(0, description="SHG.")
    """SHG field."""
    
    power_play_goals: int = Field(0, description="PPG.")
    """PPG field."""

    shots_on_goal_per_game: float
    points: int

class PlayerIn(Schema):
    team_id: int
    position_id: int
    height: int = Field(..., description="Height in inches.")
    weight: int = Field(..., description="Weight in lbs.")
    shoots: int = Field(..., description="\"R\" - Right Shot, \"L\" - Left Shot.")
    number: int
    first_name: str
    last_name: str
    birth_year: int
    penalties_drawn: int
    penalties_taken: int

class PlayerOut(PlayerIn):
    id: int
    shots_on_goal: int
    games_played: int
    goals: int
    assists: int
    scoring_chances: int
    blocked_shots: int
    power_play_goals_diff: int
    penalty_kill_diff: int
    five_on_five_diff: int
    overall_diff: int
    shots_on_goal_per_game: float
    points: int
