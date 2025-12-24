import datetime
from types import SimpleNamespace
from typing import Any, Optional
from ninja import Field, Schema

from hockey.models import Game, Highlight, TeamSeason
from hockey.utils.constants import EventName, GameStatus, GoalType, HighlightVisibility, RinkZone, get_constant_class_int_description, get_constant_class_str_description
from hockey.utils.formulas import get_team_points

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
    ties: int
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

class GoalieTeamSeasonOut(GoalieSeasonOut):
    team_id: int

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

class PlayerTeamSeasonOut(PlayerSeasonOut):
    team_id: int

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
    abbreviation: str | None = None
    city: str

class TeamOut(TeamIn):
    id: int
    level_name: str
    division_name: str
    games_played: int
    goals_for: int
    goals_against: int
    wins: int
    losses: int
    ties: int
    points: int

class TeamSeasonOut(Schema):
    id: int
    team_id: int
    season_id: int
    games_played: int
    goals_for: int
    goals_against: int
    wins: int
    losses: int
    ties: int
    points: int

    @staticmethod
    def resolve_points(obj: TeamSeason) -> int:
        return get_team_points(obj)

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

class ArenaRinkExtendedOut(ArenaRinkOut):
    id: int
    arena_name: str
    arena_address: str

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
    analysis: str | None = None

    home_goalies: list[int]
    away_goalies: list[int]
    home_players: list[int]
    away_players: list[int]

    game_period_id: int | None = None

class GameOut(Schema):
    id: int
    home_team_id: int
    home_start_goalie_id: int | None
    home_start_goalie_name: str | None
    home_goals: int
    away_team_id: int
    away_start_goalie_id: int | None
    away_start_goalie_name: str | None
    away_goals: int
    game_type_id: int
    game_type: str
    game_type_name_id: int | None
    game_type_name: str | None = Field(None, description="Subtype of the game type.")
    status: int = Field(..., description=get_constant_class_int_description(GameStatus))
    date: datetime.date
    time: datetime.time
    season_id: int | None = None
    arena_id: int | None = None
    rink_id: int | None = None
    analysis: str | None = None

    game_period_id: int | None = None
    game_period_name: str | None

    @staticmethod
    def resolve_home_start_goalie_name(obj: Game) -> str | None:
        if obj.home_start_goalie is not None:
            return obj.home_start_goalie.player.first_name + " " + obj.home_start_goalie.player.last_name
        return None
    
    @staticmethod
    def resolve_away_start_goalie_name(obj: Game) -> str | None:
        if obj.away_start_goalie is not None:
            return obj.away_start_goalie.player.first_name + " " + obj.away_start_goalie.player.last_name
        return None
    
    @staticmethod
    def resolve_game_period_name(obj: Game) -> str | None:
        if obj.game_period is not None:
            return obj.game_period.name
        return None

    @staticmethod
    def resolve_game_type(obj: Game) -> str:
        return obj.game_type.name
    
    @staticmethod
    def resolve_game_type_name(obj: Game) -> str | None:
        if obj.game_type_name is not None:
            return obj.game_type_name.name
        return None

class GameBannerOut(Schema):
    id: int
    home_team_id: int
    away_team_id: int
    home_team_name: str
    away_team_name: str
    home_team_abbreviation: str | None
    away_team_abbreviation: str | None
    date: datetime.date
    time: datetime.time
    game_type_name: str | None
    arena_name: str
    rink_name: str
    game_period_name: str | None
    status: int = Field(..., description=get_constant_class_int_description(GameStatus))
    home_goals: int
    away_goals: int

class GameTypeRecordOut(Schema):
    wins: int
    losses: int
    ties: int

class GameDashboardGameOut(Schema):
    # All fields from GameOut duplicated to avoid resolver method conflicts
    id: int
    home_team_id: int
    home_start_goalie_id: int | None
    home_start_goalie_name: str | None
    home_goals: int
    away_team_id: int
    away_start_goalie_id: int | None
    away_start_goalie_name: str | None
    away_goals: int
    game_type_id: int
    game_type: str
    game_type_name_id: int | None
    game_type_name: str | None = Field(None, description="Subtype of the game type.")
    status: int = Field(..., description=get_constant_class_int_description(GameStatus))
    date: datetime.date
    time: datetime.time
    season_id: int | None = None
    arena_id: int
    rink_id: int | None = None
    analysis: str | None = None
    game_period_id: int | None = None
    game_period_name: str | None

class GameExtendedOut(GameDashboardGameOut):
    home_team_game_type_record: GameTypeRecordOut | None = None
    away_team_game_type_record: GameTypeRecordOut | None = None

class GameDashboardOut(Schema):
    upcoming_games: list[GameDashboardGameOut]
    previous_games: list[GameDashboardGameOut]

class GoalieBaseOut(Schema):
    id: int
    first_name: str
    last_name: str
    number: int

class GameGoalieOut(GoalieBaseOut):
    season_name: str
    date: datetime.date
    team_id: int
    team_name: str
    team_vs_id: int
    team_vs_name: str
    score: str
    goals_against: int
    shots_against: int
    saves: int
    save_percents: int

