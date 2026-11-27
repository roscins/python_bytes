"""Grade one wave: run all of its tests on what the player wrote.

grade_wave(wave, text) is the grader's front door. `text` is the player's
code, or for a predict wave the output they predicted. The result says
which checks passed, and for a build wave also the code-quality rules.
"""

from grader.checks import CheckResult, normalise_output, run_check
from grader.style import style_checks
from runner.process import DEFAULT_TIME_LIMIT

# The blank that fill-in starters use for the parts the player fills in.
BLANK = "___"


class WaveResult:
    """The result of grading one wave.

    Attributes:
        checks: a list of CheckResults, one per test.
        quality: a list of CheckResults, one per code-quality rule, for a
            build wave; None for other waves.
    """

    def __init__(self, checks, quality=None):
        """Remember the checks and the quality rules."""
        self.checks = list(checks)
        self.quality = quality

    def passed_count(self):
        """Return how many checks passed."""
        count = 0
        for check in self.checks:
            if check.passed:
                count = count + 1
        return count

    def test_count(self):
        """Return how many checks there were."""
        return len(self.checks)

    def all_passed(self):
        """Return True if every check passed."""
        return self.test_count() > 0 and self.passed_count() == self.test_count()

    def share_passed(self):
        """Return the share of checks that passed, from 0.0 to 1.0."""
        if self.test_count() == 0:
            return 0.0
        return self.passed_count() / self.test_count()

    def quality_share(self):
        """Return the share of code-quality rules passed, from 0.0 to 1.0, or None."""
        if self.quality is None:
            return None
        passed = 0
        for rule in self.quality:
            if rule.passed:
                passed = passed + 1
        return passed / len(self.quality)


def check_answer(wave, answer):
    """Compare a predicted output with the wave's right answer."""
    name = "predicts the output"
    if answer.strip() == "":
        return CheckResult(False, name, "Your answer is empty.")
    if normalise_output(answer) == normalise_output(wave.answer):
        return CheckResult(True, name)
    return CheckResult(False, name, "That is not what this program prints. "
                                    "Go through it line by line, then try again.")


def grade_wave(wave, text):
    """Grade the player's `text` for `wave` and return a WaveResult."""
    if wave.mode == "predict":
        return WaveResult([check_answer(wave, text)])

    if wave.kind == "fill-in" and BLANK in text:
        blank_left = CheckResult(False, "fills in every blank",
                                 f"There is still a {BLANK} blank in your code. Replace it first.")
        return WaveResult([blank_left])

    time_limit = DEFAULT_TIME_LIMIT
    if wave.time_limit is not None:
        time_limit = wave.time_limit
    checks = []
    for test in wave.tests:
        checks.append(run_check(test, text, time_limit))
    quality = None
    if wave.kind == "build":
        quality = style_checks(text)
    return WaveResult(checks, quality)
