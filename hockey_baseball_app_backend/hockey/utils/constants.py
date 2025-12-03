import inspect
from typing import Any, Final, Type


# region Constant values

GOALIE_POSITION_NAME: Final[str] = "Goalie"
NO_GOALIE_FIRST_NAME: Final[str] = "No"
NO_GOALIE_LAST_NAME: Final[str] = "Goalie"

# endregion

class IdName:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

class GameStatus:
    """\"Not Started\", \"Game in Progress\" or \"Game Over\"."""
    NOT_STARTED: Final[IdName] = IdName(1, "Not Started")
    GAME_IN_PROGRESS: Final[IdName] = IdName(2, "Game in Progress")
    GAME_OVER: Final[IdName] = IdName(3, "Game Over")

class EventName:
    """\"Shot on Goal\", \"Turnover\", \"Faceoff\", \"Goalie Change\" or \"Penalty\"."""
    SHOT: Final[str] = "Shot on Goal"
    TURNOVER: Final[str] = "Turnover"
    FACEOFF: Final[str] = "Faceoff"
    GOALIE_CHANGE: Final[str] = "Goalie Change"
    PENALTY: Final[str] = "Penalty"

class GoalType:
    """\"Short Handed\", \"Even Strength\" or \"Power Play\"."""
    SHORT_HANDED: Final[str] = "Short Handed"
    EVEN_STRENGTH: Final[str] = "Even Strength"
    POWER_PLAY: Final[str] = "Power Play"

class RinkZone:
    """\"Defending\", \"Neutral\" or \"Attacking\"."""
    DEFENDING: Final[str] = "Defending"
    NEUTRAL: Final[str] = "Neutral"
    ATTACKING: Final[str] = "Attacking"

class GameEventSystemStatus:
    """Statuses for data analyzer."""
    NEW: Final[int] = 1
    '''Event has been added: apply it to statistics.'''
    DEPRECATED: Final[int] = 2
    '''Event has been deprecated: remove it from statistics and then delete it from the database.'''

class HighlightVisibility:
    """\"Private\", \"Restricted\" or \"Public\"."""
    PRIVATE: Final[IdName] = IdName(1, "Private")
    RESTRICTED: Final[IdName] = IdName(2, "Restricted")
    PUBLIC: Final[IdName] = IdName(3, "Public")

def get_constant_class_int_choices(constant_class) -> list[tuple[int, str]]:
    return sorted([(num_name.id, num_name.name) for _, num_name in inspect.getmembers(constant_class, lambda x: isinstance(x, IdName))], key=lambda x: x[0])

def get_constant_class_int_description(constant_class) -> str:
    return ", ".join(sorted([f'{num_name.id} - {num_name.name}' for _, num_name in inspect.getmembers(constant_class, lambda x: isinstance(x, IdName))]))

def get_constant_class_str_choices(constant_class) -> list[tuple[str, str]]:
    return sorted([(str_name, str_name) for name, str_name in inspect.getmembers(constant_class, lambda x: not(inspect.isroutine(x))) if not(name.startswith('__'))], key=lambda x: x[0])

def get_constant_class_str_description(constant_class) -> str:
    return ", ".join(sorted([f'{str_name}' for name, str_name in inspect.getmembers(constant_class, lambda x: not(inspect.isroutine(x))) if not(name.startswith('__'))]))

class ApiDocTags:
    PLAYER: Final[str] = "Hockey - Goalie, Player"
    TEAM: Final[str] = "Hockey - Team, Season"
    GAME: Final[str] = "Hockey - Game"
    GAME_PLAYER: Final[str] = "Hockey - Game Player"
    GAME_EVENT: Final[str] = "Hockey - Game Event"
    STATS: Final[str] = "Hockey - Statistics"
    SPRAY_CHART: Final[str] = "Hockey - Spray Charts"
    HIGHLIGHT_REEL: Final[str] = "Hockey - Highlight Reel"
    VIDEO_LIBRARY: Final[str] = "Hockey - Video Library"
