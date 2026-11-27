"""Draw the stored digits of one or two numbers, for the approx power-up.

    APPROX
    you see       0.30000000000000004
    stored        0.3000000000000000444089209850062616169452667236328125
"""

import math
from decimal import Decimal

LABEL_WIDTH = 14
DIGITS_PER_LINE = 58
MAX_PLAIN_DIGITS = 150      # a longer number is shown with an exponent (E)


def stored_digits(value):
    """Return every digit of the number as it is stored."""
    exact = Decimal(value)
    if exact.is_finite():
        plain = format(exact, "f")
        if len(plain) <= MAX_PLAIN_DIGITS:
            return plain
    return str(exact)


def labelled(label, text):
    """Return the lines of one labelled value; a long one goes on to more lines."""
    lines = []
    for start in range(0, len(text), DIGITS_PER_LINE):
        lines.append(f"{label:<{LABEL_WIDTH}}{text[start:start + DIGITS_PER_LINE]}")
        label = ""
    return lines


def approx_view(values):
    """Return the drawing for a list of one or two numbers."""
    lines = ["APPROX"]
    if len(values) == 1:
        lines.extend(labelled("you see", repr(values[0])))
        lines.extend(labelled("stored", stored_digits(values[0])))
        return "\n".join(lines)
    left, right = values
    for side, value in [("left", left), ("right", right)]:
        lines.extend(labelled(side + " you see", repr(value)))
        lines.extend(labelled(side + " stored", stored_digits(value)))
    lines.extend(labelled("==", str(left == right)))
    lines.extend(labelled("math.isclose", str(math.isclose(left, right))))
    try:
        lines.extend(labelled("difference", repr(abs(left - right))))
    except OverflowError:
        pass
    return "\n".join(lines)
