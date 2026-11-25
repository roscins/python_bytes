"""Draw the level-clear screen: a flashing bar, the stars filling in, and the rewards.

The screen is a short animation. In each frame one more star fills in and
the bar at the top switches between White and Green; the last frame has a
Green bar and every star the player earned. All frames have the same
height, so the loop can draw each one over the one before.
"""

from pathlib import Path

from render.canvas import draw_line, new_canvas, paste
from render.palette import load_palette
from render.sprite import load_sprite, render_sprite

ART_FOLDER = Path(__file__).parent.parent / "art"

SCREEN_WIDTH = 80       # pixels, the same as terminal cells
ICON_SIZE = 8           # stars and coins are 8 x 8 pixels
BAR_THICKNESS = 2
ICON_TOP = BAR_THICKNESS + 2
PICTURE_HEIGHT = ICON_TOP + ICON_SIZE + 2
ICON_GAP = 4            # pixels between two stars
MAX_STARS = 3

GREEN = "8"             # the art guide's colour for success
WHITE = "5"             # the art guide's colour for sparkles


class ClearArt:
    """The palette and icons the level-clear screen is drawn with.

    Attributes:
        palette: the game's palette.
        star: the sprite for an earned star.
        star_empty: the sprite for a star not earned.
        coin: the sprite for a coin.
    """

    def __init__(self, palette, star, star_empty, coin):
        """Remember the palette and the icons."""
        self.palette = palette
        self.star = star
        self.star_empty = star_empty
        self.coin = coin


def load_clear_art(art_folder=ART_FOLDER):
    """Read the palette and the star and coin icons from the art folder."""
    palette = load_palette(art_folder / "palette.txt")
    star = load_sprite(art_folder / "star-full.txt", palette)
    star_empty = load_sprite(art_folder / "star-empty.txt", palette)
    coin = load_sprite(art_folder / "coin-spin.txt", palette)
    return ClearArt(palette, star, star_empty, coin)


def stars_left_edge():
    """Return the column where the first of the three stars starts, so they sit centred."""
    width = MAX_STARS * ICON_SIZE + (MAX_STARS - 1) * ICON_GAP
    return (SCREEN_WIDTH - width) // 2


def clear_picture(filled_stars, bar_colour, art):
    """Return the pixel picture as terminal lines: the bar, the stars and a coin."""
    canvas = new_canvas(SCREEN_WIDTH, PICTURE_HEIGHT)
    draw_line(canvas, bar_colour, 0, SCREEN_WIDTH - 1, 0, BAR_THICKNESS)
    left = stars_left_edge()
    for index in range(MAX_STARS):
        star = art.star_empty
        if index < filled_stars:
            star = art.star
        paste(canvas, star, left + index * (ICON_SIZE + ICON_GAP), ICON_TOP)
    coin_left = left + MAX_STARS * (ICON_SIZE + ICON_GAP) + ICON_GAP
    paste(canvas, art.coin, coin_left, ICON_TOP)
    return render_sprite(canvas, art.palette)


def clear_frame(banner, filled_stars, bar_colour, reward_lines, art):
    """Return one frame of the level-clear screen as text."""
    lines = [banner]
    lines.extend(clear_picture(filled_stars, bar_colour, art))
    lines.extend(reward_lines)
    return "\n".join(lines)


def level_clear_frames(level_id, title, score, stars, xp_gained, coins_gained, power_up, art):
    """Return the frames of the level-clear animation.

    The first frame has no stars filled in; each frame after it fills one
    more, up to `stars`, while the bar flashes. `power_up` is the power-up
    the level gives, or "" for none.
    """
    banner = f"LEVEL {level_id} CLEARED · {title.upper()}"
    reward_lines = ["", f"SCORE {score} %", f"+{xp_gained} XP   +{coins_gained} COINS"]
    if power_up:
        reward_lines.append(f"POWER-UP: {power_up}")
    frames = []
    for filled in range(stars + 1):
        bar_colour = WHITE
        if filled % 2 == 1:
            bar_colour = GREEN
        frames.append(clear_frame(banner, filled, bar_colour, reward_lines, art))
    # The last frame always has a green bar, whatever the number of stars.
    frames.append(clear_frame(banner, stars, GREEN, reward_lines, art))
    return frames
