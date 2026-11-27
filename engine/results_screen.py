"""The text submit shows: which tests of each wave passed, and why others failed.

After the waves comes the score line: the level score, stars and coins
earned, and whether the level was cleared. Like the other screens, this
module returns text and never prints.
"""

from engine.friendly import friendly_error, friendly_message
from engine.scoring import star_text
from render.compare_view import compare_lines

TICK = "✓"
CROSS = "✗"


def check_lines(check):
    """Return the lines for one failed check: a cross, its name and why.

    Two outputs that differ are shown side by side.
    """
    lines = [f"  {CROSS} {check.name}"]
    if check.expected is not None:
        explanation = compare_lines(check.expected, check.printed)
    else:
        explanation = friendly_message(check.message).splitlines()
    for line in explanation:
        lines.append("      " + line)
    return lines


def syntax_lines(code):
    """Return where Python stopped reading `code`, with a ^ under the column, or []."""
    try:
        compile(code, "main.py", "exec")
    except SyntaxError as error:
        source = code.splitlines()
        if error.lineno is None or not 1 <= error.lineno <= len(source):
            return []
        start = f"{error.lineno:>3} | "
        column = max(0, (error.offset or 1) - 1)
        sentence = friendly_error(f'File "main.py", line {error.lineno}\n'
                                  f"{type(error).__name__}: {error.msg}").headline
        return ["  " + sentence, "  " + start + source[error.lineno - 1],
                "  " + " " * (len(start) + column) + "^"]
    return []


def wave_result_lines(submission):
    """Return the lines that report one graded wave."""
    title = f"WAVE {submission.number} · {submission.wave.kind.upper()}"
    result = submission.result
    if result is None:
        return [f"{title}  not started: type your code first"]

    mark = CROSS
    if result.all_passed():
        mark = TICK
    tests_word = "tests"
    if result.test_count() == 1:
        tests_word = "test"
    lines = [f"{title}  {result.passed_count()}/{result.test_count()} {tests_word} passed {mark}"]
    broken = []
    if submission.wave.mode != "predict":
        broken = syntax_lines(submission.code)
    if broken and "___" not in submission.code:
        # One explanation with the column; the tests only by name.
        lines.extend(broken)
        for check in result.checks:
            if not check.passed:
                lines.append(f"  {CROSS} {check.name}")
        return lines
    for check in result.checks:
        if not check.passed:
            lines.extend(check_lines(check))

    if result.quality is not None:
        passed = 0
        for rule in result.quality:
            if rule.passed:
                passed = passed + 1
        lines.append(f"  Code quality {passed}/{len(result.quality)}")
        already_said = [check.name for check in result.checks if not check.passed]
        for rule in result.quality:
            if not rule.passed and rule.name not in already_said:
                lines.extend(check_lines(rule))
    return lines


def reward_lines(level, reward):
    """Return the score lines shown after the waves."""
    lines = [f"LEVEL SCORE {reward.best_score} %  {star_text(reward.stars)}"]
    lines.append(f"+{reward.coins_gained} coins · combo {reward.combo}")
    if reward.cleared_now:
        cleared = f"LEVEL {level.id} CLEARED."
        if reward.opened_level is not None:
            cleared = cleared + f" Level {reward.opened_level.id} is open."
        lines.append(cleared)
    elif not reward.is_cleared:
        lines.append("Pass every wave to clear this level.")
    return lines


def results_text(level, submissions, perfect_numbers=(), reward=None):
    """Return the whole report for a submitted level, as one text.

    `perfect_numbers` are the waves that were not graded again because they
    already had full marks. With a Reward, the score lines come last.
    """
    lines = [f"LEVEL {level.id} · RESULTS", ""]
    graded = {}
    for submission in submissions:
        graded[submission.number] = submission
    for number in range(1, len(level.waves) + 1):
        if number in perfect_numbers:
            kind = level.waves[number - 1].kind.upper()
            lines.append(f"WAVE {number} · {kind}  already passed {TICK}")
        elif number in graded:
            lines.extend(wave_result_lines(graded[number]))
    if reward is not None:
        lines.append("")
        lines.extend(reward_lines(level, reward))
    return "\n".join(lines)