class PlayerBaseOut(Schema):
    id: int
    first_name: str
    last_name: str
    number: int

class GamePlayerOut(PlayerBaseOut):
    season_name: str
    date: datetime.date
    team_id: int
    team_name: str
    team_vs_id: int
    team_vs_name: str
    score: str
    goals: int
    assists: int
    shots_on_goal: int
    scoring_chances: int
    penalty_minutes: datetime.timedelta
    turnovers: int
    faceoffs: int
    faceoffs_won: int
    faceoff_win_percents: int = Field(0, description="Faceoff Win %.")
    points: int

class GamePlayersIn(Schema):
    goalie_ids: list[int]
    player_ids: list[int]

class GamePlayersOut(Schema):
    home_goalies: list[GoalieBaseOut]
    home_players: list[PlayerBaseOut]
    away_goalies: list[GoalieBaseOut]
    away_players: list[PlayerBaseOut]

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

# region Spray charts

class SprayChartFilters(Schema):
    season_id: int | None = None
    game_id: int | None = None

class GoalieSprayChartFilters(SprayChartFilters):
    shot_type_id: int | None = None

class PlayerSprayChartFilters(SprayChartFilters):
    event_name: str | None = Field(None, description=get_constant_class_str_description(EventName))
    shot_type_id: int | None = None
    is_scoring_chance: bool | None = None
    goal_type: str | None = Field(None, description=get_constant_class_str_description(GoalType))

class GameSprayChartFilters(Schema):
    event_name: str | None = Field(None, description=get_constant_class_str_description(EventName))

# endregion

# region Highlight Reels

class CustomEventIn(Schema):
    event_name: str
    note: str
    youtube_link: str | None = None
    date: datetime.date | None = None
    time: datetime.time | None = None

class CustomEventOut(CustomEventIn):
    id: int

class HighlightIn(Schema):
    game_event_id: int | None = None
    event_name: str | None = None
    note: str | None = None
    youtube_link: str | None = None
    date: datetime.date | None = None
    time: datetime.time | None = None
    order: int | None = None
    visibility: int = Field(HighlightVisibility.PRIVATE.id, description=get_constant_class_int_description(HighlightVisibility))
    users_with_access: list[int] = Field([], description="List of user IDs with access to the highlight.")

class HighlightUpdateIn(HighlightIn):
    id: int | None = None

class HighlightOut(HighlightIn):
    id: int
    event_name: str
    note: str | None = None
    youtube_link: str | None = None
    date: datetime.date | None = None
    time: str | None = None
    is_custom: bool = Field(..., description="Whether the highlight is a custom event.")
    user_id: int
    visibility: int = Field(..., description=get_constant_class_int_description(HighlightVisibility))
    users_with_access: list[int] = Field([], description="List of user IDs with access to the highlight.")

    @staticmethod
    def resolve_event_name(obj: Highlight) -> str:
        if obj.game_event is not None:
            return obj.game_event.event_name.name
        if obj.custom_event is not None:
            return obj.custom_event.event_name
        return "(no associated event)"

    @staticmethod
    def resolve_note(obj: Highlight) -> str | None:
        if obj.game_event is not None:
            return obj.game_event.note
        if obj.custom_event is not None:
            return obj.custom_event.note
        return ""
    
    @staticmethod
    def resolve_youtube_link(obj: Highlight) -> str | None:
        if obj.game_event is not None:
            return obj.game_event.youtube_link
        if obj.custom_event is not None:
            return obj.custom_event.youtube_link
        return None

    @staticmethod
    def resolve_date(obj: Highlight) -> datetime.date | None:
        if obj.game_event is not None:
            return obj.game_event.game.date
        if obj.custom_event is not None:
            return obj.custom_event.date
        return None
    
    @staticmethod
    def resolve_time(obj: Highlight) -> str | None:
        if obj.game_event is not None:
            return f"{obj.game_event.period.name} / {obj.game_event.time.strftime('%M:%S')}"
        if obj.custom_event is not None:
            return obj.custom_event.time.strftime('%H:%M:%S')
        return None

    @staticmethod
    def resolve_is_custom(obj: Highlight) -> bool:
        return (obj.custom_event is not None)

    @staticmethod
    def resolve_users_with_access(obj: Highlight) -> list[int]:
        return [user.user_id for user in obj.users_with_access.all()]

class HighlightReelIn(Schema):
    name: str
    description: str
    highlights: list[HighlightIn]

class HighlightReelUpdateIn(HighlightReelIn):
    highlights: list[HighlightUpdateIn]

class HighlightReelListOut(Schema):
    id: int
    name: str
    description: str
    user_id: int = Field(..., description="ID of the user who created the highlight reel.")
    created_by: str = Field(..., description="Name of the user who created the highlight reel.")
    date: datetime.date

# endregion

# region Video Library

class VideoLibraryIn(Schema):
    name: str
    description: str | None = None
    youtube_link: str | None = None

class VideoLibraryOut(VideoLibraryIn):
    id: int
    added_by: str
    date: datetime.date

# endregion
