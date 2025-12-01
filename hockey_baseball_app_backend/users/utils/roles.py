import inspect
from typing import Final


class IdName:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

class Role:
    """\"Admin\", \"Coach\" or \"Player\"."""
    ADMIN: Final[IdName] = IdName(1, "Admin")
    COACH: Final[IdName] = IdName(2, "Coach")
    PLAYER: Final[IdName] = IdName(3, "Player")
    
    @staticmethod
    def get_name_by_id(id: int) -> str:
        return next((role.name for _, role in inspect.getmembers(Role, lambda x: isinstance(x, IdName)) if role.id == id), "Player")

def is_user_admin(user) -> bool:
    return user.role == Role.ADMIN.id

def is_user_coach(user, team_id: int) -> bool:
    return is_user_admin(user) or (user.role == Role.COACH.id and user.team_id == team_id)

def is_user_player(user) -> bool:
    return user.role <= Role.PLAYER.id

def get_constant_class_int_choices(constant_class) -> list[tuple[int, str]]:
    return sorted([(num_name.id, num_name.name) for _, num_name in inspect.getmembers(constant_class, lambda x: isinstance(x, IdName))], key=lambda x: x[0])

def get_constant_class_int_description(constant_class) -> str:
    return ", ".join(sorted([f'{num_name.id} - {num_name.name}' for _, num_name in inspect.getmembers(constant_class, lambda x: isinstance(x, IdName))]))

def get_constant_class_str_description(constant_class) -> str:
    return ", ".join(sorted([num_name.name for _, num_name in inspect.getmembers(constant_class, lambda x: isinstance(x, IdName))], key=lambda x: x[0]))
