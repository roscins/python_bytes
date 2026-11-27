"""Expected output and the player's output side by side, with the first difference marked.

    EXPECTED          YOURS
    SNEK ONLINE     > Snek online
                       ^
"""

COLUMN = 32             # the widest line that fits in a column
MAX_ROWS = 10
LABEL_ROW = "YOURS"


def first_difference(expected, printed):
    """Return (line index, column) of the first difference, or None if the texts are equal."""
    for index in range(max(len(expected), len(printed))):
        left = expected[index] if index < len(expected) else None
        right = printed[index] if index < len(printed) else None
        if left == right:
            continue
        if left is None or right is None:
            return index, 0
        column = 0
        while column < min(len(left), len(right)) and left[column] == right[column]:
            column = column + 1
        return index, column
    return None


def window(lines, first):
    """Return (start, end) of the rows to show, so the first difference is among them."""
    start = max(0, first - MAX_ROWS // 2)
    return start, min(len(lines), start + MAX_ROWS)


def compare_lines(expected_text, printed_text):
    """Return the lines that compare two outputs. Both are already tidied up."""
    expected = expected_text.split("\n") if expected_text else []
    printed = printed_text.split("\n") if printed_text else []
    difference = first_difference(expected, printed)
    if difference is None:
        return []
    row, column = difference
    start, end = window([""] * max(len(expected), len(printed)), row)
    # Long lines do not fit side by side: they go one under the other.
    side_by_side = max([len(line) for line in expected + printed] + [0]) <= COLUMN
    lines = []
    if side_by_side:
        lines.append(f"{'EXPECTED':<{COLUMN}}   {LABEL_ROW}")
    for index in range(start, end):
        left = expected[index] if index < len(expected) else "(no line)"
        right = printed[index] if index < len(printed) else "(no line)"
        mark = ">" if index == row else " "
        if side_by_side:
            lines.append(f"{left:<{COLUMN}} {mark} {right}".rstrip())
            if index == row:
                lines.append(" " * (COLUMN + 3 + column) + "^")
        elif index == row:
            lines.append(f"expected: {left}")
            lines.append(f"yours:    {right}")
            lines.append(" " * (10 + column) + "^")
    lines.append(f"First difference: line {row + 1}, character {column + 1}.")
    return lines
