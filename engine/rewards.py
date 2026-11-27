"""Turn a graded submission into progress: best scores, stars, XP, coins and unlocks.

apply_submission is the only place where a submit changes the player's
progress. The rules themselves (weights, marks, prices) are in
engine/scoring.py.
"""

from engine.roadmap import is_written
from engine.scoring import (
    FIRST_TRY_COINS,
    PASS_MARK,
    QUALITY_COINS,
    combo_multiplier,
    level_score,
    stars_for,
    xp_for,
)


class Reward:
    """What one submit earned, for the screen that shows it.

    Attributes:
        best_score: the level's best score after this submit.
        old_best: the best score before it.
        stars: the stars the level has now (0 to 3).
        old_stars: the stars it had before this submit.
        xp_gained: the XP earned by this submit.
        coins_gained: the coins earned by this submit.
        combo: the combo after this submit.
        multiplier: the XP multiplier that combo gives.
        cleared_now: True if this submit cleared the level for the first time.
        opened_level: the Level that opened because of it, or None.
    """

    def __init__(self, best_score, old_best, stars, xp_gained, coins_gained, combo,
                 multiplier, cleared_now, opened_level, old_stars=0):
        """Remember every part of the reward."""
        self.best_score = best_score
        self.old_best = old_best
        self.stars = stars
        self.old_stars = old_stars
        self.xp_gained = xp_gained
        self.coins_gained = coins_gained
        self.combo = combo
        self.multiplier = multiplier
        self.cleared_now = cleared_now
        self.opened_level = opened_level


def has_build_wave(level):
    """Return True if the level has a build wave, which is scored on code quality."""
    for wave in level.waves:
        if wave.kind == "build":
            return True
    return False


def next_level(state, level):
    """Return the level after `level` in map order, or None if there is none to open.

    A level that the curriculum lists but that has no pack yet does not
    count: nothing opens.
    """
    slots = state.slots()
    for index in range(len(slots) - 1):
        if slots[index].id == level.id:
            following = slots[index + 1]
            if is_written(following):
                return following
            return None
    return None


def update_wave(state, progress, submission):
    """Record one graded wave in `progress`; return the coins it earned.

    Also moves the combo: a wave passed on its first graded attempt adds 1,
    and any other result sets the combo back to 0.
    """
    index = submission.number - 1
    result = submission.result
    first_try = progress.wave_attempts[index] == 0
    progress.wave_attempts[index] = progress.wave_attempts[index] + 1
    if result.share_passed() > progress.wave_best[index]:
        progress.wave_best[index] = result.share_passed()

    coins = 0
    if result.all_passed() and first_try:
        state.combo = state.combo + 1
        coins = coins + FIRST_TRY_COINS
    else:
        state.combo = 0

    quality = result.quality_share()
    if quality is not None:
        if quality > progress.best_quality:
            progress.best_quality = quality
        if progress.best_quality == 1.0 and not progress.quality_rewarded:
            progress.quality_rewarded = True
            coins = coins + QUALITY_COINS
    return coins


def apply_submission(state, level, submissions):
    """Update the player's progress after `submissions` of `level` were graded.

    Waves that were not started (their result is None) change nothing.
    Returns a Reward.
    """
    progress = state.progress_for(level)
    old_best = progress.best_score
    old_stars = progress.stars

    coins = 0
    for submission in submissions:
        if submission.result is not None:
            coins = coins + update_wave(state, progress, submission)

    quality = None
    if has_build_wave(level):
        quality = progress.best_quality
    score = level_score(level.waves, progress.wave_best, quality)
    if score > progress.best_score:
        progress.best_score = score

    multiplier = combo_multiplier(state.combo)
    xp_gained = xp_for(old_best, progress.best_score, multiplier)
    new_stars = stars_for(progress.best_score, progress.hints_used())
    if new_stars > progress.stars:
        progress.stars = new_stars

    state.xp = state.xp + xp_gained
    state.coins = state.coins + coins

    cleared_now = progress.best_score >= PASS_MARK and level.id not in state.cleared
    opened_level = None
    if cleared_now:
        state.cleared.append(level.id)
        opened_level = next_level(state, level)

    return Reward(progress.best_score, old_best, progress.stars, xp_gained, coins,
                  state.combo, multiplier, cleared_now, opened_level, old_stars)
