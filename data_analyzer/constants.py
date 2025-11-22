from typing import Final


class GameSystemStatus:
    """Statuses for data analyzer."""
    ACTUAL: Final[None] = None
    '''No action required in analyzer.'''
    NEW: Final[int] = 1
    '''Game has finished: apply it and its events to statistics.'''
    MODIFIED: Final[int] = 2
    '''Game has been modified: apply it to statistics.'''
    DEPRECATED: Final[int] = 3
    '''Game has been deprecated: remove it and its events from statistics and then delete it from the database.'''
    UNDONE_FINISH: Final[int] = 4
    '''Game finish has been undone: remove it and its events from statistics.'''

class GameEventSystemStatus:
    """Statuses for data analyzer."""
    ACTUAL: Final[None] = None
    '''No action required in analyzer.'''
    NEW: Final[int] = 1
    '''Event has been added: apply it to statistics.'''
    # MODIFIED: Final[int] = 2  # Need to re-add event to make sure old one is correctly deleted from game stats.
    DEPRECATED: Final[int] = 3
    '''Event has been deprecated: remove it from statistics and then delete it from the database.'''