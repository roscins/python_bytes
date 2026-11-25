"""The state of one boss fight: lives, the boss's health and the time limit.

A boss's health is made of its hidden tests: every test the player's code
passes knocks off one block. Each failed submit costs a life; with no lives
left, or when the time runs out, the fight starts again. Losing restarts
the fight, not the world.
"""

import time

from render.boss_screen import LIVES_TOTAL

# What submit_result can say happened.
WON = "won"
HIT = "hit"
RESTART = "restart"
TIMEOUT = "timeout"


class BossFight:
    """One boss fight in progress.

    Attributes:
        level: the boss Level being fought.
        clock: a function that returns the time in seconds. It is
            time.monotonic in the game; tests pass their own clock.
        lives: the lives the player has left.
        hp_total: the boss's full health: the number of hidden tests.
        hp_left: the tests still failing in the player's best attempt.
        started_at: the clock's time when this fight (or restart) began.
    """

    def __init__(self, level, clock=time.monotonic):
        """Start a fight against `level` with full lives and full health."""
        self.level = level
        self.clock = clock
        self.hp_total = len(level.waves[0].tests)
        self.restart()

    def restart(self):
        """Start the fight again: full lives, full health and a new timer."""
        self.lives = LIVES_TOTAL
        self.hp_left = self.hp_total
        self.started_at = self.clock()

    def time_left(self):
        """Return the seconds left before the time runs out (never below 0)."""
        left = self.level.time_limit - (self.clock() - self.started_at)
        if left < 0:
            return 0
        return left

    def time_is_up(self):
        """Return True if the time limit has passed."""
        return self.time_left() <= 0

    def submit_result(self, result):
        """Update the fight with a graded WaveResult and return what happened.

        Returns WON if every hidden test passed, HIT if the player lost a
        life, or RESTART if that was the last life (the fight is then
        started again).
        """
        still_failing = result.test_count() - result.passed_count()
        if still_failing < self.hp_left:
            self.hp_left = still_failing
        if result.all_passed():
            return WON
        self.lives = self.lives - 1
        if self.lives == 0:
            self.restart()
            return RESTART
        return HIT
