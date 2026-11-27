"""The title menu, the window check and the map, worked with keys.

The map does not run commands itself. It returns the line a player would
have typed ("play 1-1", "stats", "quit"), and the command loop handles it
as always.
"""

from engine.commands import do_map, level_ids
from engine.focus import Choice
from engine.hud import map_status
from engine.progression_help import next_level_to_play
from engine.title import NEW, QUIT, TITLE, options_for
from render.buttons import menu_lines
from render.panel import panel
from render.screen import WIDTH, size_problem
from render.typewriter import play_frames
from render.world_map import load_map_art, map_screen, slither_frames

# What wait_for_window_keys can answer, besides QUIT.
FULL = "full"
PLAIN = "plain"

MAP_BUTTONS = ["Play", "Stats", "Help", "Quit"]
BUTTON_COMMANDS = {"Stats": "stats", "Help": "help", "Quit": "quit"}
MAP_FOOTER = "←→ move · Enter play · ↓ buttons · : command"
BUTTON_FOOTER = "←→ choose · Enter press · ↑ map"


def wait_for_window_keys(keyboard, size, write):
    """Before full screen: wait until the window is big enough.

    The size is checked again by itself. Returns FULL, PLAIN if the player
    pressed p, or QUIT.
    """
    shown = ""
    keyboard.start()
    try:
        while True:
            problem = size_problem(*size())
            if not problem:
                return FULL
            if problem != shown:
                write(problem + "\n")
                shown = problem
            key = keyboard.read_key(0.25)
            if key in ("p", "P"):
                return PLAIN
            if key == "ctrl-d":
                return QUIT
    except (EOFError, KeyboardInterrupt):
        return QUIT
    finally:
        keyboard.stop()


def menu_screen(display, heading, notes, choice):
    """Draw a menu in a panel and wait for a key."""
    lines = list(notes) + menu_lines(choice.labels, choice.index)
    display.draw_buttons(panel(heading, lines, WIDTH), [], None, "↑↓ choose · Enter press")
    return display.wait_key()


def title_menu(display, info):
    """Show the title menu; return CONTINUE, NEW or QUIT.

    A new game over a good save asks first, with No chosen.
    """
    options = options_for(info)
    choice = Choice([label for _, label in options], back="up", forward="down")
    notes = []
    if info.status == "damaged":
        notes = ["Your save file is damaged. NEW GAME keeps it as a .broken file.", ""]
    while True:
        try:
            key = menu_screen(display, TITLE, notes, choice)
            if key == "ctrl-d":
                return QUIT
            if key != "enter":
                choice.move(key)
                continue
            chosen = options[choice.index][0]
            if chosen == NEW and info.status == "ok" and not confirm_new_game(display):
                continue
            return chosen
        except EOFError:
            return QUIT


def confirm_new_game(display):
    """Ask before starting over; return True only for Yes."""
    answer = Choice(["No", "Yes"], back="up", forward="down")
    notes = ["This starts again from the beginning.", "Your old game is kept as save.json.old.", ""]
    while True:
        key = menu_screen(display, "NEW GAME?", notes, answer)
        if key == "enter":
            return answer.label() == "Yes"
        if key == "escape":
            return False
        answer.move(key)


class MapScreen:
    """The map as the player walks on it.

    Attributes:
        selected: the id of the level Snek stands at, or None before the first look.
        on_buttons: True while the buttons have the focus.
        message: a short answer to show under the map once.
    """

    def __init__(self, display, state):
        """Remember what to draw on and the game."""
        self.display = display
        self.state = state
        self.art = load_map_art()
        self.selected = None
        self.on_buttons = False
        self.buttons = Choice(MAP_BUTTONS)
        self.message = ""
        self.last_level = None

    def follow_the_player(self):
        """Put Snek where the player is now, if they have been somewhere since the last look."""
        if self.selected is not None and self.state.current_level == self.last_level:
            return
        self.last_level = self.state.current_level
        level = self.state.find_level(self.state.current_level)
        if level is None:
            level = next_level_to_play(self.state)
        if level is None:
            level = self.state.slots()[0]
        self.selected = level.id

    def world_of_selected(self):
        """Return (world, its level ids, the position of the selected one, its slot)."""
        slot = self.state.find_slot(self.selected)
        ids = level_ids(self.state.slots_in_world(slot.world))
        return slot.world, ids, ids.index(slot.id), slot

    def draw(self):
        """Draw the map, the chosen level's name and the buttons."""
        world, ids, index, slot = self.world_of_selected()
        status = map_status(self.state, self.state.slots_in_world(world))
        lines = map_screen(world, ids, index, self.art, status).split("\n")
        lines.append("")
        lines.append(f" [{slot.id}] {slot.title}")
        chosen = None
        footer = MAP_FOOTER
        if self.on_buttons:
            chosen = self.buttons.index
            footer = BUTTON_FOOTER
        self.display.draw_buttons(lines, MAP_BUTTONS, chosen, footer, self.message)

    def move(self, step):
        """Move Snek one level left (-1) or right (1), slithering within a world."""
        slots = self.state.slots()
        ids = level_ids(slots)
        target = ids.index(self.selected) + step
        if not 0 <= target < len(slots):
            return
        world, world_ids, index, slot = self.world_of_selected()
        self.selected = slots[target].id
        self.message = ""
        if slots[target].world != world or not self.display.animating():
            return
        status = map_status(self.state, self.state.slots_in_world(world))
        frames = slither_frames(world, world_ids, index, index + step, self.art, status)
        play_frames(frames, lambda frame: self.display.draw(frame.split("\n")), self.display.sleep,
                    lambda: False, self.display.delay)

    def press(self, key):
        """Handle one key; return the command line it stands for, or None."""
        if key == "ctrl-d":
            return "quit"
        if key in (":", "ctrl-e"):
            return self.typed_command()
        if self.on_buttons:
            if key in ("up", "escape"):
                self.on_buttons = False
            elif key == "enter":
                self.on_buttons = False
                if self.buttons.label() == "Play":
                    return f"play {self.selected}"
                return BUTTON_COMMANDS[self.buttons.label()]
            else:
                self.buttons.move(key)
            return None
        if key == "enter":
            return f"play {self.selected}"
        if key == "left":
            self.move(-1)
        elif key == "right":
            self.move(1)
        elif key in ("down", "tab"):
            self.on_buttons = True
        return None

    def typed_command(self):
        """Let the player type one command on the last row; None if they typed nothing."""
        line = self.display.read(self.display.read_line, ": ")
        if line.strip() == "":
            return None
        return line

    def next_line(self):
        """Show the map until the player chooses something; return it as a command line."""
        self.follow_the_player()
        while True:
            self.draw()
            line = self.press(self.display.wait_key())
            if line is not None:
                self.message = ""
                return line


def is_map_answer(state, answer):
    """Return True if `answer` is just the map, which the map screen draws itself."""
    return not state.coding and answer == do_map(state, [])
