"""What the panel under the editor says after Submit or Run, and where the error is."""

import re

from engine.data_files import written_lines
from engine.friendly import PLAYER_FILES, friendly_for_source, friendly_timeout
from engine.results_screen import CROSS, TICK, results_text
from engine.scoring import GUESSES_BEFORE_REVEAL
from render.compare_view import first_difference
from render.editor_view import Mark
from runner.process import DEFAULT_TIME_LIMIT, run_code

GREY = "\x1b[90m"
RESET = "\x1b[0m"

# The width of the text inside the panel.
PANEL_TEXT_WIDTH = 74

TRACEBACK_PLACE = re.compile(r'^\s*File "([^"]+)", line (\d+)')


def column_of(error_text, code):
    """Return the column (from 0) a traceback points at with ^, or None if it does not say."""
    lines = error_text.splitlines()
    source = code.splitlines()
    found = None
    for index in range(len(lines)):
        place = TRACEBACK_PLACE.match(lines[index])
        if place is None or place.group(1).replace("\\", "/").split("/")[-1] not in PLAYER_FILES:
            continue
        found = None
        number = int(place.group(2))
        if index + 2 >= len(lines) or not 1 <= number <= len(source):
            continue
        under = lines[index + 2]
        if "^" not in under or under.strip(" ^~") != "":
            continue
        # Python shows the line without its own indentation, after 4 spaces.
        indent = len(source[number - 1]) - len(source[number - 1].lstrip())
        found = max(0, under.index("^") - 4 + indent)
    return found


def syntax_error_of(code):
    """Return Python's traceback-like text for a syntax error in `code`, or ""."""
    try:
        compile(code, "main.py", "exec")
    except SyntaxError as error:
        return f'File "main.py", line {error.lineno or 1}\n{type(error).__name__}: {error.msg}'
    return ""


def column_of_syntax_error(code):
    """Return the column (from 0) of the syntax error in `code`, or None."""
    try:
        compile(code, "main.py", "exec")
    except SyntaxError as error:
        if error.offset:
            return error.offset - 1
    return None


def grey_lines(text):
    """Return `text` as grey lines that fit in the panel."""
    lines = []
    for start in range(0, len(text), PANEL_TEXT_WIDTH):
        lines.append(f"{GREY}{text[start:start + PANEL_TEXT_WIDTH]}{RESET}")
    return lines


def explain_error(error_text, code):
    """Return (panel lines, Mark or None) for a traceback or a syntax error."""
    error = friendly_for_source(error_text, code)
    lines = [error.headline] + grey_lines(error.detail)
    if error.line is None:
        return lines, None
    if syntax_error_of(code):
        column = column_of_syntax_error(code)
    else:
        column = column_of(error_text, code)
    return lines, Mark(error.line - 1, column)


def error_text_of(result, code):
    """Return the error to explain for a graded wave: a syntax error, or a crash, or ""."""
    broken = syntax_error_of(code)
    if broken:
        return broken
    for check in result.checks:
        if check.error_text:
            return check.error_text
    return ""


def wrong_answer_mark(wave, answer):
    """Return the Mark on the first wrong line of a predicted output, or None."""
    expected = [line.rstrip() for line in wave.answer.rstrip("\n").split("\n")]
    typed = [line.rstrip() for line in answer.rstrip("\n").split("\n")]
    difference = first_difference(expected, typed)
    if difference is None:
        return None
    return Mark(min(difference[0], len(typed) - 1))


def submit_report(level, submission, reward, progress):
    """Return (panel lines, Mark or None) for a graded wave of a normal level."""
    wave = submission.wave
    result = submission.result
    mark = None
    lines = []
    # The first two lines are the heading, which the panel's title replaces.
    full = results_text(level, [submission], [], reward)[len(f"LEVEL {level.id} · RESULTS\n\n"):]
    error_text = ""
    if wave.mode is None and "___" not in submission.code:
        error_text = error_text_of(result, submission.code)
    if error_text:
        lines, mark = explain_error(error_text, submission.code)
        lines.append(f"{result.passed_count()}/{result.test_count()} tests passed {CROSS}")
        for check in result.checks:
            if not check.passed:
                lines.append(f"  {CROSS} {check.name}")
    else:
        lines = full.split("\n")
        if wave.mode == "predict" and not result.all_passed():
            mark = wrong_answer_mark(wave, submission.code)
    number = submission.number
    if result.all_passed():
        lines.insert(0, f"{TICK} Wave {number} passed!")
    elif progress.revealed[number - 1]:
        lines.insert(0, f"Wave {number} is done: Snek shows the output below.")
    elif wave.mode == "predict" or wave.is_quiz():
        left = GUESSES_BEFORE_REVEAL - progress.wave_attempts[number - 1]
        lines.insert(0, f"Not yet. Wrong guesses left before Snek shows the output: {left}")
    else:
        lines.insert(0, "Not yet. Fix it and press Ctrl-S again. Ctrl-T buys a hint.")
    return lines, mark


def run_report(code, stdin_text="", data=None):
    """Run `code` without grading; return (panel lines, Mark or None)."""
    result = run_code(code, stdin_text, data=data)
    lines = []
    mark = None
    if result.stdout.strip() != "":
        lines = result.stdout.rstrip("\n").split("\n")
    elif result.finished_cleanly():
        lines = ["(no output)"]
    lines.extend(written_lines(result.written))
    if result.timed_out:
        lines.append(friendly_timeout(DEFAULT_TIME_LIMIT).headline)
    elif result.exit_code != 0:
        explained, mark = explain_error(syntax_error_of(code) or result.stderr, code)
        lines = lines + explained
    return lines, mark
