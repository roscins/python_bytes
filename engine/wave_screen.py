"""A wave in the key-driven mode: the code editor, the buttons and the panel.

    GOAL: Make Snek print SNEK ONLINE.
    [ the editor, always editable ]
    [ the panel: the task, results, run output or a hint ]
    [Submit]  [Run]  [Hint]  [Restart level]  [Map]  [Help]

WaveScreen.run() works the wave until the player leaves it, and returns the
command that says where to (":map", ":quit", ":play 1-2"). The buttons use
the same functions as the typed commands of line mode.
"""

from engine.boss import BossFight
from engine.boss_turns import submit_to_boss
from engine.choice_picker import ChoicePicker
from engine.commands import clear_frames, reveal_text, run_command
from engine.console import continue_pending
from engine.data_files import files_line
from engine.display import split_art_and_message
from engine.editor import BLANK, Editor
from engine.focus import Choice
from engine.hints import ask_for_hint, hint_lines
from engine.predict_lock import locked_message
from engine.review_picker import ReviewPicker
from engine.progression_help import next_level_to_play
from engine.rewards import apply_submission
from engine.scoring import HINT_NAMES, HINT_PRICES, is_unlocked
from engine.submission import grade_text
from engine.wave_report import explain_error, run_report, submit_report, syntax_error_of
from engine.workspace import starting_text
from render.editor_view import GUTTER, View, code_rows, divider, frame
from render.ansi import strip_ansi
from render.highlight import highlight_lines
from render.panel import wrap_lines
from render.screen import WIDTH

DIM = "\x1b[2m"
NORMAL = "\x1b[0m"

# The width of the text inside a frame.
INNER = WIDTH - 4

# Rows of text in the panel: when it opens, and while the player is typing.
PANEL_ROWS = 6
SMALL_PANEL_ROWS = 3

# The editor's rows beside a full panel in the smallest window.
TALLEST_EDITOR = 8

# The fewest rows of answer in a predict wave, and of text in its panel.
ANSWER_ROWS = 4
SMALLEST_PANEL = 3

BUTTONS = ["Submit", "Run", "Hint", "Restart wave", "Map", "Help"]

# The shortcut of each button that has one.
SHORTCUTS = {"ctrl-s": "Submit", "ctrl-r": "Run", "ctrl-t": "Hint", "ctrl-o": "Map", "ctrl-g": "Help"}

EDITOR_FOOTER = "^S submit  ^R run  ^T hint  ^G help  ^O map  ^Z undo  ^E command"
BUTTON_FOOTER = "←→ pick · Enter press · ↑ editor · ^S submit  ^R run"
QUESTION_FOOTER = "←→ pick · Enter press · Esc no"
INPUT_FOOTER = "type the input lines · ^R run · Esc cancel"

HELP_KEYS = [
    "Arrows move. Enter splits a line, Backspace joins lines, Tab adds 4 spaces.",
    "Down from the last line, or Esc, goes to the buttons.",
    "Ctrl-S submit      Ctrl-R run (not graded)   Ctrl-T hint",
    "Ctrl-Z undo        Ctrl-O map                Ctrl-G this help",
    "Ctrl-E one command: power-ups, stats, where, wave 2, restart level,",
    "       or a line of Python",
    "PgUp and PgDn turn the panel under the code. Esc hides it; F1 or the",
    "[Panel] button shows it again.",
]


def dimmed(text):
    """Return `text` in dim letters, without its own colours."""
    return f"{DIM}{strip_ansi(text)}{NORMAL}"


class Panel:
    """The box under the editor.

    Attributes:
        title: what it holds, for example "RESULTS".
        lines: its text.
        top: the first line shown.
        checked: for results and run output, the code lines they are about,
            or None.
    """

    def __init__(self, title, lines):
        """Wrap the lines to the width of the panel."""
        self.title = title
        self.lines = wrap_lines(lines, INNER)
        self.top = 0
        self.checked = None

    def is_outdated(self, code_lines):
        """Return True if the code is no longer what these results are about."""
        return self.checked is not None and self.checked != code_lines

    def shown(self, height):
        """Return the `height` rows to show, with a note if there is more."""
        self.top = max(0, min(self.top, len(self.lines) - height))
        rows = self.lines[self.top:self.top + height]
        while len(rows) < height:
            rows.append("")
        return rows

    def heading(self, height):
        """Return the title, saying how to see the rest when it does not fit."""
        if len(self.lines) > height:
            return f"{self.title} · PgUp/PgDn for more"
        return self.title


