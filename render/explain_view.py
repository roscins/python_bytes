"""Draw a line of code with its parts marked, for the explain power-up.

    EXPLAIN
    print("HI")  # greet
    ^^^^^                 call: show something
          ^^^^            string: only text
                 ^^^^^^^  comment: Python skips it
    SCREEN: HI
"""

GAP = 2                 # spaces between the end of the line and the labels
SCREEN_WIDTH = 60


def explain_view(line, marks, screen):
    """Return the drawing of `line` with `marks`, a list of (start, end, label).

    `screen` is what the line shows, or None if only running it could tell.
    """
    lines = ["EXPLAIN", line]
    for start, end, label in marks:
        carets = " " * start + "^" * (end - start)
        lines.append(f"{carets:<{len(line) + GAP}}{label}")
    if screen is None:
        lines.append("SCREEN: explain runs nothing, so it cannot tell for this line.")
    elif screen == "":
        lines.append("SCREEN: (nothing)")
    else:
        for part in screen.split("\n"):
            lines.append("SCREEN: " + part[:SCREEN_WIDTH])
    return "\n".join(lines)
