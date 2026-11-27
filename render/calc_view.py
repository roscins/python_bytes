"""Draw the steps of a calculation, for the calc power-up.

    CALC
    2 + 3 * 4
        ~~~~~
    2 + 12
    ~~~~~~
    14
"""


def calc_view(steps, error=None):
    """Return the drawing of `steps`, a list of (line, start, end) to underline.

    A step with start == end has nothing underlined: it is the result. With
    an `error`, the last underlined part is where Python stops.
    """
    lines = ["CALC"]
    for line, start, end in steps:
        lines.append(line)
        if end > start:
            lines.append(" " * start + "~" * (end - start))
    if error is not None:
        lines.append(f"Python stops here: {type(error).__name__}: {error}")
    return "\n".join(lines)
