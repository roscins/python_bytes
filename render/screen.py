"""The layout of the full screen, and the codes that draw it.

    rows 1-2        the HUD (see render/hud.py)
    row  3          a thin rule
    rows 4 ...      the body: panels, the map, the editor, animations
    row  rows - 2   the status line (a short message)
    row  rows - 1   the buttons
    row  rows       the keys that work (a typed command is also read here)

compose_screen() and key_screen() return the rows as a list of text; draw_commands() turns
them into escape codes that put each row at its place, so nothing scrolls.
Both are pure functions: no terminal is needed to test them.
"""

from render.ansi import fit, pad

WIDTH = 80
MIN_COLUMNS = 80
MIN_ROWS = 24

# HUD (2) + rule (1) + status (1) + buttons (1) + keys (1).
FIXED_ROWS = 6


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


def compose_screen(hud, body, status, rows, footer=""):
    """Return the frame: `rows - 1` rows, each exactly WIDTH cells wide.

    The last row of the window is left out: key_screen puts the keys there.
    A body that is taller than the room is cut; callers split long bodies
    with paginate first.
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
    frame.append(pad(fit(footer, WIDTH), WIDTH))
    return frame


def key_screen(hud, body, status, rows, buttons, keys_footer):
    """Return a screen of the key-driven mode: `rows` rows, with no row for typing.

    The buttons are on the row above the last one, and the last row says
    which keys work. It is not padded, so the window never scrolls.
    """
    frame = compose_screen(hud, body, status, rows, buttons)
    frame.append(fit(keys_footer, WIDTH - 1))
    return frame


def draw_commands(lines):
    """Return the escape codes that draw `lines` from the top row down, clearing each row's end."""
    parts = []
    for index in range(len(lines)):
        parts.append(f"\x1b[{index + 1};1H{lines[index]}\x1b[K")
    return "".join(parts)


def size_problem(columns, rows):
    """Say exactly what a too small window needs, or return "" if it is big enough."""
    if columns >= MIN_COLUMNS and rows >= MIN_ROWS:
        return ""
    needed = []
    if columns < MIN_COLUMNS:
        needed.append(f"{MIN_COLUMNS - columns} columns wider")
    if rows < MIN_ROWS:
        needed.append(f"{MIN_ROWS - rows} rows taller")
    return (f"Python Bytes needs a window of {MIN_COLUMNS} x {MIN_ROWS}; yours is {columns} x {rows}.\n"
            f"Make it {' and '.join(needed)}.\n"
            "Press Enter to check again, or type p to play in plain mode.")


def too_small_message(columns, rows):
    """Return the message for a window smaller than the game needs."""
    return (f"The window is {columns} x {rows}. Python Bytes needs at least "
            f"{MIN_COLUMNS} x {MIN_ROWS}. Make the window bigger, or start the game with --plain.")
