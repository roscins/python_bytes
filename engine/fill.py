"""Fill-in waves: the player types only what goes in the blank.

While a fill-in wave still has a ___ , a typed line fills the next blank. A
player who types the whole line out of habit is understood too.
"""

import re

BLANK = "___"


def has_blanks_to_fill(wave):
    """Return True for a fill-in wave whose starter has blanks."""
    return wave.kind == "fill-in" and wave.starter is not None and BLANK in wave.starter


def is_filling(wave, text):
    """Return True while the code of a fill-in wave still has a blank."""
    return has_blanks_to_fill(wave) and BLANK in text


def line_pattern(line):
    """Return a pattern that matches `line` with anything in place of its blanks."""
    pieces = [re.escape(piece) for piece in line.strip().split(BLANK)]
    return "(.+?)".join(pieces)


def filled_line(line, typed):
    """Return `line` (which has a blank) filled in with what the player typed."""
    indent = line[:len(line) - len(line.lstrip())]
    match = re.fullmatch(line_pattern(line), typed.strip())
    if match and line.strip() != BLANK:
        # The whole line was typed.
        return indent + typed.strip()
    return line.replace(BLANK, typed.strip(), 1)


def fill_next_blank(text, typed):
    """Return `text` with its first blank filled from `typed`."""
    lines = text.splitlines()
    for index in range(len(lines)):
        if BLANK in lines[index]:
            lines[index] = filled_line(lines[index], typed)
            break
    return "\n".join(lines) + "\n"


def all_blanks_filled(wave, text):
    """Return True if `text` is the starter with every blank filled in, and nothing else changed."""
    if not has_blanks_to_fill(wave) or BLANK in text:
        return False
    starter = wave.starter.strip().splitlines()
    lines = text.strip().splitlines()
    if len(lines) != len(starter):
        return False
    return all(re.fullmatch(line_pattern(starter[index]), lines[index].strip())
               for index in range(len(lines)))


def blank_marker(text, wave, prefix_width):
    """Return (line index, marker line, question) for the next blank of `text`."""
    lines = text.splitlines()
    number = wave.starter.count(BLANK) - text.count(BLANK) + 1
    total = wave.starter.count(BLANK)
    for index in range(len(lines)):
        if BLANK in lines[index]:
            marker = " " * (prefix_width + lines[index].index(BLANK)) + "^" * len(BLANK)
            question = f"Blank {number} of {total}, line {index + 1}: what goes where the ^^^ are?"
            return index, marker, question
    return None
