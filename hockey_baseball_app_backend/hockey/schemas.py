import datetime
from typing import Optional
from ninja import Field, Schema

class Message(Schema):
    message: str

class ObjectId(Schema):
    id: int

# region Goalie, player

class PlayerPositionOut(Schema):
    id: int
    name: str

class GoalieIn(Schema):
    team_id: int
    height: int = Field(..., description="Height in inches.")
    weight: int = Field(..., description="Weight in lbs.")
    shoots: str = Field(..., description="\"R\" - Right Shot, \"L\" - Left Shot.")
    jersey_number: int
    first_name: str
    last_name: str
    birth_year: datetime.date
    wins: int
    losses: int
    saves_above_avg: int

class GoalieOut(GoalieIn):
    id: int
    position_id: int
    shots_on_goal: int
    saves: int
    goals_against: int
    games_played: int
    goals: int
    assists: int

    short_handed_goals_against: int = Field(0, description="SHGA.")
    """SHG field."""
    
    power_play_goals_against: int = Field(0, description="PPGA.")
    """PPG field."""

    shots_on_goal_per_game: float
    points: int

class PlayerIn(Schema):
    team_id: int
    position_id: int
    height: int = Field(..., description="Height in inches.")
    weight: int = Field(..., description="Weight in lbs.")
    shoots: str = Field(..., description="\"R\" - Right Shot, \"L\" - Left Shot.")
    number: int
    first_name: str
    last_name: str
    birth_year: datetime.date
    penalties_drawn: int
    penalties_taken: int

class PlayerUpdate(PlayerIn):
    class Meta:
        fields_optional = "__all__"

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

# endregion

# region Team, season, division, level

class DivisionOut(Schema):
    id: int
    name: str

class TeamLevelOut(Schema):
    id: int
    name: str

class SeasonIn(Schema):
    name: str

class SeasonOut(SeasonIn):
    id: int

class TeamIn(Schema):
    age_group: str
    level_id: int
    division_id: int
    name: str
    city: str

class TeamOut(TeamIn):
    id: int

class TeamSeasonIn(Schema):
    team_id: int
    season_id: int
    games_played: int
    goals_against: int
    wins: int
    losses: int
    ties: int

class TeamSeasonOut(TeamSeasonIn):
    id: int

# endregion
