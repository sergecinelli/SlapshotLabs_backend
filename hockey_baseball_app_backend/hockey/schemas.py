import datetime
from typing import Optional
from ninja import Field, Schema

# region Common

class Message(Schema):
    message: str
    details: str | None = None

class ObjectId(Schema):
    id: int

class ObjectIdName(ObjectId):
    name: str

# endregion

# region Goalie, player

class PlayerPositionOut(Schema):
    id: int
    name: str

class GoalieIn(Schema):
    team_id: int | None = None
    height: int = Field(..., description="Height in inches.")
    weight: int = Field(..., description="Weight in lbs.")
    shoots: str = Field(..., description="\"R\" - Right Shot, \"L\" - Left Shot.")
    jersey_number: int
    first_name: str
    last_name: str
    birth_year: datetime.date
    player_bio: str | None = None
    birthplace_country: str
    address_country: str
    address_region: str
    address_city: str
    address_street: str
    address_postal_code: str
    wins: int | None = None
    losses: int | None = None
    analysis: str | None = None

class GoalieOut(GoalieIn):
    id: int
    shots_on_goal: int
    saves: int
    goals_against: int
    games_played: int
    goals: int
    assists: int
    penalty_minutes: datetime.timedelta

    save_percents: int = Field(0, description="Save %.")
    """Save % field."""

    short_handed_goals_against: int = Field(0, description="SHGA.")
    """SHGA field."""
    
    power_play_goals_against: int = Field(0, description="PPGA.")
    """PPGA field."""

    shots_on_goal_per_game: float
    points: int

class GoalieSeasonsGet(Schema):
    goalie_id: int
    season_ids: list[int]

class GoalieSeasonOut(Schema):
    goalie_id: int
    season_id: int

    shots_on_goal: int
    saves: int
    goals_against: int
    games_played: int
    wins: int
    losses: int
    goals: int
    assists: int
    penalty_minutes: datetime.timedelta

    save_percents: int = Field(0, description="Save %.")
    """Save % field."""

    short_handed_goals_against: int = Field(0, description="SHGA.")
    """SHGA field."""
    
    power_play_goals_against: int = Field(0, description="PPGA.")
    """PPGA field."""

    shots_on_goal_per_game: float
    points: int

class PlayerIn(Schema):
    team_id: int | None = None
    position_id: int
    height: int = Field(..., description="Height in inches.")
    weight: int = Field(..., description="Weight in lbs.")
    shoots: str = Field(..., description="\"R\" - Right Shot, \"L\" - Left Shot.")
    number: int
    first_name: str
    last_name: str
    birth_year: datetime.date
    player_bio: str | None = None
    birthplace_country: str
    address_country: str
    address_region: str
    address_city: str
    address_street: str
    address_postal_code: str
    analysis: str | None = None

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
    penalties_drawn: datetime.timedelta
    penalty_minutes: datetime.timedelta
    faceoffs: int
    faceoffs_won: int
    turnovers: int

    faceoff_win_percents: int = Field(0, description="Faceoff Win %.")
    """Faceoff Win % field."""

    short_handed_goals: int = Field(0, description="SHG.")
    """SHG field."""
    
    power_play_goals: int = Field(0, description="PPG.")
    """PPG field."""

    shots_on_goal_per_game: float
    points: int

class PlayerSeasonsGet(Schema):
    player_id: int
    season_ids: list[int]

class PlayerSeasonOut(Schema):
    player_id: int
    season_id: int

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
    penalties_drawn: datetime.timedelta
    penalty_minutes: datetime.timedelta

    faceoff_win_percents: int = Field(0, description="Faceoff Win %.")
    """Faceoff Win % field."""

    short_handed_goals: int = Field(0, description="SHG.")
    """SHG field."""
    
    power_play_goals: int = Field(0, description="PPG.")
    """PPG field."""

    faceoffs: int
    faceoffs_won: int
    turnovers: int
    shots_on_goal_per_game: float
    points: int

# endregion

# region Team, season, division, level

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

# region Game

class ArenaIn(Schema):
    name: str
    address: str

class ArenaOut(ArenaIn):
    id: int

