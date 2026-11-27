"""The full screen: every answer of the game drawn, and everything worked with keys.

A screen is the HUD (where you are, your stars and coins), a body, a status
line, a row of buttons and a row saying which keys work (see
render/screen.py). Only a typed command (`:` on the map, Ctrl-E in a wave)
is read as a line: for that the keyboard is switched back to normal.

On top of that the display plays the animations: the story types itself out
(Enter skips it), the level-clear screen counts stars and coins, and the
combo flashes in the HUD.

Time (`sleep`), the keyboard (`keys`) and the window (`size`) are given to
the display, so tests use fakes and no real time passes. The plain mode does
not use this module.
"""

import time

from engine.display import (
    RESULTS_TEXT_WIDTH,
    framed,
    is_pixel_art,
    make_pages,
    split_art_and_message,
    split_sections,
    title_and_body,
)
from engine.focus import Choice
from engine.hud import hud_info
from engine.progression_help import next_level_to_play
from engine.screens import PAGE_BREAK, split_screens
from engine.terminal import Fullscreen, terminal_size
from render.ansi import to_256
from render.buttons import button_row
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
    key_screen,
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

# How often a waiting screen looks whether the window changed size.
RESIZE_CHECK = 0.25

# The keys that move between the pages of a long text.
PREVIOUS_PAGE = ["up", "page-up"]
NEXT_PAGE = ["down", "page-down"]


