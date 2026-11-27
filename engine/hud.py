"""The player's numbers as the map shows them: stars, coins and locks.

The renderer does not know about the game state, so this module turns the
state into a MapStatus that render/world_map.py can draw.
"""

from engine.roadmap import is_written
from engine.scoring import MAX_STARS, is_unlocked
from render.hud import HudInfo
from render.world_map import WORLD_NAMES, MapStatus


def level_stars(state, level):
    """Return the stars earned in `level` (0 if it was never submitted)."""
    if level.id not in state.progress:
        return 0
    return state.progress[level.id].stars


def hud_text(state, world_levels):
    """Return the HUD line, for example "★ 7/12   COINS 35".

    The stars count is for the levels of the world on screen.
    """
    stars = 0
    for level in world_levels:
        stars = stars + level_stars(state, level)
    most = MAX_STARS * len(world_levels)
    return f"★ {stars}/{most}   COINS {state.coins}"


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


def hud_info(state, flash=False):
    """Return what the HUD at the top of the screen shows (see render/hud.py).

    At the map it shows the world; while a level is being played, the level
    too. The stars are those of the current world. In a boss fight it also
    shows the tries left.
    """
    world = state.current_world()
    if world is None:
        world = 1
    slots = state.slots_in_world(world)
    stars = 0
    for slot in slots:
        stars = stars + level_stars(state, slot)
    level = state.find_level(state.current_level)
    level_id = None
    level_title = ""
    tries = None
    if state.coding and level is not None:
        level_id = level.id
        level_title = level.title
        fight = state.boss_fight
        if level.boss and fight is not None and fight.level.id == level.id:
            tries = (fight.lives, 3)
        elif level.boss:
            tries = (3, 3)
    return HudInfo(world, WORLD_NAMES.get(world, ""), level_id, level_title, stars,
                   MAX_STARS * len(slots), state.coins, state.combo, tries, flash)
