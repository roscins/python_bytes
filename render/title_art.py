"""The title screen: the pixel-art PYTHON BYTES logo and Snek crossing the screen.

The letters come from a small pixel font (5 x 7 pixels per letter) written
out below, so no extra art files are needed. title_frames() returns the
frames of the animation: the logo stays, Snek slithers from the left edge to
the middle, and the last frame says PRESS ENTER.
"""

from pathlib import Path

from render.canvas import new_canvas, paste, set_pixel
from render.reactions import load_reaction_art
from render.sprite import render_sprite

ART_FOLDER = Path(__file__).parent.parent / "art"

LOGO_TEXT = "PYTHON BYTES"
SCREEN_WIDTH = 80
LETTER_WIDTH = 5
LETTER_GAP = 1
SPACE_WIDTH = 4
LOGO_HEIGHT = 10        # 7 rows of letters, 1 above, a shadow below
SNEK_SIZE = 16
SNEK_TOP = LOGO_HEIGHT + 2
PICTURE_HEIGHT = SNEK_TOP + SNEK_SIZE

FILL = "8"      # green
SHADOW = "1"    # navy

# Each letter is 7 rows of 5 pixels: # is a pixel, . is empty.
GLYPHS = {
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "N": ["#...#", "##..#", "#.#.#", "#.#.#", "#..##", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
}


class TitleArt:
    """The palette and Snek's sprite for the title screen."""

    def __init__(self, palette, snek):
        """Remember the palette and the sprite."""
        self.palette = palette
        self.snek = snek


def load_title_art(art_folder=ART_FOLDER):
    """Read the palette and Snek's idle sprite."""
    reactions = load_reaction_art(art_folder)
    return TitleArt(reactions.palette, reactions.sprites["idle"])


def logo_width(text):
    """Return how many pixels wide the logo of `text` is."""
    width = 0
    for letter in text:
        if letter == " ":
            width = width + SPACE_WIDTH
        else:
            width = width + LETTER_WIDTH + LETTER_GAP
    return width - LETTER_GAP


def draw_glyph(canvas, letter, left, top):
    """Draw one letter with its shadow (one pixel down and to the right)."""
    rows = GLYPHS[letter]
    for shadow in (True, False):
        for row in range(len(rows)):
            for column in range(LETTER_WIDTH):
                if rows[row][column] != "#":
                    continue
                if shadow:
                    set_pixel(canvas, left + column + 1, top + row + 1, SHADOW)
                else:
                    set_pixel(canvas, left + column, top + row, FILL)


def logo_canvas(text):
    """Return a canvas with the logo of `text` drawn in the middle of the top."""
    canvas = new_canvas(SCREEN_WIDTH, LOGO_HEIGHT)
    left = (SCREEN_WIDTH - logo_width(text)) // 2
    for letter in text:
        if letter == " ":
            left = left + SPACE_WIDTH
        else:
            draw_glyph(canvas, letter, left, 1)
            left = left + LETTER_WIDTH + LETTER_GAP
    return canvas


def title_picture(art, snek_left):
    """Return the title picture, with Snek's left edge at `snek_left`, as terminal lines."""
    canvas = new_canvas(SCREEN_WIDTH, PICTURE_HEIGHT)
    paste(canvas, logo_canvas(LOGO_TEXT), 0, 0)
    paste(canvas, art.snek, snek_left, SNEK_TOP)
    return render_sprite(canvas, art.palette)


def centred(text):
    """Return `text` centred in the 80-column screen."""
    return text.center(SCREEN_WIDTH).rstrip()


def title_frames(art, step=4):
    """Return the frames of the title animation, each as one text.

    Snek starts off the left edge and moves `step` pixels per frame to the
    middle. The last frame adds PRESS ENTER. All frames have the same height.
    """
    middle = (SCREEN_WIDTH - SNEK_SIZE) // 2
    frames = []
    for left in range(-SNEK_SIZE, middle, step):
        lines = title_picture(art, left) + ["", ""]
        frames.append("\n".join(lines))
    lines = title_picture(art, middle) + ["", centred("PRESS ENTER")]
    frames.append("\n".join(lines))
    return frames
