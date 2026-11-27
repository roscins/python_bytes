"""Draw the editor: numbered, coloured code with a cursor and the failing line marked.

A frame is a list of lines, each exactly `width` cells wide:

    ┌─ WAVE 1 of 3 · FILL-IN ──────────┐
    │   1 │ print(___)                 │
    └──────────────────────────────────┘

The cursor is one cell in reverse video. A line with an error has a red
background, and a ^ is drawn under the column.
"""

from render.ansi import pad
from render.highlight import STYLES, find_spans
from render.panel import BOX

RESET = "\x1b[0m"
CURSOR = "7"
ERROR_BACKGROUND = "48;5;52"
ERROR_MARK = "\x1b[91m"

# "  1 │ " before the code of each line.
GUTTER = 6


class Mark:
    """Where an error is: the row and, if known, the column (both from 0)."""

    def __init__(self, row, column=None):
        """Remember the place."""
        self.row = row
        self.column = column


class View:
    """Which part of the text is on screen.

    Attributes:
        top: the first row shown.
        left: the first column shown.
    """

    def __init__(self):
        """Start at the beginning."""
        self.top = 0
        self.left = 0

    def follow(self, row, column, height, width):
        """Scroll just enough that (row, column) can be seen, and not under a < or >."""
        if row < self.top:
            self.top = row
        if row >= self.top + height:
            self.top = row - height + 1
        if column <= self.left:
            self.left = max(0, column - 1)
        if column >= self.left + width - 1:
            self.left = column - width + 2


def line_styles(lines):
    """Return for every line a list with the colour of each character ("" for none)."""
    spans = find_spans("\n".join(lines), lines)
    styles = []
    for index in range(len(lines)):
        colours = [""] * len(lines[index])
        for first, last, kind in spans.get(index + 1, []):
            for column in range(first, min(last, len(colours))):
                colours[column] = STYLES[kind]
        styles.append(colours)
    return styles


def paint_cell(character, colour, cursor, marked):
    """Return one character with its colour, the error background and the cursor."""
    codes = []
    if colour:
        codes.append(colour)
    if marked:
        codes.append(ERROR_BACKGROUND)
    if cursor:
        codes.append(CURSOR)
    if not codes:
        return character
    return f"\x1b[{';'.join(codes)}m{character}{RESET}"


def paint_part(line, colours, left, width, cursor=None, marked=False):
    """Return `width` cells of `line` from column `left`; < and > say there is more."""
    cells = []
    for column in range(left, left + width):
        character = " "
        colour = ""
        if column < len(line):
            character = line[column]
            colour = colours[column]
        if column == left and left > 0 and line:
            character = "<"
        if column == left + width - 1 and len(line) > left + width:
            character = ">"
        cells.append(paint_cell(character, colour, column == cursor, marked))
    return "".join(cells)


def code_rows(lines, view, height, width, cursor=None, mark=None, follow=None):
    """Return `height` rows of numbered code.

    `cursor` is (row, column) or None. The view scrolls to keep `follow` on
    screen, or the cursor if `follow` is None. The row with the ^ takes one
    of the rows.
    """
    code_width = width - GUTTER
    room = height
    if mark is not None and mark.column is not None:
        room = height - 1
    if follow is None:
        follow = cursor
    if follow is not None:
        view.follow(follow[0], follow[1], room, code_width)
    view.top = max(0, min(view.top, len(lines) - 1))
    styles = line_styles(lines)
    rows = []
    row = view.top
    while len(rows) < height and row < len(lines):
        at = None
        if cursor is not None and cursor[0] == row:
            at = cursor[1]
        marked = mark is not None and mark.row == row
        code = paint_part(lines[row], styles[row], view.left, code_width, at, marked)
        rows.append(f"{row + 1:>3} │ {code}")
        if marked and mark.column is not None and len(rows) < height:
            under = max(0, mark.column - view.left)
            rows.append(f"    │ {' ' * min(under, code_width - 1)}{ERROR_MARK}^{RESET}")
        row = row + 1
    while len(rows) < height:
        rows.append("")
    return rows


def divider(title, width):
    """Return a rule with a title inside a frame, for example "── YOUR ANSWER ───"."""
    head = f"{BOX['h']} {title} "
    return head + BOX["h"] * (width - len(head))


def frame(title, rows, width):
    """Return `rows` (already cut to width - 4 cells) inside a box with `title`."""
    inner = width - 2
    head = f"{BOX['h']} {title} "
    lines = [BOX["tl"] + head + BOX["h"] * (inner - len(head)) + BOX["tr"]]
    for row in rows:
        lines.append(BOX["v"] + pad(" " + row, inner) + BOX["v"])
    lines.append(BOX["bl"] + BOX["h"] * inner + BOX["br"])
    return lines
