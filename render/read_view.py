"""Draw a text with its index numbers, for the read power-up.

    READ
    char    S  N  E  K
    index   0  1  2  3
    back   -4 -3 -2 -1
    [1:3]      ^  ^
    gives  'NE'
"""

CELL_WIDTH = 3          # characters of screen for one character of the text
LABEL_WIDTH = 7         # room for "index", "back" and a slice like "[0:5]"
BLOCK_SIZE = 20         # characters of the text on one row
MAX_WIDTH = 70          # a longer result is split over several lines


def shown_character(character, plain):
    """Return how one character is shown; spaces and line breaks are made visible."""
    if character == " ":
        return "_" if plain else "·"
    if character.isprintable():
        return character
    return repr(character)[1:-1][:CELL_WIDTH - 1]


def row(label, cells):
    """Return one row: the label, then every cell right-aligned in its column."""
    line = f"{label:<{LABEL_WIDTH}}"
    for cell in cells:
        line = line + f"{cell:>{CELL_WIDTH}}"
    return line.rstrip()


def selected_indexes(length, selection):
    """Return the indexes picked by a slice or one index (an empty list if there are none)."""
    if selection is None:
        return []
    if isinstance(selection, slice):
        return list(range(length))[selection]
    if -length <= selection < length:
        return [range(length)[selection]]
    return []


def result_line(text, selection):
    """Return the last line: what the selection gives, and the length."""
    if selection is None:
        return f"len = {len(text)}"
    if not isinstance(selection, slice) and not -len(text) <= selection < len(text):
        return f"IndexError: there is no index {selection}     len = {len(text)}"
    return f"gives  {text[selection]!r}     len = {len(text)}"


def read_view(text, selection, selection_text, plain=False):
    """Return the drawing of `text`, marking what `selection` picks.

    `selection` is None, an int or a slice; `selection_text` is what the
    player typed after the last "[", used as the label of the marks.
    """
    label = "[" + selection_text.strip()
    if len(label) >= LABEL_WIDTH:
        label = "picked"
    picked = selected_indexes(len(text), selection)
    lines = ["READ"]
    for start in range(0, len(text), BLOCK_SIZE):
        block = text[start:start + BLOCK_SIZE]
        indexes = range(start, start + len(block))
        if start > 0:
            lines.append("")
        lines.append(row("char", [shown_character(character, plain) for character in block]))
        lines.append(row("index", [str(index) for index in indexes]))
        lines.append(row("back", [str(index - len(text)) for index in indexes]))
        if any(index in picked for index in indexes):
            lines.append(row(label, ["^" if index in picked else "" for index in indexes]))
    result = result_line(text, selection)
    while len(result) > MAX_WIDTH:
        lines.append(result[:MAX_WIDTH])
        result = " " * LABEL_WIDTH + result[MAX_WIDTH:]
    lines.append(result)
    return "\n".join(lines)
