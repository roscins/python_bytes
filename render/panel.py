"""Framed panels: text inside a box drawn with box-drawing characters.

    ┌─ STORY ───────────────┐
    │ The lab is dark.      │
    └───────────────────────┘

Every line of a panel is exactly `width` cells wide, so panels line up.
With ascii_only the box is drawn with + - | for terminals that cannot show
the box characters.
"""

import textwrap

from render.ansi import fit, pad, visible_length

BOX = {"tl": "┌", "tr": "┐", "bl": "└", "br": "┘", "h": "─", "v": "│"}
ASCII_BOX = {"tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "-", "v": "|"}


def wrap_lines(lines, width):
    """Return `lines` with the long ones wrapped to `width` cells.

    A line with colour codes (highlighted code) is cut instead of wrapped,
    because wrapping would break its colours. A wrapped line keeps the
    indentation of its first line.
    """
    result = []
    for line in lines:
        if "\x1b" in line:
            result.append(fit(line, width))
        elif len(line) <= width:
            result.append(line)
        else:
            indent = " " * (len(line) - len(line.lstrip()))
            wrapped = textwrap.wrap(line, width=width, subsequent_indent=indent)
            result.extend(wrapped)
    return result


def panel(title, lines, width, ascii_only=False):
    """Return a framed panel as a list of lines, each exactly `width` cells wide."""
    box = ASCII_BOX if ascii_only else BOX
    inner = width - 2
    if title:
        head = box["h"] + " " + title + " "
        top = box["tl"] + head + box["h"] * (inner - len(head)) + box["tr"]
    else:
        top = box["tl"] + box["h"] * inner + box["tr"]
    result = [top]
    for line in wrap_lines(lines, width - 4):
        result.append(box["v"] + pad(" " + line, inner) + box["v"])
    result.append(box["bl"] + box["h"] * inner + box["br"])
    return result
