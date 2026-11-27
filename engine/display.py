"""The full-screen display: every answer of the game drawn as a screen.

A screen is the HUD (where you are, your stars and coins), a body, a status
line, and the row where the player types (see render/screen.py). The body
is made of framed panels: STORY, TIPS, CODE, RESULTS. Pixel art (the map,
the boss, the level-clear animation) is drawn as it is.

On top of that the display plays the animations: the story types itself out
(Enter skips it), Snek reacts next to the results, the level-clear screen
counts stars and coins, and the combo flashes in the HUD.

Time (`sleep`), the Enter key (`skipped`) and the window (`size`) are given
to the display, so tests use a fake terminal and no real time passes. This
module is only used in the full-screen mode; the plain mode writes text.
"""

import re
import time

from engine.code_mode import show_wave
from engine.footer import footer_for
from engine.screens import PAGE_BREAK, SKIP_WORDS, split_screens
from engine.hud import hud_info
from engine.terminal import Fullscreen, terminal_size
from render.ansi import strip_ansi, to_256, visible_length
from render.hud import hud_lines
from render.panel import panel, wrap_lines
from render.reactions import load_reaction_art, reaction_lines, side_by_side
from render.screen import (
    MIN_COLUMNS,
    MIN_ROWS,
    WIDTH,
    body_height,
    compose_screen,
    draw_commands,
    paginate,
    too_small_message,
)
from render.title_art import load_title_art, title_frames
from render.typewriter import play_frames, typewriter_frames

# Seconds between the frames of an animation, of typing, and of a combo flash.
FRAME_DELAY = 0.08
TYPE_DELAY = 0.025
FLASH_DELAY = 0.12
FLASH_COUNT = 3

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


