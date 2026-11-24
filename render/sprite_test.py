"""Draw a small robot sprite in the terminal.

Each terminal cell shows two pixels stacked on top of each other, using the
"upper half block" character. The top pixel is drawn as the text colour and
the bottom pixel as the background colour, so an 8x8 sprite fits in 8x4 cells.

Run it with:  python -m render.sprite_test
"""

import os

# ANSI escape codes. "\x1b[" starts a command, "m" ends a colour command.
RESET = "\x1b[0m"
UPPER_HALF_BLOCK = "▀"  # the top half of the cell is filled
LOWER_HALF_BLOCK = "▄"  # the bottom half of the cell is filled
TRANSPARENT = "."

# Each letter in the sprite stands for one of these (red, green, blue) colours.
PALETTE = {
    "1": (194, 195, 199),  # light grey body
    "2": (29, 43, 83),     # dark blue outline
    "3": (41, 173, 255),   # bright blue eyes and mouth
}

# The robot, one string per row. "." means "no pixel here".
ROBOT = [
    "..2222..",
    ".211112.",
    "21311312",
    "21111112",
    "21333312",
    ".211112.",
    "..2..2..",
    ".22..22.",
]


def foreground(code):
    """Return the escape code that sets the text colour to a palette colour."""
    red, green, blue = PALETTE[code]
    return f"\x1b[38;2;{red};{green};{blue}m"


def background(code):
    """Return the escape code that sets the background to a palette colour."""
    red, green, blue = PALETTE[code]
    return f"\x1b[48;2;{red};{green};{blue}m"


def draw_cell(top, bottom):
    """Return the text for one terminal cell showing two stacked pixels.

    `top` and `bottom` are palette codes, or "." for a transparent pixel.
    """
    if top == TRANSPARENT and bottom == TRANSPARENT:
        return RESET + " "
    if top == TRANSPARENT:
        return RESET + foreground(bottom) + LOWER_HALF_BLOCK
    if bottom == TRANSPARENT:
        return RESET + foreground(top) + UPPER_HALF_BLOCK
    return foreground(top) + background(bottom) + UPPER_HALF_BLOCK


def draw_row_pair(top_row, bottom_row):
    """Return one line of terminal text built from two rows of the sprite."""
    line = ""
    for column in range(len(top_row)):
        line = line + draw_cell(top_row[column], bottom_row[column])
    return line + RESET


def render_sprite(sprite):
    """Return a list of terminal lines that draw the whole sprite.

    The sprite must have an even number of rows, because each line of
    output shows two rows of pixels.
    """
    lines = []
    for row in range(0, len(sprite), 2):
        lines.append(draw_row_pair(sprite[row], sprite[row + 1]))
    return lines


def main():
    """Print the robot sprite to the terminal."""
    if os.name == "nt":
        os.system("")  # switches on ANSI colours in older Windows consoles
    for line in render_sprite(ROBOT):
        print(line)


if __name__ == "__main__":
    main()
