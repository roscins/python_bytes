"""What play and submit do in a boss level.

Starting a boss level begins a BossFight (engine/boss.py). Each submit
grades the player's file against the boss's hidden tests, drains the health
bar, and uses up a try if any test still fails. Winning clears the boss
level through the same apply_submission as normal levels, so XP, coins and
unlocking work the same.
"""

from engine.boss import RESTART, WON, BossFight
from engine.friendly import friendly_message
from engine.results_screen import reward_lines
from engine.rewards import apply_submission
from engine.submission import grade_text
from render.boss_screen import boss_screen, hp_drain_frames, load_boss_art

# Messages that explain a crash or unreadable code. They say nothing about
# the hidden tests, so they can be shown in a boss fight.
SAFE_MESSAGE_STARTS = [
    "Your program stopped with an error",
    "Your program ran for more than",
    "Python cannot read your code",
    "Your code has no function named",
]


def current_screen(fight):
    """Return the boss screen for the fight as it is now."""
    level = fight.level
    art = load_boss_art(level.sprite)
    return boss_screen(level.id, level.title, fight.hp_left, fight.hp_total, fight.lives,
                       fight.time_left(), art)


def start_boss_fight(state, level):
    """Begin a new fight against `level` and return its boss screen."""
    state.boss_fight = BossFight(level)
    return current_screen(state.boss_fight)


def safe_problem(result):
    """Return the first message that explains a crash or unreadable code, or ""."""
    for check in result.checks:
        if check.passed:
            continue
        for start in SAFE_MESSAGE_STARTS:
            if check.message.startswith(start):
                return check.message
    return ""


def submit_to_boss(state, level):
    """Grade the player's boss file and update the fight; return text or frames to show."""
    fight = state.boss_fight
    if fight is None or fight.level.id != level.id:
        # For example after quitting and starting the game again.
        fight = BossFight(level)
        state.boss_fight = fight

    if fight.time_is_up():
        fight.restart()
        return (current_screen(fight)
                + "\n\nTIME'S UP. The fight starts again: 3 tries, full health and a new timer.")

    submission = grade_text(level.waves[0], 1, state.wave_text(level, 1))
    submissions = [submission]
    if submission.result is None:
        return "Type your code first, then :submit."

    hp_before = fight.hp_left
    lives_before = fight.lives
    outcome = fight.submit_result(submission.result)
    art = load_boss_art(level.sprite)

    if outcome == WON:
        reward = apply_submission(state, level, submissions)
        state.boss_fight = None
        frames = hp_drain_frames(level.id, level.title, hp_before, 0, fight.hp_total,
                                 lives_before, fight.time_left(), art)
        lines = ["BOSS DEFEATED."]
        lines.extend(reward_lines(level, reward))
        frames[-1] = frames[-1] + "\n\n" + "\n".join(lines)
        return frames

    # Otherwise the outcome is HIT (a life lost) or RESTART (the last life lost).
    if outcome == RESTART:
        message = "The boss knocked you out. The fight starts again: 3 tries, full health."
        frames = [current_screen(fight)]
    else:
        frames = hp_drain_frames(level.id, level.title, hp_before, fight.hp_left,
                                 fight.hp_total, fight.lives, fight.time_left(), art)
        message = (f"HIT! {fight.hp_left} hidden tests still failing. "
                   f"One try is used up: {fight.lives} left.")
    problem = safe_problem(submission.result)
    if problem:
        message = message + "\n" + friendly_message(problem)
    frames[-1] = frames[-1] + "\n\n" + message
    return frames