class Display:
    """Draws the game in full-screen mode.

    Attributes:
        state: the GameState, for the HUD.
        fullscreen: the Fullscreen that enters and leaves the alternate screen.
        last_frame: the rows last drawn, so they can be drawn again.
    """

    def __init__(self, state, write, size=terminal_size, sleep=time.sleep, skipped=lambda: False,
                 read_line=input, truecolor=True, delay=FRAME_DELAY, type_delay=TYPE_DELAY):
        """Remember how to write, measure, wait, read; `delay` 0 switches the animations off."""
        self.state = state
        self.raw_write = write
        self.size = size
        self.sleep = sleep
        self.skipped = skipped
        self.read_line = read_line
        self.truecolor = truecolor
        self.delay = delay
        self.type_delay = type_delay
        self.fullscreen = Fullscreen(write)
        self.last_frame = None
        self.reactions = None
        # Off on the title screen; the game switches it on.
        self.show_footer = False

    # ---- starting, stopping, writing

    def start(self):
        """Switch to the alternate screen."""
        self.fullscreen.enter()

    def stop(self):
        """Switch back to the player's own screen."""
        self.fullscreen.leave()

    def write(self, text):
        """Write to the terminal, in 256 colours if the terminal has no 24-bit colour."""
        if not self.truecolor:
            text = to_256(text)
        self.raw_write(text)

    def animating(self):
        """Return True if animations are on."""
        return self.delay > 0

    # ---- drawing a frame

    def hud(self, flash=False):
        """Return the two HUD lines."""
        return hud_lines(hud_info(self.state, flash), WIDTH, color=True)

    def draw(self, body, status=""):
        """Draw a whole screen: the HUD, `body` (a list of lines) and a status line."""
        columns, rows = self.size()
        if columns < MIN_COLUMNS or rows < MIN_ROWS:
            self.write("\x1b[2J\x1b[H" + too_small_message(columns, rows))
            self.last_frame = None
            return
        frame = self.frame(body, status, rows)
        self.last_frame = frame
        self.write(draw_commands(frame))

    def frame(self, body, status, rows):
        """Return the rows of a screen with a row left for typing."""
        footer = ""
        if self.show_footer:
            footer = footer_for(self.state)
        return compose_screen(self.hud(), body, status, rows, footer)

    def redraw(self):
        """Draw the last screen again (after the player pressed Enter, which scrolls the window)."""
        if self.last_frame is not None:
            self.write(draw_commands(self.last_frame))

    def height(self):
        """Return how many rows the body has."""
        return body_height(self.size()[1])

    # ---- reading

    def read(self, read_line, prompt):
        """Move to the typing row, read a line with `read_line(prompt)`, then redraw the screen."""
        rows = self.size()[1]
        self.write(f"\x1b[{rows};1H\x1b[K")
        line = read_line(prompt)
        self.redraw()
        return line

    def wait_for_enter(self):
        """Wait until the player presses Enter."""
        self.read(self.read_line, "")

    # ---- showing answers

    def show(self, answer):
        """Show what a command answered: a text, or a list of frames to animate.

        Returns a line typed at a pause that still has to be handled, or None.
        """
        if isinstance(answer, list):
            return self.show_animation(answer)
        if PAGE_BREAK in answer:
            return self.show_screens(split_screens(answer))
        if answer == "":
            self.show_nothing_new()
        elif self.state.coding and self.is_short_message(answer):
            self.show_wave_with_status(answer)
        else:
            self.show_text(answer)
        return None

    def show_screens(self, screens):
        """Show screens one at a time; return a line typed at a pause, or None."""
        typed = ""
        for screen in screens[:-1]:
            self.show_text(screen, status="Enter to continue (s skips)")
            typed = self.read(self.read_line, "")
            if typed.strip() != "":
                break
        # A boss's task was on the first screen, so its code gets the whole room.
        level = self.state.find_level(self.state.current_level)
        if level is not None and level.boss and self.state.coding and screens[-1] == show_wave(self.state):
            self.draw(self.typing_page())
        else:
            self.show_text(screens[-1])
        if typed.strip().lower() in [""] + SKIP_WORDS:
            return None
        return typed

    def show_nothing_new(self):
        """After a line with no answer: while coding, the code (with the new line); else the same screen."""
        if self.state.coding and self.state.find_level(self.state.current_level) is not None:
            self.draw(self.typing_page())
        else:
            self.redraw()

    def typing_page(self):
        """Return the page to show while the player types: never one that needs Enter.

        A wave too tall for the window is shown without its task paragraph,
        and if it is still too tall, its end, where the player is typing.
        """
        text = show_wave(self.state)
        pages = self.pages_for(split_sections(text))
        if len(pages) > 1:
            pages = self.pages_for(split_sections(show_wave(self.state, compact=True)))
        return pages[-1]

    def is_short_message(self, text):
        """Return True for a one or two line note, which goes to the status line."""
        lines = text.split("\n")
        if len(lines) > 2 or is_pixel_art(text):
            return False
        sections = split_sections(text)
        return len(sections) == 1 and sections[0][0] == "SNEK" and visible_length(text) <= WIDTH - 2

    def show_wave_with_status(self, message):
        """Draw the code of the wave, with `message` on the status line."""
        self.draw(self.typing_page(), status=message.replace("\n", " "))

    def results_panel(self, lines):
        """Return the RESULTS panel, with Snek's reaction beside the text."""
        text = "\n".join(lines)
        face = "happy"
        if "✗" in text:
            face = "dizzy"
        if "CLEARED." in text:
            face = "celebrate"
        if self.reactions is None:
            self.reactions = load_reaction_art()
        title, body = title_and_body("RESULTS", lines)
        beside = side_by_side(wrap_lines(body, RESULTS_TEXT_WIDTH), reaction_lines(face, self.reactions),
                              RESULTS_TEXT_WIDTH, gap=2)
        return panel(title, beside, WIDTH)

    def panels_for(self, sections):
        """Return the framed panels (each a list of lines) for the sections, in order."""
        panels = []
        for title, lines in sections:
            if title == "RESULTS":
                panels.append(self.results_panel(lines))
            else:
                heading, body = title_and_body(title, lines)
                panels.extend(framed(heading, body, self.height()))
        return panels

    def pages_for(self, sections):
        """Return the pages for the sections.

        A story is a page of its own (you read it and press Enter), so the
        tips and the first wave share the next page, and the player can start
        typing right away.
        """
        if sections[0][0] == "STORY" and len(sections) > 1:
            story = make_pages(self.panels_for(sections[:1]), self.height())
            rest = make_pages(self.panels_for(sections[1:]), self.height())
            return story + rest
        return make_pages(self.panels_for(sections), self.height())

    def show_text(self, text, status=""):
        """Show a text as panels (or as pixel art), page by page; `status` goes with the last."""
        if is_pixel_art(text):
            pages = paginate(text.split("\n"), self.height())
        else:
            sections = split_sections(text)
            if sections[0][0] == "STORY" and self.animating():
                self.type_story(sections[0][1])
            pages = self.pages_for(sections)
        for number in range(len(pages)):
            last = number == len(pages) - 1
            if last:
                self.draw(pages[number], status=status)
            else:
                self.draw(pages[number], status="Press Enter for more")
                self.wait_for_enter()

    def type_story(self, lines):
        """Type the story out in its panel, letter by letter; Enter skips to the end."""
        heading, body = title_and_body("STORY", lines)
        text = "\n".join(body)
        full_height = len(wrap_lines(body, WIDTH - 4))

        def show_prefix(prefix):
            typed = wrap_lines(prefix.split("\n"), WIDTH - 4)
            while len(typed) < full_height:
                typed.append("")
            self.draw(panel(heading, typed, WIDTH))

        self.fullscreen.hide_cursor()
        play_frames(typewriter_frames(text, step=3), show_prefix, self.sleep, self.skipped, self.type_delay)
        self.fullscreen.show_cursor()

    def show_animation(self, frames):
        """Play a list of frames; then show the message that came with the last one."""
        art, message = split_art_and_message(frames[-1])
        shown = list(frames[:-1]) + [art]
        self.fullscreen.hide_cursor()
        play_frames(shown, lambda frame: self.draw(frame.split("\n")), self.sleep, self.skipped, self.delay)
        self.fullscreen.show_cursor()
        if message:
            self.draw(self.last_body(shown[-1]), status="Press Enter to continue")
            self.wait_for_enter()
            return self.show(message)
        return None

    def last_body(self, frame):
        """Return the lines of a frame, cut to the room there is."""
        return frame.split("\n")[:self.height()]

    # ---- the combo, the title

    def after_command(self, combo_before):
        """Flash the combo in the HUD if the last command raised it."""
        if self.state.combo <= combo_before or not self.animating():
            return
        for _ in range(FLASH_COUNT):
            for flash in (True, False):
                self.write(draw_commands(hud_lines(hud_info(self.state, flash), WIDTH, color=True)))
                self.sleep(FLASH_DELAY)

    def show_title(self):
        """Play the title animation (the logo, Snek slithering in) and wait for Enter.

        If the player pressed Enter during the animation, that was the Enter: nothing more is waited for.
        """
        art = load_title_art()
        frames = title_frames(art)
        self.fullscreen.hide_cursor()
        skipped = play_frames(frames, lambda frame: self.draw(frame.split("\n")), self.sleep,
                              self.skipped, self.delay)
        self.fullscreen.show_cursor()
        if not skipped:
            self.wait_at_title()

    def wait_at_title(self):
        """Wait for Enter on the finished title screen."""
        self.wait_for_enter()
