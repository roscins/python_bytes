"""The text submit shows: which tests of each wave passed, and why others failed.

Like the other screens, this module returns text and never prints.
"""

PASS_MARK = "✓"
FAIL_MARK = "✗"


def check_lines(check):
    """Return the lines for one failed check: a cross, its name and its message."""
    lines = [f"  {FAIL_MARK} {check.name}"]
    for line in check.message.splitlines():
        lines.append("      " + line)
    return lines


def wave_result_lines(submission):
    """Return the lines that report one graded wave."""
    title = f"WAVE {submission.number} · {submission.wave.kind.upper()}"
    result = submission.result
    if result is None:
        return [f"{title}  not started: write it in {submission.file_name}"]

    mark = FAIL_MARK
    if result.all_passed():
        mark = PASS_MARK
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


def results_text(level, submissions):
    """Return the whole report for a submitted level, as one text."""
    lines = [f"LEVEL {level.id} · RESULTS", ""]
    for submission in submissions:
        lines.extend(wave_result_lines(submission))
    return "\n".join(lines)
