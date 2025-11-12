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
    """\"Shot on Goal\", \"Turnover\", \"Faceoff\" or \"Goalie Change\"."""
    SHOT: Final[str] = "Shot on Goal"
    TURNOVER: Final[str] = "Turnover"
    FACEOFF: Final[str] = "Faceoff"
    GOALIE_CHANGE: Final[str] = "Goalie Change"

class GoalType:
    """\"Short Handed\", \"Normal\" or \"Power Play\"."""
    SHORT_HANDED: Final[str] = "Short Handed"
    NORMAL: Final[str] = "Normal"
    POWER_PLAY: Final[str] = "Power Play"

class RinkZone:
    """\"Defending\", \"Neutral\" or \"Attacking\"."""
    DEFENDING: Final[str] = "Defending"
    NEUTRAL: Final[str] = "Neutral"
    ATTACKING: Final[str] = "Attacking"

def get_constant_class_int_choices(constant_class) -> list[tuple[int, str]]:
    return sorted([(num_name.id, num_name.name) for _, num_name in inspect.getmembers(constant_class, lambda x: isinstance(x, IdName))], key=lambda x: x[0])

def get_constant_class_int_description(constant_class) -> str:
    return ", ".join(sorted([f'{num_name.id} - {num_name.name}' for _, num_name in inspect.getmembers(constant_class, lambda x: isinstance(x, IdName))]))

def get_constant_class_str_choices(constant_class) -> list[tuple[str, str]]:
    return sorted([(str_name, str_name) for name, str_name in inspect.getmembers(constant_class, lambda x: not(inspect.isroutine(x))) if not(name.startswith('__'))], key=lambda x: x[0])

def get_constant_class_str_description(constant_class) -> str:
    return ", ".join(sorted([f'{str_name}' for name, str_name in inspect.getmembers(constant_class, lambda x: not(inspect.isroutine(x))) if not(name.startswith('__'))]))
