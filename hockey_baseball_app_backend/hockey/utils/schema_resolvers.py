from typing import Any
from django.forms.models import model_to_dict

from hockey.models import GameEvents


def game_event_player_ids(game_event: GameEvents) -> dict[str, Any]:
    data = model_to_dict(game_event, exclude=['players'])
    data['players'] = []
    for player in game_event.players.all():
        data['players'].append(player.id)
    return data