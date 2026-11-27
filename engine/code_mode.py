"""Code mode: typing the code of a wave into the game, one line at a time.

While a wave is on, every line the player types is a line of code and is
added to the wave's buffer, shown with a line number. Commands start with a
colon: :submit, :show, :undo, :clear, :edit, :ins, :del, :wave, :hint,
:map, :help.

The buffer lives in the GameState and is saved after every line (see
engine/loop.py), so nothing typed is lost if the game is closed or killed.
Like the other command modules, this one returns text and never prints.
"""

from engine.fill import BLANK, fill_next_blank, is_filling
from engine.level_screen import wave_screen_text

NOT_PLAYING = "You are not playing a level. Type play <level> first."

# How many spaces a Tab becomes. Python code is indented by 4.
TAB_WIDTH = 4


def buffer_lines(text):
    """Return the lines of a buffer (a text) as a list."""
    return text.splitlines()


def lines_to_text(lines):
    """Return a list of lines as a buffer text: every line ends with a newline."""
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def bar(state):
    """Return the character between a line number and its code."""
    if state.plain:
        return "|"
    return "│"


def current_context(state):
    """Return (level, wave number) of the wave being played, or (None, 0) if none."""
    level = state.find_level(state.current_level)
    if level is None:
        return None, 0
    return level, state.current_wave


def prompt_for(state):
    """Return what to show before the player types: "> ", or the next line number in code mode."""
    pending = state.pending
    if pending is not None:
        if pending["kind"] == "repl":
            return "... "
        if pending["kind"] == "run_input":
            return f"input {len(pending['lines']) + 1} > "
        return f"{pending['line']:>3} {bar(state)} "
    level, number = current_context(state)
    if not state.coding or level is None:
        return "> "
    count = len(buffer_lines(state.wave_text(level, number)))
    return f"{count + 1:>3} {bar(state)} "


def add_code_line(state, line):
    """Add one typed line to the current wave's code. Returns text to show ("" normally).

    A Tab becomes four spaces. An empty line is kept only between lines of
    code, so pressing Enter twice does not fill the code with blank lines.
    """
    level, number = current_context(state)
    if level is None:
        return NOT_PLAYING
    wave = level.waves[number - 1]
    text = state.wave_text(level, number)
    if is_filling(wave, text):
        if line.strip() == "":
            return ""
        filled = fill_next_blank(text, line)
        state.set_wave_text(level, number, filled)
        if BLANK not in filled:
            state.just_filled = (level.id, number, filled)
        return show_wave(state)
    # Only right after filling: a player who cleared the wave writes freely.
    if state.just_filled == (level.id, number, text) and line.strip() != "":
        return "All blanks are filled. :submit checks it; :undo or :edit changes it."
    lines = buffer_lines(text)
    line = line.replace("\t", " " * TAB_WIDTH).rstrip("\r\n")
    if line.strip() == "":
        if not lines or lines[-1].strip() == "":
            return ""
        line = ""
    lines.append(line)
    state.set_wave_text(level, number, lines_to_text(lines))
    return ""


def show_wave(state):
    """Return the screen of the current wave: the task and the numbered code so far."""
    level, number = current_context(state)
    if level is None:
        return NOT_PLAYING
    return wave_screen_text(level, number, state.wave_text(level, number), state.plain, state.color)


def split_number(text):
    """Split "3 rest of the line" into (3, "rest of the line"); the number is None if missing.

    Only the single space after the number is removed, so the spaces that
    follow stay: they are the indentation of the new line.
    """
    first, _, rest = text.lstrip().partition(" ")
    if not first.isdigit():
        return None, ""
    return int(first), rest


def check_line_number(lines, number, allow_end=False):
    """Return a message if `number` is not a line of the code, or "" if it is."""
    last = len(lines) + 1 if allow_end else len(lines)
    if number < 1 or number > last:
        if not lines:
            return "Your code has no lines yet."
        return f"There is no line {number}. Your code has {len(lines)} lines."
    return ""


def do_show(state, text):
    """:show - the current wave and the code typed so far."""
    return show_wave(state)


def do_undo(state, text):
    """:undo - go back to the code before the last change."""
    level, number = current_context(state)
    if level is None:
        return NOT_PLAYING
    if not state.undo_wave_text(level, number):
        return "There is nothing to undo."
    return "Undone.\n" + show_wave(state)


def do_clear(state, text):
    """:clear - empty the wave's code. :undo brings it back."""
    level, number = current_context(state)
    if level is None:
        return NOT_PLAYING
    state.set_wave_text(level, number, "")
    return "Cleared. Type :undo to bring your code back.\n" + show_wave(state)


