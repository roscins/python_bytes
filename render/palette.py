"""Read the colour palette from a text file and turn colours into ANSI codes.

A palette file has one colour per line:

    code red green blue name

for example "2 29 43 83 dark-blue". Lines that start with "#" are comments,
and blank lines are skipped.
"""

TRANSPARENT = "."


def load_palette(path):
    """Read a palette file and return a dict from code to (red, green, blue).

    Example: a line "2 29 43 83 dark-blue" gives the entry {"2": (29, 43, 83)}.
    Raises ValueError, naming the file and line, if a line is not valid.
    """
    palette = {}
    with open(path, encoding="utf-8") as palette_file:
        line_number = 0
        for line in palette_file:
            line_number = line_number + 1
            text = line.strip()
            if text == "" or text.startswith("#"):
                continue
            code, colour = parse_palette_line(text, f"{path}, line {line_number}")
            if code in palette:
                raise ValueError(f"{path}, line {line_number}: code {code} is used twice")
            palette[code] = colour
    return palette


def parse_palette_line(text, place):
    """Turn one palette line into a code and a (red, green, blue) colour.

    `place` says where the line came from, for error messages.
    """
    parts = text.split()
    if len(parts) != 5:
        raise ValueError(f"{place}: expected 'code red green blue name', got {text!r}")
    code = parts[0]
    if len(code) != 1 or code == TRANSPARENT:
        raise ValueError(f"{place}: the code must be one character other than '.'")
    numbers = []
    for part in parts[1:4]:
        if not part.isdigit() or int(part) > 255:
            raise ValueError(f"{place}: {part!r} is not a number from 0 to 255")
        numbers.append(int(part))
    red, green, blue = numbers
    return code, (red, green, blue)


def foreground(colour):
    """Return the escape code that sets the text colour to (red, green, blue)."""
    red, green, blue = colour
    return f"\x1b[38;2;{red};{green};{blue}m"


def background(colour):
    """Return the escape code that sets the background to (red, green, blue)."""
    red, green, blue = colour
    return f"\x1b[48;2;{red};{green};{blue}m"