class ArenaRinkIn(Schema):
    name: str
    arena_id: int

class ArenaRinkOut(ArenaRinkIn):
    id: int

class DefensiveZoneExitIn(Schema):
    icing: int
    skate_out: int
    so_win: int = Field(..., description="SO & Win")
    so_lose: int = Field(..., description="SO & Lose")
    passes: int = Field(..., description="Pass")

class DefensiveZoneExitOut(DefensiveZoneExitIn):
    id: int

class OffensiveZoneEntryIn(Schema):
    pass_in: int = Field(..., description="Pass")
    dump_win: int = Field(..., description="Dump/W")
    dump_lose: int = Field(..., description="Dump/L")
    skate_in: int

class OffensiveZoneEntryOut(OffensiveZoneEntryIn):
    id: int

class ShotsIn(Schema):
    shots_on_goal: int
    saves: int
    missed_net: int
    scoring_chance: bool
    blocked: int

class ShotsOut(ShotsIn):
    id: int
    scoring_chance: int

class TurnoversIn(Schema):
    off_zone: int
    neutral_zone: int
    def_zone: int

class TurnoversOut(TurnoversIn):
    id: int

class GameIn(Schema):
    home_team_id: int
    home_goals: int | None = None
    home_team_goalie_id: int | None = None
    away_team_id: int
    away_goals: int | None = None
    away_team_goalie_id: int | None = None
    game_type_id: int
    tournament_name: str | None = None
    status: int = Field(..., description="1 - Not Started, 2 - Game in Progress, 3 - Game Over")
    date: datetime.date
    time: datetime.time
    rink_id: int

    game_period_id: int | None = None
    game_type_group: str

    home_faceoff_win: int = 0

    away_faceoff_win: int = 0

class GameOut(GameIn):
    id: int

    home_defensive_zone_exit_id: int | None = None
    home_offensive_zone_entry_id: int | None = None
    home_shots_id: int | None = None
    home_turnovers_id: int | None = None

    away_defensive_zone_exit_id: int | None = None
    away_offensive_zone_entry_id: int | None = None
    away_shots_id: int | None = None
    away_turnovers_id: int | None = None

class GameDashboardOut(Schema):
    upcoming_games: list[GameOut]
    previous_games: list[GameOut]

class GameGoalieOut(Schema):
    id: int
    first_name: str
    last_name: str
    goals_against: int
    shots_against: int
    saves: int
    save_percents: int

class GamePlayerOut(Schema):
    id: int
    first_name: str
    last_name: str
    goals: int
    assists: int
    shots_on_goal: int
    scoring_chances: int
    penalty_minutes: datetime.timedelta
    turnovers: int
    faceoffs: int
    points: int

class GamePlayersIn(Schema):
    goalie_ids: list[int]
    player_ids: list[int]

class GamePlayersOut(Schema):
    home_goalies: list[GameGoalieOut]
    home_players: list[GamePlayerOut]
    away_goalies: list[GameGoalieOut]
    away_players: list[GamePlayerOut]

# endregion

# region Event

class GameEventIn(Schema):
    game_id: int
    # number: int   # Calculated automatically.
    event_name_id: int
    time: datetime.time
    period_id: int
    team_id: int
    player_id: int | None = None
    player_2_id: int | None = None
    goalie_id: int | None = None

    # Shot specific fields.
    shot_type_id: int | None = None
    is_scoring_chance: bool | None = None

    # Spray chart points.
    ice_top_offset: int | None = None
    ice_left_offset: int | None = None
    net_top_offset: int | None = None
    net_left_offset: int | None = None

    note: str | None = None
    time_length: datetime.timedelta | None = None

    youtube_link: str | None = None

    class Config(Schema.Config):
        json_encoders = {
            datetime.timedelta: lambda v: f"{v.total_seconds() // 60}:{v.total_seconds() % 60}"
        }

class GameEventOut(GameEventIn):
    id: int
    number: int

    @staticmethod
    def resolve_players(obj):
        players_list = []
        for player in obj.players.all():
            players_list.append(player.id)
        return players_list

# endregion