class KeyDisplay:
    """Draws the game and reads single keys.

    Attributes:
        state: the GameState, for the HUD.
        keys: the keyboard (see engine/keys.py).
        guard: the ShutdownGuard, so a stop signal can end the waiting.
        fullscreen: the Fullscreen that enters and leaves the alternate screen.
        buttons: the button row of the screen being drawn, or None before there is one.
        last_frame: the rows last drawn, so they can be drawn again.
    """

    def __init__(self, state, write, keys, size=terminal_size, sleep=time.sleep, read_line=input,
                 truecolor=True, delay=FRAME_DELAY, type_delay=TYPE_DELAY):
        """Remember how to write, read keys, measure and wait; `delay` 0 switches animations off."""
        self.state = state
        self.raw_write = write
        self.keys = keys
        self.size = size
        self.sleep = sleep
        self.read_line = read_line
        self.truecolor = truecolor
        self.delay = delay
        self.type_delay = type_delay
        self.fullscreen = Fullscreen(write)
        self.last_frame = None
        self.reactions = None
        self.guard = None
        self.buttons = None
        self.keys_footer = ""
        self.message = ""
        self.body = []

    # ---- starting, stopping, writing

    def start(self):
        """Switch the keyboard to single keys and go to the alternate screen."""
        self.keys.start()
        self.fullscreen.enter()
        self.fullscreen.hide_cursor()

    def stop(self):
        """Switch back to the player's own screen and put the keyboard back."""
        self.fullscreen.leave()
        self.keys.stop()

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

    def height(self):
        """Return how many rows the body has."""
        return body_height(self.size()[1])

    def draw(self, body, status=""):
        """Draw a whole screen: the HUD, `body` (a list of lines) and a status line."""
        columns, rows = self.size()
        if columns < MIN_COLUMNS or rows < MIN_ROWS:
            self.write("\x1b[2J\x1b[H" + too_small_message(columns, rows))
            self.last_frame = None
            return
        if self.buttons is None:
            frame = compose_screen(self.hud(), body, status, rows)
        else:
            frame = key_screen(self.hud(), body, status, rows, self.buttons, self.keys_footer)
        self.last_frame = frame
        self.write(draw_commands(frame))

    def redraw(self):
        """Draw the last screen again (after a typed line, which scrolls the window)."""
        if self.last_frame is not None:
            self.write(draw_commands(self.last_frame))

    def draw_buttons(self, body, labels, chosen, footer, status=""):
        """Draw a screen with `body`, a row of buttons and the keys that work."""
        self.body = body
        self.message = status
        self.buttons = button_row(labels, chosen)
        self.keys_footer = footer
        self.fullscreen.hide_cursor()
        self.draw(body, status)

    # ---- reading keys and lines

    def skip_pressed(self):
        """Return True if Enter or Esc is among the keys pressed during an animation."""
        found = False
        key = self.keys.read_key(0)
        while key is not None:
            if key in ("enter", "escape"):
                found = True
            key = self.keys.read_key(0)
        return found

    def poll_key(self):
        """Return the next key, or None if none came within a short while."""
        if self.guard is None:
            return self.keys.read_key(RESIZE_CHECK)
        # A signal that came while the screen was drawn only set a flag.
        self.guard.stop_if_requested()
        return self.guard.read_input(self.keys.read_key, RESIZE_CHECK)

    def wait_key(self):
        """Wait for a key, drawing the screen again if the window changes size."""
        size = self.size()
        while True:
            key = self.poll_key()
            if key is not None:
                return key
            if self.size() != size:
                size = self.size()
                self.write("\x1b[2J")
                self.draw(self.body, self.message)

    def read(self, read_line, prompt):
        """Read a typed line on the last row, with the keyboard back to normal."""
        rows = self.size()[1]
        self.buttons = None
        self.keys.stop()
        try:
            self.write(f"\x1b[{rows};1H\x1b[K")
            self.fullscreen.show_cursor()
            line = read_line(prompt)
        finally:
            self.keys.start()
        self.redraw()
        return line

    # ---- pauses

    def browse(self, pages, labels=("Continue",), footer="Enter continue", status="", escape=False):
        """Show pages until the player is done; return the button pressed, or "escape".

        Enter goes to the next page, and on the last page presses the chosen
        button. Up and Down also move between pages. With `escape`, Esc
        leaves at once.
        """
        choice = Choice(labels)
        number = 0
        while True:
            last = number == len(pages) - 1
            if len(pages) == 1:
                self.draw_buttons(pages[0], labels, choice.index, footer, status)
            elif last:
                self.draw_buttons(pages[number], labels, choice.index, "↑↓ pages · " + footer, status)
            else:
                self.draw_buttons(pages[number], ["More"], 0, "↑↓ pages · Enter more", status)
            key = self.wait_key()
            if key == "enter" and last:
                return choice.label()
            if key == "escape" and escape:
                return "escape"
            if key == "ctrl-d":
                raise EOFError
            if key == "enter" or key in NEXT_PAGE:
                number = min(number + 1, len(pages) - 1)
            elif key in PREVIOUS_PAGE:
                number = max(number - 1, 0)
            elif last:
                choice.move(key)

    def wait_for_enter(self):
        """Keep the body as it is, with a Continue button, until Enter."""
        self.browse([self.body_on_screen()])

    def body_on_screen(self):
        """Return the body of the last drawn frame (the rows between the rule and the status)."""
        if self.last_frame is None:
            return []
        return self.last_frame[3:3 + self.height()]

    # ---- panels and pages

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
        """Return the pages for the sections; a story is a page of its own."""
        if sections[0][0] == "STORY" and len(sections) > 1:
            story = make_pages(self.panels_for(sections[:1]), self.height())
            rest = make_pages(self.panels_for(sections[1:]), self.height())
            return story + rest
        return make_pages(self.panels_for(sections), self.height())

    def pages_of(self, text):
        """Return the pages of one screen of text."""
        if is_pixel_art(text):
            return paginate(text.split("\n"), self.height())
        return self.pages_for(split_sections(text))

    # ---- showing answers

    def show(self, answer):
        """Show an answer: a text, or a list of frames. Return a command chosen with a button, or None."""
        if isinstance(answer, list):
            return self.show_animation(answer)
        return self.show_text(answer)

    def show_screens(self, screens):
        """Show screens one at a time; Esc skips to the last one."""
        for screen in screens[:-1]:
            if split_sections(screen)[0][0] == "STORY" and self.animating():
                self.type_story(split_sections(screen)[0][1])
            pressed = self.browse(self.pages_of(screen), footer="Enter continue · Esc skip", escape=True)
            if pressed == "escape":
                break
        last = screens[-1]
        if self.state.coding:
            # The wave screen draws the wave itself (see engine/wave_screen.py).
            return None
        # At the map, the map screen itself comes next.
        if is_pixel_art(last):
            return None
        return self.show_text(last)

    def show_text(self, text):
        """Show a text as pages and wait. In a wave nothing is shown: its screen does that."""
        if PAGE_BREAK in text:
            return self.show_screens(split_screens(text))
        if self.state.coding or not self.state.running:
            return None
        return self.wait_at_the_end(text, self.pages_of(text))

    def wait_at_the_end(self, text, pages):
        """Wait on a text shown at the map; return the command a button stands for, or None."""
        following = next_level_to_play(self.state)
        if following is not None and f"Next: play {following.id}" in text:
            pressed = self.browse(pages, labels=["Next level", "Map"], footer="←→ choose · Enter")
            if pressed == "Next level":
                return f"play {following.id}"
            return None
        self.browse(pages)
        return None

    # ---- animations

    def type_story(self, lines):
        """Type the story out in its panel, letter by letter; Enter skips to the end."""
        heading, body = title_and_body("STORY", lines)
        text = "\n".join(body)
        full_height = len(wrap_lines(body, WIDTH - 4))

        def show_prefix(prefix):
            """Draw the story as far as it has been typed."""
            typed = wrap_lines(prefix.split("\n"), WIDTH - 4)
            while len(typed) < full_height:
                typed.append("")
            self.draw(panel(heading, typed, WIDTH))

        self.fullscreen.hide_cursor()
        play_frames(typewriter_frames(text, step=3), show_prefix, self.sleep, self.skip_pressed,
                    self.type_delay)
        self.fullscreen.show_cursor()

    def show_animation(self, frames):
        """Play a list of frames; then show the message that came with the last one."""
        art, message = split_art_and_message(frames[-1])
        shown = list(frames[:-1]) + [art]
        self.fullscreen.hide_cursor()
        play_frames(shown, lambda frame: self.draw(frame.split("\n")), self.sleep, self.skip_pressed,
                    self.delay)
        self.fullscreen.show_cursor()
        if message:
            self.draw(self.last_body(shown[-1]))
            self.wait_for_enter()
            return self.show(message)
        return None

    def last_body(self, frame):
        """Return the lines of a frame, cut to the room there is."""
        return frame.split("\n")[:self.height()]

    def play(self, frames, wait=True):
        """Play an animation; with `wait`, stay on its last picture until Enter."""
        self.buttons = button_row([])
        self.keys_footer = ""
        play_frames(frames, lambda picture: self.draw(picture.split("\n")), self.sleep, self.skip_pressed,
                    self.delay)
        if wait:
            self.browse([self.last_body(frames[-1])])

    def after_command(self, combo_before):
        """Flash the combo in the HUD if the last command raised it."""
        if self.state.combo <= combo_before or not self.animating():
            return
        for _ in range(FLASH_COUNT):
            for flash in (True, False):
                self.write(draw_commands(hud_lines(hud_info(self.state, flash), WIDTH, color=True)))
                self.sleep(FLASH_DELAY)

    # ---- the title

    def show_title(self):
        """Play the title animation (the logo, Snek slithering in) and wait for Enter.

        If the player pressed Enter during the animation, that was the Enter: nothing more is waited for.
        """
        self.buttons = button_row([])
        self.keys_footer = "Enter start"
        frames = title_frames(load_title_art())
        self.fullscreen.hide_cursor()
        skipped = play_frames(frames, lambda frame: self.draw(frame.split("\n")), self.sleep,
                              self.skip_pressed, self.delay)
        self.fullscreen.show_cursor()
        if not skipped:
            self.wait_at_title()

    def wait_at_title(self):
        """Wait for Enter on the title; Ctrl-D or the end of input go on to the menu, which quits."""
        self.draw(self.body_on_screen())
        try:
            while self.wait_key() not in ("enter", "ctrl-d"):
                pass
        except EOFError:
            return
