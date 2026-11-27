"""Snek's faces: idle, happy (a wave passed), dizzy (a wave failed), celebrating (level clear).

Each is a 16 x 16 sprite in art/ (see docs/art-style-guide.md). They are
drawn at the side of the results, so Snek reacts to what the player did.
"""

from pathlib import Path

from render.ansi import fit, pad
from render.palette import load_palette
from render.sprite import load_sprite, render_sprite

ART_FOLDER = Path(__file__).parent.parent / "art"

REACTION_NAMES = ["idle", "happy", "dizzy", "celebrate"]


class ReactionArt:
    """The palette and the four sprites.

    Attributes:
        palette: the game's palette.
        sprites: a dict from a reaction's name to its sprite.
    """

    def __init__(self, palette, sprites):
        """Remember the palette and the sprites."""
        self.palette = palette
        self.sprites = sprites


def load_reaction_art(art_folder=ART_FOLDER):
    """Read the palette and Snek's four faces from the art folder."""
    palette = load_palette(Path(art_folder) / "palette.txt")
    sprites = {}
    for name in REACTION_NAMES:
        sprites[name] = load_sprite(Path(art_folder) / f"snek-{name}.txt", palette)
    return ReactionArt(palette, sprites)


def reaction_lines(name, art):
    """Return Snek's face `name` as 8 terminal lines, each 16 cells wide.

    Raises KeyError for a name that is not one of REACTION_NAMES.
    """
    return render_sprite(art.sprites[name], art.palette)


def side_by_side(left_lines, right_lines, left_width, gap=2):
    """Put two blocks of lines next to each other.

    The left block is padded (or cut) to `left_width` cells; `gap` spaces
    separate it from the right block. The blocks may have different heights.
    """
    rows = []
    for index in range(max(len(left_lines), len(right_lines))):
        left = ""
        if index < len(left_lines):
            left = left_lines[index]
        right = ""
        if index < len(right_lines):
            right = right_lines[index]
        rows.append(pad(fit(left, left_width), left_width) + " " * gap + right)
    return rows
