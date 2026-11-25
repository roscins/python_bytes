"""Load a sprite from a text file and draw it with half-block characters.

Each terminal cell shows two pixels stacked on top of each other, using the
"upper half block" character. The top pixel is drawn as the text colour and
the bottom pixel as the background colour, so an 8 x 8 sprite fits in 8 x 4
cells.

A sprite file has one line per row of pixels. Each character is a palette
code, or "." for a transparent pixel. The art style guide allows nothing
else: no comments, no blank lines and no spaces.
"""

from render.palette import TRANSPARENT, background, foreground

# ANSI escape code that turns all colours back to normal.
RESET = "\x1b[0m"
UPPER_HALF_BLOCK = "▀"  # the top half of the cell is filled
LOWER_HALF_BLOCK = "▄"  # the bottom half of the cell is filled


class SpriteError(ValueError):
    """A sprite file that cannot be drawn, for example with uneven rows."""


def load_sprite(path, palette):
    """Read a sprite file and return its rows as a list of strings.

    If the sprite has an odd number of rows, a transparent row is added at
    the bottom, because each terminal line shows two rows.

    Raises SpriteError if the file has no rows, a blank line, rows of
    different widths, or a pixel that is not "." or a code in the palette.
    """
    rows = []
    width = None
    with open(path, encoding="utf-8") as sprite_file:
        line_number = 0
        for line in sprite_file:
            line_number = line_number + 1
            row = line.rstrip("\n")
            if row.strip() == "":
                raise SpriteError(f"{path}, line {line_number}: blank lines are not allowed")
            if width is None:
                width = len(row)
            elif len(row) != width:
                raise SpriteError(
                    f"{path}, line {line_number}: row is {len(row)} pixels wide, "
                    f"but the first row is {width}"
                )
            for pixel in row:
                check_pixel(pixel, palette, f"{path}, line {line_number}")
            rows.append(row)
    if not rows:
        raise SpriteError(f"{path}: the sprite has no rows")
    if len(rows) % 2 == 1:
        rows.append(TRANSPARENT * width)
    return rows


def check_pixel(pixel, palette, place):
    """Raise SpriteError if `pixel` is not "." or a code in the palette.

    `place` says where the pixel came from, for error messages. Spaces and
    "#" get their own message, because they are easy mistakes to make.
    """
    if pixel == TRANSPARENT or pixel in palette:
        return
    if pixel == " ":
        raise SpriteError(f"{place}: spaces are not allowed, use '.' for a transparent pixel")
    if pixel == "#":
        raise SpriteError(f"{place}: comments are not allowed in sprite files")
    raise SpriteError(f"{place}: {pixel!r} is not in the palette")


def draw_cell(top, bottom, palette):
    """Return the text for one terminal cell showing two stacked pixels.

    `top` and `bottom` are palette codes, or "." for a transparent pixel.
    """
    if top == TRANSPARENT and bottom == TRANSPARENT:
        return RESET + " "
    if top == TRANSPARENT:
        return RESET + foreground(palette[bottom]) + LOWER_HALF_BLOCK
    if bottom == TRANSPARENT:
        return RESET + foreground(palette[top]) + UPPER_HALF_BLOCK
    return foreground(palette[top]) + background(palette[bottom]) + UPPER_HALF_BLOCK


def draw_row_pair(top_row, bottom_row, palette):
    """Return one line of terminal text built from two rows of the sprite."""
    line = ""
    for column in range(len(top_row)):
        line = line + draw_cell(top_row[column], bottom_row[column], palette)
    return line + RESET


def render_sprite(sprite, palette):
    """Return a list of terminal lines that draw the whole sprite.

    The sprite must have an even number of rows, because each line shows
    two rows. load_sprite makes sure of that; a sprite made some other way
    with an odd number of rows raises SpriteError.
    """
    if len(sprite) % 2 == 1:
        raise SpriteError(f"the sprite has {len(sprite)} rows, but it needs an even number")
    lines = []
    for row in range(0, len(sprite), 2):
        lines.append(draw_row_pair(sprite[row], sprite[row + 1], palette))
    return lines
