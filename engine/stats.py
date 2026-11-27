"""The stats command: levels cleared and stars, world by world."""

from engine.hud import level_stars
from engine.scoring import MAX_STARS
from render.world_map import WORLD_NAMES


def world_numbers(slots):
    """Return the world numbers on the map, in order, each once."""
    numbers = []
    for slot in slots:
        if slot.world not in numbers:
            numbers.append(slot.world)
    return numbers


def stats_text(state):
    """Return the table of progress: one row per world and a total."""
    lines = ["STATS", f"{'WORLD':<28}{'CLEARED':<11}STARS"]
    all_cleared = 0
    all_levels = 0
    all_stars = 0
    for world in world_numbers(state.slots()):
        slots = state.slots_in_world(world)
        cleared = 0
        stars = 0
        for slot in slots:
            if slot.id in state.cleared:
                cleared = cleared + 1
            stars = stars + level_stars(state, slot)
        name = f"{world}  {WORLD_NAMES.get(world, '')}"
        count = f"{cleared}/{len(slots)}"
        lines.append(f"{name:<28}{count:<11}★ {stars}/{MAX_STARS * len(slots)}")
        all_cleared = all_cleared + cleared
        all_levels = all_levels + len(slots)
        all_stars = all_stars + stars
    total = f"{all_cleared}/{all_levels}"
    lines.append(f"{'TOTAL':<28}{total:<11}★ {all_stars}/{MAX_STARS * all_levels}")
    return "\n".join(lines)
