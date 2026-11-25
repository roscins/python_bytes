"""The player's numbers as the map shows them: XP, stars, coins and locks.

The renderer does not know about the game state, so this module turns the
state into a MapStatus that render/world_map.py can draw.
"""

from engine.roadmap import is_written
from engine.scoring import MAX_STARS, is_unlocked
from render.world_map import MapStatus


def level_stars(state, level):
    """Return the stars earned in `level` (0 if it was never submitted)."""
    if level.id not in state.progress:
        return 0
    return state.progress[level.id].stars


def hud_text(state, world_levels):
    """Return the HUD line, for example "XP 1240   ★ 7/12   COINS 35".

    The stars count is for the levels of the world on screen.
    """
    stars = 0
    for level in world_levels:
        stars = stars + level_stars(state, level)
    most = MAX_STARS * len(world_levels)
    return f"XP {state.xp}   ★ {stars}/{most}   COINS {state.coins}"


def map_status(state, world_levels):
    """Return the MapStatus for the slots of one world.

    A slot is locked if its level is not written yet, or the slot before
    it (anywhere in the game) is not cleared.
    """
    locked = []
    stars = []
    all_slots = state.slots()
    for level in world_levels:
        open_to_play = is_written(level) and is_unlocked(all_slots, state.cleared, level)
        locked.append(not open_to_play)
        stars.append(level_stars(state, level))
    return MapStatus(hud_text(state, world_levels), locked, stars)
