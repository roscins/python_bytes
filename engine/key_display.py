"""The full-screen display for the key-driven mode.

It draws the same panels as Display, but everything is worked with single
keys. Only a typed command (`:` on the map, Ctrl-E in a wave) is read as a
line: for that the keyboard is switched back to normal.
"""

from engine.display import Display, is_pixel_art, split_sections
from engine.focus import Choice
from engine.progression_help import next_level_to_play
from engine.screens import PAGE_BREAK, split_screens
from render.buttons import button_row
from render.screen import compose_screen, key_screen, paginate
from render.typewriter import play_frames

# How often a waiting screen looks whether the window changed size.
RESIZE_CHECK = 0.25

# The keys that move between the pages of a long text.
PREVIOUS_PAGE = ["up", "page-up"]
NEXT_PAGE = ["down", "page-down"]


class KeyDisplay(Display):
    """Draws the game and reads single keys.

    Attributes:
        keys: the keyboard (see engine/keys.py).
        guard: the ShutdownGuard, so a stop signal can end the waiting.
        buttons: the button row of the screen being drawn, or None for a
            screen with a typing row.
    """

    def __init__(self, state, write, keys, **options):
        """Remember the keyboard; the other options are Display's."""
        super().__init__(state, write, **options)
        self.keys = keys
        self.guard = None
        self.buttons = None
        self.keys_footer = ""
        self.message = ""
        self.body = []
        self.skipped = self.skip_pressed

    # ---- starting and stopping

    def start(self):
        """Switch the keyboard to single keys and go to the alternate screen."""
        self.keys.start()
        super().start()
        self.fullscreen.hide_cursor()

    def stop(self):
        """Leave the alternate screen and put the keyboard back."""
        super().stop()
        self.keys.stop()

    # ---- drawing

    def frame(self, body, status, rows):
        """Return the rows of a screen: with buttons, or with an empty last row."""
        if self.buttons is None:
            # The line mode's footer names typed commands, so it is not shown.
            return compose_screen(self.hud(), body, status, rows)
        return key_screen(self.hud(), body, status, rows, self.buttons, self.keys_footer)

    def draw_buttons(self, body, labels, chosen, footer, status=""):
        """Draw a screen with `body`, a row of buttons and the keys that work."""
        self.body = body
        self.message = status
        self.buttons = button_row(labels, chosen)
        self.keys_footer = footer
        self.fullscreen.hide_cursor()
        self.draw(body, status)

    # ---- reading

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

    def pages_of(self, text):
        """Return the pages of one screen of text."""
        if is_pixel_art(text):
            return paginate(text.split("\n"), self.height())
        return self.pages_for(split_sections(text))

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

    def show_text(self, text, status=""):
        """Show a text as pages and wait. In a wave nothing is shown: its screen does that."""
        if PAGE_BREAK in text:
            return self.show_screens(split_screens(text))
        if self.state.coding or not self.state.running:
            return None
        return self.wait_at_the_end(text, self.pages_of(text))

    def play(self, frames, wait=True):
        """Play an animation; with `wait`, stay on its last picture until Enter."""
        self.buttons = button_row([])
        self.keys_footer = ""
        play_frames(frames, lambda picture: self.draw(picture.split("\n")), self.sleep, self.skipped,
                    self.delay)
        if wait:
            self.browse([self.last_body(frames[-1])])

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

    def show(self, answer):
        """Show an answer; return a command chosen with a button, or None."""
        if isinstance(answer, list):
            return self.show_animation(answer)
        return self.show_text(answer)

    def show_title(self):
        """Play the title animation and wait for Enter."""
        self.buttons = button_row([])
        self.keys_footer = "Enter start"
        super().show_title()

    def wait_at_title(self):
        """Wait for Enter on the title; Ctrl-D or the end of input go on to the menu, which quits."""
        self.draw(self.body_on_screen())
        try:
            while self.wait_key() not in ("enter", "ctrl-d"):
                pass
        except EOFError:
            return
