"""The layout of the full screen, and the codes that draw it.

    rows 1-2        the HUD (see render/hud.py)
    row  3          a thin rule
    rows 4 ...      the body: panels, the map, animations
    row  rows - 1   the status line (a short message)
    row  rows       where the player types

compose_screen() returns the rows as a list of text; draw_commands() turns
them into escape codes that put each row at its place, so nothing scrolls.
Both are pure functions: no terminal is needed to test them.
"""

from render.ansi import fit, pad

WIDTH = 80
MIN_COLUMNS = 80
MIN_ROWS = 24

# HUD (2) + rule (1) + status (1) + the row where the player types (1).
FIXED_ROWS = 5


def body_height(rows):
    """Return how many rows the body has in a window with `rows` rows."""
    return rows - FIXED_ROWS


def paginate(lines, height):
    """Split `lines` into pages of at most `height` lines; there is always at least one page."""
    if not lines:
        return [[]]
    pages = []
    for start in range(0, len(lines), height):
        pages.append(lines[start:start + height])
    return pages


def compose_screen(hud, body, status, rows):
    """Return the frame: `rows - 1` rows, each exactly WIDTH cells wide.

    The last row of the window is left for the player's typing. A body that
    is taller than the room is cut; callers split long bodies with paginate
    first.
    """
    frame = []
    for line in hud:
        frame.append(pad(fit(line, WIDTH), WIDTH))
    frame.append("─" * WIDTH)
    height = body_height(rows)
    for index in range(height):
        line = ""
        if index < len(body):
            line = body[index]
        frame.append(pad(fit(line, WIDTH), WIDTH))
    frame.append(pad(fit(status, WIDTH), WIDTH))
    return frame


def draw_commands(lines):
    """Return the escape codes that draw `lines` from the top row down, clearing each row's end."""
    parts = []
    for index in range(len(lines)):
        parts.append(f"\x1b[{index + 1};1H{lines[index]}\x1b[K")
    return "".join(parts)


def too_small_message(columns, rows):
    """Return the message for a window smaller than the game needs."""
    return (f"The window is {columns} x {rows}. Python Bytes needs at least "
            f"{MIN_COLUMNS} x {MIN_ROWS}. Make the window bigger, or start the game with --plain.")
