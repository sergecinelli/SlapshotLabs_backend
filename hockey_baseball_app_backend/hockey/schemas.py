import datetime
from typing import Optional
from ninja import Field, Schema

from hockey.models import Game
from hockey.utils.constants import GameStatus, GoalType, RinkZone, get_constant_class_int_description, get_constant_class_str_description

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
    number: int = Field(...)
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

class GoalieOut(GoalieIn):
    id: int = Field(...)
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
    wins: int
    losses: int
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

class GameTypeOut(Schema):
    id: int
    name: str
    game_type_names: list[ObjectIdName] = Field(..., description="List of game type names for the game type.")

class GamePeriodOut(Schema):
    id: int
    name: str
    order: int

class GameIn(Schema):
    home_team_id: int
    home_start_goalie_id: int | None = Field(None, alias="home_team_goalie_id", description="ID of the goalie that started the game for the home team.")
    away_team_id: int
    away_start_goalie_id: int | None = Field(None, alias="away_team_goalie_id", description="ID of the goalie that started the game for the away team.")
    game_type_id: int
    game_type_name_id: int | None = None
    status: int = Field(..., description=get_constant_class_int_description(GameStatus))
    date: datetime.date
    time: datetime.time
    rink_id: int

    home_goalies: list[int]
    away_goalies: list[int]
    home_players: list[int]
    away_players: list[int]

    game_period_id: int | None = None

class GameOut(Schema):
    id: int
    home_team_id: int
    home_start_goalie_id: int | None
    home_goals: int
    away_team_id: int
    away_start_goalie_id: int | None
    away_goals: int
    game_type_id: int
    game_type_name: str | None = Field(None, alias="game_type_name_str")
    status: int = Field(..., description=get_constant_class_int_description(GameStatus))
    date: datetime.date
    time: datetime.time
    season_id: int | None = None
    arena_id: int | None = None
    rink_id: int | None = None

    game_period_id: int | None = None

class GameTypeRecordOut(Schema):
    wins: int
    losses: int
    ties: int

class GameExtendedOut(GameOut):
    game_type_name: str | None = None
    arena_id: int
    home_team_game_type_record: GameTypeRecordOut | None = None
    away_team_game_type_record: GameTypeRecordOut | None = None

class GameDashboardGameOut(GameOut):
    game_type_name: str | None

class GameDashboardOut(Schema):
    upcoming_games: list[GameDashboardGameOut]
    previous_games: list[GameDashboardGameOut]

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

    # Shot -> goal specific fields.
    goal_type: str | None = Field(None, description=get_constant_class_str_description(GoalType))

    # Turnover specific fields.
    zone: str | None = Field(None, description=get_constant_class_str_description(RinkZone))

    note: str | None = None
    time_length: datetime.timedelta | None = None

    youtube_link: str | None = None

class GameEventOut(GameEventIn):
    id: int

class GameLiveDataOut(Schema):
    game_period_id: int | None
    home_goalie_id: int | None
    away_goalie_id: int | None
    home_goals: int
    away_goals: int
    home_faceoff_win: int
    away_faceoff_win: int
    home_defensive_zone_exit: DefensiveZoneExitOut
    away_defensive_zone_exit: DefensiveZoneExitOut
    home_offensive_zone_entry: OffensiveZoneEntryOut
    away_offensive_zone_entry: OffensiveZoneEntryOut
    home_shots: ShotsOut
    away_shots: ShotsOut
    home_turnovers: TurnoversOut
    away_turnovers: TurnoversOut
    events: list[GameEventOut]

# endregion

# region Highlight Reels

class HighlightReelIn(Schema):
    name: str
    description: str
    game_events: list[int]

class HighlightReelListOut(Schema):
    id: int
    name: str
    description: str
    created_by: str
    date: datetime.date

class HighlightReelOut(HighlightReelListOut):
    game_events: list[GameEventOut]

# endregion