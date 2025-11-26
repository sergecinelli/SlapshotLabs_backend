from typing import Final


class GameEventSystemStatus:
    """Statuses for data analyzer."""
    NEW: Final[int] = 1
    '''Event has been added: apply it to statistics.'''
    DEPRECATED: Final[int] = 2
    '''Event has been deprecated: remove it from statistics and then delete it from the database.'''