import inspect
from typing import Any, Final, Type


class NumName:
    def __init__(self, num: int, name: str):
        self.num = num
        self.name = name

class GameStatus:
    """\"Not Started\", \"Game in Progress\" or \"Game Over\"."""
    NOT_STARTED: Final[NumName] = NumName(1, "Not Started")
    GAME_IN_PROGRESS: Final[NumName] = NumName(2, "Game in Progress")
    GAME_OVER: Final[NumName] = NumName(3, "Game Over")

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
    return sorted([(num_name.num, num_name.name) for _, num_name in inspect.getmembers(constant_class, lambda x: isinstance(x, NumName))], key=lambda x: x[0])

def get_constant_class_int_description(constant_class) -> str:
    return ", ".join(sorted([f'{num_name.num} - {num_name.name}' for _, num_name in inspect.getmembers(constant_class, lambda x: isinstance(x, NumName))]))

def get_constant_class_str_choices(constant_class) -> list[tuple[str, str]]:
    return sorted([(str_name, str_name) for name, str_name in inspect.getmembers(constant_class, lambda x: not(inspect.isroutine(x))) if not(name.startswith('__'))], key=lambda x: x[0])

def get_constant_class_str_description(constant_class) -> str:
    return ", ".join(sorted([f'{str_name}' for name, str_name in inspect.getmembers(constant_class, lambda x: not(inspect.isroutine(x))) if not(name.startswith('__'))]))