class WaveScreen:
    """The screen of the wave being played.

    Attributes:
        level, number: the wave on screen.
        editor: its code, with the cursor.
        picker: for a quiz wave, what the arrow keys move in; otherwise None.
            The editor then only holds the answer sheet it writes.
        input_editor: the input lines being typed for Run, or None.
        mark: where the last error is, or None.
        panel: the Panel, or None if there is nothing to show.
        hidden: True after Esc put the panel away.
        small: True while the player types, so the code gets more room.
        on_buttons: True while the buttons have the focus.
        buttons: the Choice among the buttons.
        question: (Choice of No and Yes, what Yes does), or None.
        leave: the command to leave with, or None to stay.
    """

    def __init__(self, display, state, save=lambda: None):
        """Remember what to draw on, the game, and how to save it."""
        self.display = display
        self.state = state
        self.save = save
        self.level = None
        self.number = 0
        self.editor = None
        self.picker = None
        self.leave = None

    # ---- opening a wave

    def open(self):
        """Show the wave the game is on, with the cursor where the work starts."""
        self.level = self.state.find_level(self.state.current_level)
        self.number = self.state.current_wave
        wave = self.wave()
        text = self.state.wave_text(self.level, self.number)
        self.editor = Editor(text, blanks=wave.kind == "fill-in")
        self.synced = list(self.editor.lines)
        self.place_cursor()
        self.picker = None
        if wave.mode == "choice":
            self.picker = ChoicePicker(wave, text)
        elif wave.mode == "review":
            self.picker = ReviewPicker(wave, text)
        self.view = View()
        self.input_editor = None
        self.mark = None
        self.show_mark = False
        self.on_buttons = False
        self.question = None
        self.leave = None
        self.panel = None
        self.shown_time = None
        self.hidden = False
        self.small = False
        # A boss gave its task on the screens before; its code needs the room.
        if not self.level.boss:
            self.panel = Panel("TASK", self.task_lines())
        elif self.state.boss_fight is None and not self.passed():
            self.state.boss_fight = BossFight(self.level)
        self.buttons = Choice(self.labels())

    def task_lines(self):
        """Return the task as lines, with the data files named first."""
        lines = self.wave().brief.strip().splitlines()
        named = files_line(self.wave(), keys=True)
        if named:
            lines = [named] + lines
        return lines

    def show_panel(self):
        """Show the panel at its full size; with none, show the task."""
        if self.panel is None:
            self.panel = Panel("TASK", self.task_lines())
        self.hidden = False
        self.small = False

    def new_panel(self, title, lines):
        """Put a new panel under the editor, at its full size."""
        self.panel = Panel(title, lines)
        self.hidden = False
        self.small = False

    def place_cursor(self):
        """Fill-in: the first blank. Debug and boss: line 1. Build: a new line. Predict: the end."""
        wave = self.wave()
        if wave.mode == "predict":
            self.editor.go_to_end()
        elif wave.kind == "fill-in":
            if not self.editor.go_to_first_blank():
                self.editor.go_to_end()
        elif wave.kind == "build":
            if self.editor.text():
                self.editor.go_to_new_last_line()

    def wave(self):
        """Return the Wave on screen."""
        return self.level.waves[self.number - 1]

    def passed(self):
        """Return True if every test of this wave has passed (or its answer was shown)."""
        return self.state.progress_for(self.level).wave_best[self.number - 1] >= 1.0

    def next_label(self):
        """Return "Next wave", "Next level" or None."""
        if not self.passed():
            return None
        if self.number < len(self.level.waves):
            return "Next wave"
        if self.level.id in self.state.cleared and next_level_to_play(self.state) is not None:
            return "Next level"
        return None

    def labels(self):
        """Return the buttons, with the way onward first once the wave is passed."""
        labels = list(BUTTONS)
        onward = self.next_label()
        if onward is not None:
            labels.insert(0, onward)
        if self.panel is not None and (self.hidden or self.small):
            labels.append("Panel")
        return labels

    # ---- drawing

    def panel_open(self):
        """Return True if the panel is on screen."""
        return self.panel is not None and not self.hidden

    def panel_rows(self):
        """Return how many rows of text the panel gets."""
        if self.small and self.input_editor is None:
            return max(1, min(SMALL_PANEL_ROWS, len(self.panel.lines)))
        return PANEL_ROWS

    def editor_rows(self, total):
        """Return how many rows of text the editor frame gets out of `total` screen rows."""
        # The GOAL line and the two borders of the frame.
        room = total - 3
        if not self.panel_open():
            return room
        if self.picker is not None:
            rows, _ = self.picker.rows(INNER)
            return min(len(rows), room - 2 - SMALLEST_PANEL)
        if self.wave().mode == "predict":
            wanted = len(self.code_to_read()) + 1 + max(ANSWER_ROWS, len(self.editor.lines))
            smallest = min(SMALLEST_PANEL, self.panel_rows())
            return min(wanted, room - 2 - smallest)
        # A taller window gives its extra rows to the panel.
        return min(room - 2 - self.panel_rows(), TALLEST_EDITOR + PANEL_ROWS - self.panel_rows())

    def code_to_read(self):
        """Return the lines a predict wave asks about."""
        return highlight_lines((self.wave().code or "").strip(), True)

    def editor_frame(self, height):
        """Return the frame with the code (and, for predict, the code to read above the answer)."""
        if self.picker is not None:
            return self.picker_frame(height)
        cursor = None
        if not self.on_buttons and self.input_editor is None:
            cursor = (self.editor.row, self.editor.column)
        mark = self.mark
        # Just after Submit or Run, scroll so that the failing line is seen.
        follow = None
        if self.show_mark and mark is not None:
            follow = (mark.row, mark.column or 0)
        rows = []
        if self.wave().mode == "predict":
            rows = [f"      {line}" for line in self.code_to_read()]
            rows.append(divider("YOUR ANSWER: one printed line per line", INNER))
        rows = rows + code_rows(self.editor.lines, self.view, height - len(rows), INNER, cursor, mark, follow)
        return frame(self.title(), rows, WIDTH)

    def picker_frame(self, height):
        """Return the frame of a quiz wave, scrolled so that the cursor's line shows."""
        focused = not self.on_buttons
        rows, cursor_row = self.picker.rows(INNER, focused)
        top = max(0, cursor_row - height + 1)
        shown = rows[top:top + height]
        return frame(self.title(), shown + [""] * (height - len(shown)), WIDTH)

    def title(self):
        """Return the title of the editor frame."""
        if not self.level.boss:
            return f"WAVE {self.number} of {len(self.level.waves)} · {self.wave().kind.upper()}"
        fight = self.state.boss_fight
        if fight is None:
            return "BOSS WAVE"
        seconds = int(fight.time_left())
        tries = "try" if fight.lives == 1 else "tries"
        return (f"BOSS WAVE · {fight.hp_left}/{fight.hp_total} tests to beat · {fight.lives} {tries} · "
                f"{seconds // 60}:{seconds % 60:02d}")

    def lines(self, total):
        """Return the `total` rows above the buttons."""
        goal = self.wave().goal or self.wave().brief.strip().splitlines()[0]
        height = self.editor_rows(total)
        lines = [f" GOAL: {goal}"] + self.editor_frame(height)
        room = total - len(lines) - 2
        if not self.panel_open():
            return lines + [""] * (total - len(lines))
        if self.input_editor is not None:
            cursor = None
            if not self.on_buttons:
                cursor = (self.input_editor.row, self.input_editor.column)
            rows = code_rows(self.input_editor.lines, View(), room, INNER, cursor)
            return lines + frame("INPUT the program will read", rows, WIDTH)
        if self.small:
            room = min(room, self.panel_rows())
        rows = self.panel.shown(room)
        heading = self.panel.heading(room)
        if self.panel.is_outdated(self.editor.lines):
            heading = f"{self.panel.title} · edited since last check"
            rows = [dimmed(row) for row in rows]
        lines = lines + frame(heading, rows, WIDTH)
        return lines + [""] * (total - len(lines))

    def draw(self):
        """Draw the whole screen."""
        height = self.display.height()
        lines = self.lines(height + 1)
        labels = self.labels()
        chosen = None
        footer = EDITOR_FOOTER
        if self.picker is not None:
            footer = self.picker.footer
        if self.input_editor is not None:
            footer = INPUT_FOOTER
        if self.on_buttons:
            self.buttons.labels = labels
            self.buttons.index = min(self.buttons.index, len(labels) - 1)
            chosen = self.buttons.index
            footer = BUTTON_FOOTER
        if self.question is not None:
            choice = self.question[0]
            labels = choice.labels
            chosen = choice.index
            footer = QUESTION_FOOTER
        self.display.draw_buttons(lines[:height], labels, chosen, footer, lines[height])

    # ---- keys

    def run(self):
        """Work the wave until the player leaves; return the command to leave with."""
        self.open()
        while self.leave is None:
            self.draw()
            key = self.wait()
            # Pasted text arrives as many keys: handle them all, then save once.
            while key is not None and self.leave is None:
                self.press(key)
                self.sync()
                key = self.display.keys.read_key(0)
            self.save()
        return self.leave

    def wait(self):
        """Wait for a key. In a boss fight, return None when the timer has moved on."""
        if not self.level.boss or self.state.boss_fight is None:
            return self.display.wait_key()
        while True:
            key = self.display.poll_key()
            if key is not None:
                return key
            seconds = int(self.state.boss_fight.time_left())
            if seconds != self.shown_time:
                self.shown_time = seconds
                return None

    def sync(self):
        """Put the edited code into the game state, from where it is saved."""
        if self.editor.lines == self.synced:
            return
        self.synced = list(self.editor.lines)
        self.state.wave_text(self.level, self.number)
        self.state.buffers[self.level.id][self.number] = self.editor.text()

    def press(self, key):
        """Handle one key."""
        self.show_mark = False
        if self.question is not None:
            self.answer_question(key)
        elif key == "ctrl-d":
            self.leave = ":quit"
        elif key in SHORTCUTS:
            self.do(SHORTCUTS[key])
        elif key == "f1":
            self.show_panel()
        elif key == "ctrl-e":
            self.typed_command()
        elif key in ("page-up", "page-down"):
            self.turn_panel(key)
        elif key == "escape":
            self.escape()
        elif self.on_buttons:
            self.press_on_buttons(key)
        elif self.input_editor is not None:
            self.press_in_editor(self.input_editor, key)
        elif self.picker is not None:
            self.press_in_picker(key)
        else:
            self.press_in_editor(self.editor, key)

    def press_in_editor(self, editor, key):
        """Move or change the text; Down on the last line goes to the buttons."""
        if key == "down" and editor.on_last_line():
            self.focus_buttons()
            return
        before = list(editor.lines)
        row = editor.row
        if key == "ctrl-z":
            editor.undo()
        else:
            editor.press(key)
        if editor is self.editor:
            self.forget_mark(before, min(row, editor.row))
            if before != editor.lines:
                self.small = True

    def press_in_picker(self, key):
        """Move in a quiz wave; keep the answer sheet up to date."""
        before = self.picker.sheet()
        where = self.picker.press(key)
        if self.picker.sheet() != before:
            self.editor = Editor(self.picker.sheet())
        if where == "buttons":
            self.focus_buttons()

    def forget_mark(self, before, first_row):
        """Remove the mark when its line was changed or moved."""
        after = self.editor.lines
        if self.mark is None or before == after:
            return
        row = self.mark.row
        if len(before) != len(after):
            if first_row <= row:
                self.mark = None
        elif before[row:row + 1] != after[row:row + 1]:
            self.mark = None

    def focus_buttons(self):
        """Move to the buttons."""
        self.on_buttons = True
        self.buttons = Choice(self.labels())

    def escape(self):
        """Cancel the input, hide the panel, or go between editor and buttons."""
        if self.picker is not None and self.picker.choosing and not self.on_buttons:
            self.press_in_picker("escape")
        elif self.input_editor is not None:
            self.input_editor = None
            self.panel = None
            self.on_buttons = False
        elif self.on_buttons:
            self.on_buttons = False
        elif self.panel_open():
            self.hidden = True
        else:
            self.focus_buttons()

    def press_on_buttons(self, key):
        """Left, Right and Tab pick; Enter presses; Up goes back to the editor."""
        if key == "up":
            self.on_buttons = False
        elif key == "tab":
            self.buttons.index = (self.buttons.index + 1) % len(self.buttons.labels)
        elif key == "enter":
            self.do(self.buttons.label())
        else:
            self.buttons.move(key)

    def turn_panel(self, key):
        """Show the earlier or later part of a long panel."""
        if self.panel is None:
            return
        step = SMALLEST_PANEL
        if key == "page-up":
            step = -step
        self.panel.top = max(0, self.panel.top + step)

    def ask(self, question, on_yes):
        """Put a yes-or-no question in the panel; No is chosen."""
        lines = [] if self.panel is None or self.panel.title != "HINT" else self.panel.lines
        self.new_panel(self.panel.title if lines else "SNEK", lines + [question])
        self.panel.top = len(self.panel.lines)
        self.question = (Choice(["No", "Yes"]), on_yes)

    def answer_question(self, key):
        """Handle a key while a question waits."""
        choice, on_yes = self.question
        if key == "enter":
            self.question = None
            if choice.label() == "Yes":
                on_yes()
            else:
                self.panel = None
        elif key == "escape":
            self.question = None
            self.panel = None
        elif key == "tab":
            choice.index = 1 - choice.index
        else:
            choice.move(key)

    # ---- the buttons

    def do(self, label):
        """Press the button `label`."""
        self.sync()
        if label == "Submit":
            self.submit()
        elif label == "Run":
            self.run_code()
        elif label == "Hint":
            self.hint()
        elif label == "Restart wave":
            self.ask("Restart this wave? Its starter code comes back.", self.restart_wave)
        elif label == "Panel":
            self.show_panel()
        elif label == "Map":
            self.leave = ":map"
        elif label == "Help":
            self.help()
        elif label == "Next wave":
            self.state.current_wave = self.number + 1
            self.state.coding = True
            self.open()
        elif label == "Next level":
            self.leave = f":play {next_level_to_play(self.state).id}"

    def say(self, title, text):
        """Put a text in the panel."""
        self.input_editor = None
        self.new_panel(title, text.split("\n"))

    def show_result(self, title, lines, mark):
        """Put a result in the panel and mark the failing line, if there is one."""
        self.input_editor = None
        self.new_panel(title, lines)
        self.panel.checked = list(self.editor.lines)
        self.mark = mark
        self.show_mark = True
        self.on_buttons = False

    def submit(self):
        """Grade the code."""
        if self.level.boss:
            self.submit_boss()
            return
        progress = self.state.progress_for(self.level)
        if progress.wave_is_perfect(self.number, self.wave()):
            self.say("RESULTS", f"Wave {self.number} already passed ✓.")
            return
        submission = grade_text(self.wave(), self.number, self.editor.text())
        if submission.result is None:
            self.say("RESULTS", submission.problem
                     or "Your code is empty. Type your first line, then press Ctrl-S.")
            return
        combo = self.state.combo
        reward = apply_submission(self.state, self.level, [submission])
        lines, mark = submit_report(self.level, submission, reward, progress)
        if progress.revealed[self.number - 1]:
            lines = lines[:1] + reveal_text(self.wave()).split("\n") + lines[1:]
        self.show_result("RESULTS", lines, mark)
        if self.passed():
            if self.number == len(self.level.waves):
                self.state.coding = False
            self.focus_buttons()
        self.save()
        self.celebrate(reward)
        self.draw()
        self.display.after_command(combo)

    def celebrate(self, reward):
        """Play the level-clear animation if this submit earned it."""
        frames = clear_frames(self.state, self.level, reward)
        if frames is not None:
            self.display.play(frames)

    def submit_boss(self):
        """A hit on the boss. Only a crash or a syntax error is marked, so its tests stay hidden."""
        code = self.editor.text()
        if code.strip() == "":
            self.say("RESULTS", "Type your code first, then press Ctrl-S.")
            return
        answer = submit_to_boss(self.state, self.level)
        frames = answer if isinstance(answer, list) else [answer]
        art, message = split_art_and_message(frames[-1])
        # After a hit you are straight back in the code; a win stays until Enter.
        won = "BOSS DEFEATED." in message
        self.display.play(frames[:-1] + [art], wait=won)
        lines = message.split("\n")
        mark = None
        crashed = "stopped with an error" in message or "Snek tripped" in message
        if syntax_error_of(code):
            explained, mark = explain_error(syntax_error_of(code), code)
            lines = lines[:1] + explained
        elif crashed:
            explained, mark = run_report(code, data=self.wave().files)
            if mark is not None:
                lines = lines[:1] + explained
        self.show_result("RESULTS", lines, mark)
        if won:
            self.state.coding = False
            self.focus_buttons()

    def run_code(self):
        """Try the code without grading it; ask for its input first if it reads any."""
        code = self.editor.text()
        problem = ""
        if self.wave().mode == "predict":
            problem = "Snek will not tell you what that code prints. Type your answer and press Ctrl-S."
        elif self.picker is not None:
            problem = "There is nothing to run here. Answer, then press Ctrl-S."
        elif locked_message(self.state):
            problem = locked_message(self.state)
        elif code.strip() == "":
            problem = "Your code is empty. Type your first line, then press Ctrl-R."
        elif BLANK in code and self.wave().kind == "fill-in":
            problem = f"There is still a {BLANK} blank in your code. Fill it in first."
        if problem:
            self.say("RUN", problem)
            return
        stdin_text = ""
        if "input(" in code:
            if self.input_editor is None:
                self.input_editor = Editor()
                self.new_panel("INPUT", [])
                self.on_buttons = False
                return
            stdin_text = self.input_editor.text()
        lines, mark = run_report(code, stdin_text, self.wave().files)
        self.show_result("RUN (not graded)", lines, mark)

    def hint(self):
        """Show the hints of this wave, asking before a new one is bought."""
        wave = self.wave()
        bought = self.state.progress_for(self.level).hints_bought[self.number - 1]
        if wave.hints and bought < len(HINT_NAMES) and self.state.coins >= HINT_PRICES[bought]:
            self.say("HINT", "\n".join(hint_lines(wave, self.number, bought)))
            self.panel.lines = [line for line in self.panel.lines if line]
            self.ask(f"Buy the {HINT_NAMES[bought]} hint for {HINT_PRICES[bought]} coins? "
                     f"You have {self.state.coins}.", self.buy_hint)
            return
        self.buy_hint()

    def buy_hint(self):
        """Show the hints, buying the next one if the player can."""
        self.say("HINT", ask_for_hint(self.state, self.level, self.number))
        self.panel.top = len(self.panel.lines)

    def restart_wave(self):
        """Put the starter code back in this wave only. Progress stays."""
        self.state.buffers[self.level.id][self.number] = starting_text(self.wave())
        self.state.undo_stack = []
        self.state.coding = True
        if self.level.boss:
            self.state.boss_fight = BossFight(self.level)
        self.open()
        self.say("SNEK", "Wave restarted: the starter code is back.\n" + self.wave().brief.strip())

    def restart_level(self):
        """Put the starter code back in every wave and go to wave 1. Progress stays."""
        for number in self.state.buffers.get(self.level.id, {}):
            self.state.buffers[self.level.id][number] = starting_text(self.level.waves[number - 1])
        self.state.current_wave = 1
        self.state.coding = True
        if self.level.boss:
            self.state.boss_fight = BossFight(self.level)
        self.open()
        self.say("SNEK", "Level restarted: the starter code is back.\n" + self.wave().brief.strip())

    def help(self):
        """Show the task and the keys on a screen of their own."""
        keys = HELP_KEYS if self.picker is None else self.picker.help_lines
        lines = ["TASK"] + self.task_lines() + ["", "KEYS"] + keys
        self.display.browse(self.display.pages_of("\n".join(lines)))

    # ---- Ctrl-E

    def typed_command(self):
        """Read one command on the last row and show what it answers."""
        self.sync()
        line = self.display.read(self.display.read_line, "command: ").strip().lstrip(":")
        if line == "":
            return
        words = line.split()
        name = words[0].lower()
        shortcuts = {"submit": "Submit", "run": "Run", "map": "Map", "help": "Help"}
        if len(words) == 1 and name in shortcuts:
            self.do(shortcuts[name])
        elif name == "quit":
            self.leave = ":quit"
        elif [word.lower() for word in words] == ["restart", "wave"]:
            self.do("Restart wave")
        elif [word.lower() for word in words] == ["restart", "level"]:
            self.ask("Restart the level? The starter code comes back in every wave.",
                     self.restart_level)
        elif name == "play" and len(words) == 2 and self.can_play(words[1]):
            self.leave = f":{line}"
        elif name == "wave":
            answer = run_command(self.state, line, colon=True)
            if self.state.current_wave != self.number:
                self.open()
            else:
                self.say("SNEK", answer if "waves 1 to" in answer else self.wave().brief.strip())
        else:
            self.show_command(line)

    def can_play(self, level_id):
        """Return True if `level_id` is a level that is open."""
        level = self.state.find_level(level_id)
        return level is not None and is_unlocked(self.state.slots(), self.state.cleared, level)

    def show_command(self, line):
        """Run a power-up, a command or a line of Python and show the answer."""
        answer = run_command(self.state, line, colon=False)
        # A block such as a for loop needs more lines.
        while self.state.pending is not None:
            answer = continue_pending(self.state, self.display.read(self.display.read_line, "... "))
        self.say("SNEK", answer or "Done.")
