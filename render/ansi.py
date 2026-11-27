"""Measuring and cutting text that has colour codes in it.

A colour code such as ESC[36m takes no room on the screen. To lay text out
in columns we need its visible length, not its length in characters. All
the symbols the game draws with (stars, box characters, hearts) are one
cell wide, so the visible length is the number of characters left after the
colour codes are removed.
"""

import re

RESET = "\x1b[0m"

ANSI_CODE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


def strip_ansi(text):
    """Return `text` without its colour (and other) escape codes."""
    return ANSI_CODE.sub("", text)


def visible_length(text):
    """Return how many cells `text` takes on the screen."""
    return len(strip_ansi(text))


def pad(text, width):
    """Return `text` followed by spaces up to `width` visible cells (never cut)."""
    missing = width - visible_length(text)
    if missing <= 0:
        return text
    return text + " " * missing


def fit(text, width):
    """Return `text` cut to at most `width` visible cells.

    The colour codes are kept, and if the text was cut, a reset code at the
    end makes sure a colour is never left open for the next line.
    """
    if visible_length(text) <= width:
        return text
    result = ""
    shown = 0
    position = 0
    had_colour = False
    while position < len(text):
        code = ANSI_CODE.match(text, position)
        if code:
            result = result + code.group()
            position = code.end()
            had_colour = True
        else:
            if shown < width:
                result = result + text[position]
                shown = shown + 1
            position = position + 1
    if had_colour and not result.endswith(RESET):
        result = result + RESET
    return result


TRUE_COLOUR = re.compile(r"\x1b\[([34])8;2;(\d+);(\d+);(\d+)m")


def nearest_256(red, green, blue):
    """Return the number (16 to 255) of the colour in the 256-colour table closest to (red, green, blue)."""
    if red == green == blue:
        # The 24 greys of the table (232 to 255), plus pure black and white.
        if red < 8:
            return 16
        if red > 248:
            return 231
        return 232 + round((red - 8) / 247 * 24)
    return 16 + 36 * round(red / 255 * 5) + 6 * round(green / 255 * 5) + round(blue / 255 * 5)


def to_256(text):
    """Return `text` with 24-bit colour codes changed to 256-colour codes.

    The pixel art uses 24-bit colour, which macOS Terminal.app does not have.
    Everything else in the text is left as it is.
    """
    def replace(match):
        number = nearest_256(int(match.group(2)), int(match.group(3)), int(match.group(4)))
        return f"\x1b[{match.group(1)}8;5;{number}m"

    return TRUE_COLOUR.sub(replace, text)
