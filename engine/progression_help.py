"""Which level the player should play next, for the hints on screen."""

from engine.roadmap import is_written
from engine.scoring import is_unlocked


def next_level_to_play(state):
    """Return the first level that is open and not cleared yet, or None."""
    slots = state.slots()
    for slot in slots:
        if is_written(slot) and slot.id not in state.cleared and is_unlocked(slots, state.cleared, slot):
            return slot
    return None
