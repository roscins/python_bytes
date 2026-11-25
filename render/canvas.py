"""A canvas: a blank picture that sprites are pasted onto.

A canvas has the same shape as a sprite: a list of row strings, where each
character is a palette code or "." for a transparent pixel. So once the
sprites are pasted, render_sprite in render/sprite.py draws the canvas
like any other sprite.
"""

from render.palette import TRANSPARENT


def new_canvas(width, height):
    """Return a blank canvas of `width` x `height` transparent pixels."""
    canvas = []
    for row in range(height):
        canvas.append(TRANSPARENT * width)
    return canvas


def set_pixel(canvas, column, row, code):
    """Change one pixel of the canvas. Pixels outside the canvas are ignored.

    Strings cannot be changed in place, so the row is rebuilt from the part
    before the pixel, the new pixel and the part after it.
    """
    if row < 0 or row >= len(canvas):
        return
    line = canvas[row]
    if column < 0 or column >= len(line):
        return
    canvas[row] = line[:column] + code + line[column + 1:]


def paste(canvas, sprite, left, top):
    """Copy `sprite` onto `canvas` with its top-left corner at (left, top).

    Transparent pixels in the sprite let the canvas show through. Parts of
    the sprite that fall outside the canvas are cut off.
    """
    for sprite_row in range(len(sprite)):
        for sprite_column in range(len(sprite[sprite_row])):
            code = sprite[sprite_row][sprite_column]
            if code != TRANSPARENT:
                set_pixel(canvas, left + sprite_column, top + sprite_row, code)


def draw_line(canvas, code, left, right, top, thickness):
    """Draw a horizontal line from column `left` to `right` (both included).

    The line is `thickness` pixels high, starting at row `top`.
    """
    for row in range(top, top + thickness):
        for column in range(left, right + 1):
            set_pixel(canvas, column, row, code)
