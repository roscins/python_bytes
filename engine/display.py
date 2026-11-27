"""Turning a command's answer into framed panels and pages, for the full screen.

The body of a screen is made of framed panels: STORY, TIPS, CODE, RESULTS.
Pixel art (the map, the boss, the level-clear animation) is drawn as it is.
These functions only work on text; engine/key_display.py draws the result.
"""

import re

from render.panel import panel, wrap_lines
from render.screen import WIDTH, paginate

# The width of the text beside Snek in the results panel: the panel's inner
# width (76), minus Snek (16) and the gap (2).
RESULTS_TEXT_WIDTH = 58

PIXEL_ART_CHARACTERS = "▀▄"


RESULTS_LINE = re.compile(r"^LEVEL \S+ · RESULTS$")
STORY_LINE = re.compile(r"^LEVEL \d+-\d+ · ")
WAVE_LINE = re.compile(r"^WAVE \d+ of \d+ · ")


def section_title(line):
    """Return the panel title for a line that starts a section, or None if it does not start one.

    The patterns are exact, because the results also have lines like
    "WAVE 1 · FILL-IN  2/2 tests passed" and "LEVEL SCORE 100 %" that must
    stay inside the results.
    """
    if line == "PYTHON BYTES":
        return "MENU"
    if line == "TIPS":
        return "TIPS"
    if line == "BOSS WAVE" or WAVE_LINE.match(line):
        return "CODE"
    if RESULTS_LINE.match(line):
        return "RESULTS"
    if STORY_LINE.match(line):
        return "STORY"
    return None


def split_sections(text):
    """Cut an answer into sections: a list of (panel title, lines).

    A section starts at the first line, or at a line after a blank line,
    that looks like the start of one (a level title, TIPS, a wave, results).
    Text that starts no section is a note, titled SNEK.
    """
    sections = []
    previous_blank = True
    for line in text.split("\n"):
        title = None
        if previous_blank:
            title = section_title(line)
        if title is not None:
            sections.append((title, [line]))
        elif sections:
            sections[-1][1].append(line)
        else:
            sections.append(("SNEK", [line]))
        previous_blank = line.strip() == ""
    cleaned = []
    for title, lines in sections:
        while lines and lines[-1].strip() == "":
            lines.pop()
        cleaned.append((title, lines))
    return cleaned


def title_and_body(kind, lines):
    """Return (panel title, body lines) for a section: its own heading becomes the title.

    "WAVE 1 of 3 · FILL-IN" is a better title than "CODE", and a heading
    repeated inside the box would say the same thing twice.
    """
    if kind in ("STORY", "CODE", "RESULTS"):
        return lines[0], strip_leading_blanks(lines[1:])
    if kind == "TIPS":
        return "TIPS", lines[1:]
    if kind == "MENU":
        return lines[0], strip_leading_blanks(lines[2:])
    return kind, lines


def strip_leading_blanks(lines):
    """Return `lines` without the empty lines at the start."""
    start = 0
    while start < len(lines) and lines[start].strip() == "":
        start = start + 1
    return lines[start:]


def is_pixel_art(text):
    """Return True if the text holds pixel art, which needs the whole 80 cells."""
    for character in PIXEL_ART_CHARACTERS:
        if character in text:
            return True
    return False


def split_art_and_message(text):
    """Split a frame into the pixel art with the lines that belong to it, and the message after it.

    The art block ends at the first blank line after the last line of pixel
    art. Returns (art text, message text); the message may be empty.
    """
    lines = text.split("\n")
    last_art = -1
    for index in range(len(lines)):
        if is_pixel_art(lines[index]):
            last_art = index
    end = len(lines)
    for index in range(last_art + 1, len(lines)):
        if lines[index].strip() == "":
            end = index
            break
    message = "\n".join(lines[end:]).strip("\n")
    return "\n".join(lines[:end]), message


def framed(title, lines, height):
    """Return the panels for one section: one panel, or several if it is taller than a page.

    A tall section (the help text) is split in the middle of its text, and
    each part gets its own frame and title, so every page is a whole panel.
    """
    box = panel(title, lines, WIDTH)
    if len(box) <= height:
        return [box]
    boxes = []
    for chunk in paginate(wrap_lines(lines, WIDTH - 4), height - 2):
        boxes.append(panel(title, chunk, WIDTH))
    return boxes


def make_pages(panels, height):
    """Put whole panels on pages of at most `height` lines."""
    pages = []
    current = []
    for lines in panels:
        if current and len(current) + len(lines) > height:
            pages.append(current)
            current = []
        current.extend(lines)
    if current or not pages:
        pages.append(current)
    return pages
