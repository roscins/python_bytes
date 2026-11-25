"""The text submit shows: which tests of each wave passed, and why others failed.

After the waves comes the score line: the level score, stars, XP and coins
earned, and whether the level was cleared. Like the other screens, this
module returns text and never prints.
"""

from engine.scoring import PASS_MARK, star_text

TICK = "✓"
CROSS = "✗"


def check_lines(check):
    """Return the lines for one failed check: a cross, its name and its message."""
    lines = [f"  {CROSS} {check.name}"]
    for line in check.message.splitlines():
        lines.append("      " + line)
    return lines


def wave_result_lines(submission):
    """Return the lines that report one graded wave."""
    title = f"WAVE {submission.number} · {submission.wave.kind.upper()}"
    result = submission.result
    if result is None:
        return [f"{title}  not started: write it in {submission.file_name}"]

    mark = CROSS
    if result.all_passed():
        mark = TICK
    tests_word = "tests"
    if result.test_count() == 1:
        tests_word = "test"
    lines = [f"{title}  {result.passed_count()}/{result.test_count()} {tests_word} passed {mark}"]
    for check in result.checks:
        if not check.passed:
            lines.extend(check_lines(check))

    if result.quality is not None:
        passed = 0
        for rule in result.quality:
            if rule.passed:
                passed = passed + 1
        lines.append(f"  Code quality {passed}/{len(result.quality)}")
        for rule in result.quality:
            if not rule.passed:
                lines.extend(check_lines(rule))
    return lines


def multiplier_text(multiplier):
    """Return an XP multiplier as text: "×1.5", or "×2" without a needless ".0"."""
    if multiplier == int(multiplier):
        return f"×{int(multiplier)}"
    return f"×{multiplier}"


def reward_lines(level, reward):
    """Return the score lines shown after the waves."""
    lines = [f"LEVEL SCORE {reward.best_score} %  {star_text(reward.stars)}"]
    gains = f"+{reward.xp_gained} XP · +{reward.coins_gained} coins · combo {reward.combo}"
    if reward.multiplier > 1:
        gains = gains + f" (XP {multiplier_text(reward.multiplier)})"
    lines.append(gains)
    if reward.cleared_now:
        cleared = f"LEVEL {level.id} CLEARED."
        if reward.opened_level is not None:
            cleared = cleared + f" Level {reward.opened_level.id} is open."
        lines.append(cleared)
    elif reward.best_score < PASS_MARK:
        lines.append(f"You need {PASS_MARK} % to clear this level. Fix the waves marked ✗ "
                     "and submit again.")
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
