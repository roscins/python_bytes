"""The quick console and :run: Python typed in the game.

Outside a wave, a typed line that is not a command is Python. It runs in
the quick console (runner/repl.py), which keeps the variables from line to
line, so `print("hi")` works everywhere. Inside a wave, :run tries the
code of the wave without grading it.

Some answers need more typing: the second line of a for loop, the new text
of :edit, the input of a program. The game remembers what it is waiting
for in state.pending (a dict with a "kind") and the next line goes there.
Like the other command modules, this one returns text and never prints.
"""

import builtins

from engine.data_files import written_lines
from engine.code_mode import (
    NOT_PLAYING,
    apply_edit,
    apply_insert,
    buffer_lines,
    current_context,
)
from engine.friendly import format_friendly, friendly_for_source, friendly_timeout
from engine.level_screen import separator
from engine.predict_lock import locked_message
from engine.suggest import MAP_WORDS, did_you_mean
from runner.process import DEFAULT_TIME_LIMIT, run_code
from runner.repl import ReplSession, classify

BLANK = "___"

# Characters that show that a line was meant as Python, not as a command.
PYTHON_SIGNS = "()[]{}=\"'"


def get_repl(state):
    """Return the game's quick console, starting it the first time it is needed."""
    if state.repl is None:
        state.repl = ReplSession(state.repl_timeout)
    state.repl.data = state.wave_files()
    return state.repl


def unknown_command_text(word):
    """Return the answer for a line that is neither a command nor Python."""
    return (f"Unknown command: {word}. Type help to see the commands."
            + did_you_mean(word, MAP_WORDS, colon=False))


def looks_like_python(line):
    """Return True if the line has signs of Python code: brackets, quotes or =."""
    for sign in PYTHON_SIGNS:
        if sign in line:
            return True
    return False


def syntax_error_text(source):
    """Return the text Python gives for the syntax error in `source`, like a traceback's last part."""
    try:
        compile(source, "<repl>", "single")
    except SyntaxError as error:
        return f'  File "<repl>", line {error.lineno or 1}\n{type(error).__name__}: {error.msg}'
    return ""


def show_error(state, source, error_text):
    """Return an error text as the friendly message, with the player's line and the real error."""
    error = friendly_for_source(error_text, source)
    return format_friendly(error, source, state.plain, state.color)


def run_python_line(state, line):
    """Handle a line that is not a command: run it, or wait for more lines of a block."""
    status = classify(line)
    if status == "invalid":
        if looks_like_python(line):
            return show_error(state, line, syntax_error_text(line))
        return unknown_command_text(line.split()[0])
    if status == "incomplete":
        state.pending = {"kind": "repl", "lines": [line]}
        return ""
    return run_source(state, line)


def run_source(state, source):
    """Run `source` in the quick console and return what to show."""
    locked = locked_message(state)
    if locked:
        # A single unknown word is a mistyped command, not code to refuse.
        word = source.strip()
        if word.isidentifier() and not hasattr(builtins, word):
            return unknown_command_text(word)
        return locked
    result = get_repl(state).run(source)
    parts = []
    if result.output:
        parts.append(result.output.rstrip("\n"))
    if result.output_cut:
        parts.append("(the output was too long and was cut)")
    if result.timed_out:
        parts.append(friendly_timeout(state.repl_timeout).headline)
        parts.append("The quick console was reset: your variables are gone.")
    elif result.was_reset:
        parts.append("The quick console was closed, so it starts again: your variables are gone.")
    elif result.error:
        parts.append(explain_console_error(state, source, result.error))
    return "\n".join(parts)


def explain_console_error(state, source, error_text):
    """Return the message for an error in the quick console.

    A single word that Python does not know is most likely a mistyped
    command, so it is answered like an unknown command.
    """
    word = source.strip()
    if word.isidentifier() and "NameError" in error_text:
        return unknown_command_text(word)
    return show_error(state, source, error_text)


def continue_repl(state, line):
    """Add a line to the block being typed; run it when it is finished."""
    lines = state.pending["lines"]
    if line.strip() == "":
        state.pending = None
        source = "\n".join(lines) + "\n"
    else:
        lines.append(line)
        source = "\n".join(lines)
        status = classify(source)
        if status == "incomplete":
            return ""
        state.pending = None
        if status == "invalid":
            return show_error(state, source, syntax_error_text(source))
    if classify(source) == "invalid":
        return show_error(state, source, syntax_error_text(source))
    return run_source(state, source)


def continue_edit(state, line):
    """Use the line that was typed as the new text of :edit or :ins; an empty line keeps the old one."""
    pending = state.pending
    state.pending = None
    if line.strip() == "":
        return "Kept the old code."
    if pending["kind"] == "edit":
        return apply_edit(state, pending["line"], line)
    return apply_insert(state, pending["line"], line)


def continue_run_input(state, line):
    """Collect the input lines for :run; an empty line starts the program."""
    pending = state.pending
    if line.strip() != "":
        pending["lines"].append(line)
        return ""
    state.pending = None
    level, number = current_context(state)
    if level is None:
        return NOT_PLAYING
    stdin_text = "\n".join(pending["lines"]) + "\n"
    return run_wave_code(state, state.wave_text(level, number), stdin_text)


def continue_pending(state, line):
    """Give a typed line to what the game is waiting for (see state.pending)."""
    kind = state.pending["kind"]
    if kind == "repl":
        return continue_repl(state, line)
    if kind == "run_input":
        return continue_run_input(state, line)
    return continue_edit(state, line)


def run_wave_code(state, code, stdin_text):
    """Run the code of a wave (not graded) and return what it printed, or the friendly error."""
    result = run_code(code, stdin_text, data=state.wave_files())
    locked = locked_message(state)
    if locked:
        return locked
    lines = ["RUN (this is not graded)"]
    if result.stdout.strip() != "":
        lines.append(result.stdout.rstrip("\n"))
    elif result.finished_cleanly():
        lines.append("(no output)")
    lines.extend(written_lines(result.written))
    if result.timed_out:
        lines.append(friendly_timeout(DEFAULT_TIME_LIMIT).headline)
    elif result.exit_code != 0:
        lines.append(show_error(state, code, result.stderr))
    return "\n".join(lines)


def do_run(state, text):
    """:run - try the code of this wave without grading it."""
    level, number = current_context(state)
    if level is None:
        return NOT_PLAYING
    wave = level.waves[number - 1]
    if wave.mode == "predict":
        return "Snek will not tell you what that code prints. Type your answer and :submit."
    if wave.is_quiz():
        return "There is nothing to run here. Write your answers, then :submit."
    locked = locked_message(state)
    if locked:
        return locked
    code = state.wave_text(level, number)
    if code.strip() == "":
        return "Your code is empty. Type your first line, then :run."
    if BLANK in code:
        return f"There is still a {BLANK} blank in your code. Replace it first, for example with :edit."
    if "input(" in code:
        state.pending = {"kind": "run_input", "lines": []}
        return ("This program asks for input. Type the lines it will read, one at a time. "
                "Press Enter on an empty line to run it.")
    return run_wave_code(state, code, "")


def do_cancel(state, text):
    """:cancel - stop what you were typing (the game has already done it; this is the answer)."""
    return "Nothing to cancel."
