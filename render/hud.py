"""The two lines at the top of every screen: where you are, and your numbers.

    WORLD 1 · BOOT SECTOR · 1-2 MEMORY CELLS
    ★ 7/18   COINS 35   COMBO x3

Inside a boss fight the second line also shows TRIES 2 of 3. There is no XP
and there are no lives in the game, so none are shown.
"""

from render.ansi import RESET, fit, pad

REVERSE = "\x1b[7m"
GOLD = "\x1b[33m"
MAGENTA = "\x1b[95m"
RED = "\x1b[31m"
GAP = "   "


class HudInfo:
    """What the HUD shows.

    Attributes:
        world: the world number.
        world_name: the world's name, for example "Boot Sector".
        level_id: the level being played, or None at the map.
        level_title: the level's title ("" at the map).
        stars: the stars earned in this world.
        max_stars: the stars this world can give.
        coins: the player's coins.
        combo: waves passed first try in a row (0 shows nothing).
        tries: (left, total) in a boss fight, otherwise None.
        flash: True for the moment the combo has just gone up.
    """

    def __init__(self, world, world_name, level_id, level_title, stars, max_stars,
                 coins, combo, tries, flash):
        """Remember every part."""
        self.world = world
        self.world_name = world_name
        self.level_id = level_id
        self.level_title = level_title
        self.stars = stars
        self.max_stars = max_stars
        self.coins = coins
        self.combo = combo
        self.tries = tries
        self.flash = flash


def first_line(info, width, color):
    """Return the line with the world and the level."""
    text = f" WORLD {info.world} · {info.world_name.upper()}"
    if info.level_id is not None:
        text = text + f" · {info.level_id} {info.level_title.upper()}"
    text = pad(fit(text, width), width)
    if color:
        return REVERSE + text + RESET
    return text


def paint(text, code, color):
    """Return `text` in the colour `code` if `color` is True."""
    if color:
        return code + text + RESET
    return text


def second_line(info, width, color):
    """Return the line with the stars, the coins, the combo and the tries."""
    parts = [paint(f"★ {info.stars}/{info.max_stars}", GOLD, color),
             paint(f"COINS {info.coins}", GOLD, color)]
    if info.combo > 0:
        combo = paint(f"COMBO x{info.combo}", MAGENTA, color)
        if info.flash and color:
            combo = REVERSE + f"COMBO x{info.combo}" + RESET
        parts.append(combo)
    if info.tries is not None:
        left, total = info.tries
        parts.append(paint(f"TRIES {left} of {total}", RED, color))
    return pad(fit(" " + GAP.join(parts), width), width)


def hud_lines(info, width, color):
    """Return the two HUD lines, each exactly `width` cells wide."""
    return [first_line(info, width, color), second_line(info, width, color)]
