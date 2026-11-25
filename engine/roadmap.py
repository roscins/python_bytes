"""The map's view of the levels: every item of the curriculum, written or not.

levels/concepts.toml lists all the levels of every world, but only some of
them have a level pack yet. The map shows them all, in curriculum order. A
slot is either the real Level (it has a pack) or a MissingLevel (it does
not, so it is drawn locked and cannot be played).
"""


class MissingLevel:
    """A level that the curriculum lists but that has no pack yet.

    It has the same id, title, world and boss flag as a Level, so the map
    can draw it, but nothing to play.

    Attributes:
        id: the level id, for example "1-2" or "boss-1".
        title: the level's name from the curriculum.
        world: the world number.
        boss: True for a boss.
    """

    def __init__(self, level_id, title, world, boss):
        """Remember what the curriculum says about the level."""
        self.id = level_id
        self.title = title
        self.world = world
        self.boss = boss


def is_written(slot):
    """Return True if the slot is a real level that can be played."""
    return not isinstance(slot, MissingLevel)


def build_slots(levels, curriculum):
    """Return one slot for each item of `curriculum`, in curriculum order.

    The slot is the Level from `levels` with the same id, or a MissingLevel
    if there is none. A level that the curriculum does not list gets no
    slot. Without a curriculum (None) the slots are just the levels.
    """
    if curriculum is None:
        return list(levels)
    slots = []
    for item in curriculum.items:
        slot = None
        for level in levels:
            if level.id == item.id:
                slot = level
        if slot is None:
            slot = MissingLevel(item.id, item.title, item.world, item.boss)
        slots.append(slot)
    return slots