def apply_edit(state, line_number, new_text):
    """Replace line `line_number` of the current wave's code; return the wave screen or a message."""
    level, number = current_context(state)
    if level is None:
        return NOT_PLAYING
    lines = buffer_lines(state.wave_text(level, number))
    problem = check_line_number(lines, line_number)
    if problem:
        return problem
    lines[line_number - 1] = new_text.replace("\t", " " * TAB_WIDTH)
    state.set_wave_text(level, number, lines_to_text(lines))
    return show_wave(state)


def apply_insert(state, line_number, new_text):
    """Put a new line before line `line_number` (the last line + 1 adds at the end)."""
    level, number = current_context(state)
    if level is None:
        return NOT_PLAYING
    lines = buffer_lines(state.wave_text(level, number))
    problem = check_line_number(lines, line_number, allow_end=True)
    if problem:
        return problem
    lines.insert(line_number - 1, new_text.replace("\t", " " * TAB_WIDTH))
    state.set_wave_text(level, number, lines_to_text(lines))
    return show_wave(state)


def do_edit(state, text):
    """:edit <n> [new text] - replace line n. Without the text, the game asks for it."""
    level, number = current_context(state)
    if level is None:
        return NOT_PLAYING
    line_number, new_text = split_number(text)
    if line_number is None:
        return "Usage: :edit <line> [new text], for example: :edit 2     print(x)"
    lines = buffer_lines(state.wave_text(level, number))
    problem = check_line_number(lines, line_number)
    if problem:
        return problem
    if new_text.strip() == "":
        state.pending = {"kind": "edit", "line": line_number}
        return (f"Line {line_number} now: {lines[line_number - 1]}\n"
                "Type the new line (Enter on an empty line keeps the old one).")
    return apply_edit(state, line_number, new_text)


def do_ins(state, text):
    """:ins <n> [text] - put a new line before line n. Without the text, the game asks for it."""
    level, number = current_context(state)
    if level is None:
        return NOT_PLAYING
    line_number, new_text = split_number(text)
    if line_number is None:
        return "Usage: :ins <line> [text], for example: :ins 1 import math"
    lines = buffer_lines(state.wave_text(level, number))
    problem = check_line_number(lines, line_number, allow_end=True)
    if problem:
        return problem
    if new_text.strip() == "":
        state.pending = {"kind": "ins", "line": line_number}
        return f"Type the new line {line_number} (Enter on an empty line adds nothing)."
    return apply_insert(state, line_number, new_text)


def do_del(state, text):
    """:del <n> - remove line n."""
    level, number = current_context(state)
    if level is None:
        return NOT_PLAYING
    line_number, _ = split_number(text)
    if line_number is None:
        return "Usage: :del <line>, for example: :del 2"
    lines = buffer_lines(state.wave_text(level, number))
    problem = check_line_number(lines, line_number)
    if problem:
        return problem
    del lines[line_number - 1]
    state.set_wave_text(level, number, lines_to_text(lines))
    return show_wave(state)


def do_wave(state, text):
    """:wave <n> - go to wave n of this level (to continue, or to play it again)."""
    level, _ = current_context(state)
    if level is None:
        return NOT_PLAYING
    number, _ = split_number(text)
    if number is None or number < 1 or number > len(level.waves):
        example = ":wave 2"
        if state.keys:
            example = "wave 2"
        return f"Level {level.id} has waves 1 to {len(level.waves)}. Type, for example: {example}"
    state.current_wave = number
    state.coding = True
    return show_wave(state)


# The commands that only make sense in code mode. Each takes the game state
# and the text after the command name, and has a short description for :help.
CODE_COMMANDS = {
    "show": (do_show, "show this wave and the code you have typed"),
    "undo": (do_undo, "go back to the code before your last change"),
    "clear": (do_clear, "empty your code (:undo brings it back)"),
    "edit": (do_edit, "replace a line, for example: :edit 2     print(x)"),
    "ins": (do_ins, "add a line before line n, for example: :ins 1 import math"),
    "del": (do_del, "remove a line, for example: :del 2"),
    "wave": (do_wave, "go to another wave, for example: :wave 2"),
}


def first_unfinished_wave(state, level):
    """Return the number of the first wave of `level` that is not perfect (1 if all are)."""
    progress = state.progress_for(level)
    for number in range(1, len(level.waves) + 1):
        if not progress.wave_is_perfect(number, level.waves[number - 1]):
            return number
    return 1


def start_coding(state, level):
    """Put the player in code mode on the first unfinished wave of `level`."""
    state.current_level = level.id
    state.current_wave = first_unfinished_wave(state, level)
    state.coding = True
    state.wave_text(level, state.current_wave)

