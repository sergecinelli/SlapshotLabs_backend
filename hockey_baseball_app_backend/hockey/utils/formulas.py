from typing import Protocol


class HasWinsTies(Protocol):
    wins: int
    ties: int

def get_team_points(obj: HasWinsTies) -> int:
    return (obj.wins * 2) + obj.ties