"""Turn a graded submission into progress: best scores, stars, XP, coins and unlocks.

apply_submission is the only place where a submit changes the player's
progress. The rules themselves (weights, marks, prices) are in
engine/scoring.py.
"""

from engine.roadmap import is_written
from engine.scoring import (
    FIRST_TRY_COINS,
    GUESSES_BEFORE_REVEAL,
    QUALITY_COINS,
    QUALITY_GATE_SHARE,
    QUALITY_GATE_WORLD,
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
        is_cleared: True if the level is cleared now (this time or earlier).
        opened_level: the Level that opened because of it, or None.
        quality_blocked: True if low code quality keeps the level from clearing.
    """

    def __init__(self, best_score, old_best, stars, xp_gained, coins_gained, combo,
                 multiplier, cleared_now, opened_level, old_stars=0, is_cleared=False,
                 quality_blocked=False):
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
        self.is_cleared = is_cleared
        self.quality_blocked = quality_blocked


def has_build_wave(level):
    """Return True if the level has a build wave, which is scored on code quality."""
    for wave in level.waves:
        if wave.kind == "build":
            return True
    return False


def build_wave_number(level):
    """Return the number of the build wave (counting from 1), or 0 if there is none."""
    for number, wave in enumerate(level.waves, start=1):
        if wave.kind == "build":
            return number
    return 0


def quality_blocks_clear(level, progress):
    """Return True if the code quality is too low to clear this level."""
    if level.world < QUALITY_GATE_WORLD or not has_build_wave(level):
        return False
    return progress.passed_quality < QUALITY_GATE_SHARE


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


def all_waves_passed(progress):
    """Return True if every wave of the level has had all of its tests passed at least once.

    This is what clears a level. The score only decides the stars.
    """
    for best in progress.wave_best:
        if best < 1.0:
            return False
    return True


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

    # The third wrong prediction or answer sheet: the answer is shown and the wave is done.
    # A passed wave is never graded again, so every earlier attempt was wrong.
    if ((submission.wave.mode == "predict" or submission.wave.is_quiz())
            and not result.all_passed()
            and progress.wave_attempts[index] >= GUESSES_BEFORE_REVEAL):
        progress.revealed[index] = True
        progress.wave_best[index] = 1.0

    quality = result.quality_share()
    if quality is not None:
        if quality > progress.best_quality:
            progress.best_quality = quality
        if result.all_passed() and quality > progress.passed_quality:
            progress.passed_quality = quality
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
    score = level_score(level.waves, progress.scored_shares(), quality)
    if score > progress.best_score:
        progress.best_score = score

    multiplier = combo_multiplier(state.combo)
    xp_gained = xp_for(old_best, progress.best_score, multiplier)
    full_quality = not has_build_wave(level) or progress.passed_quality == 1.0
    new_stars = stars_for(progress.best_score, progress.hints_used(), full_quality)
    if new_stars > progress.stars:
        progress.stars = new_stars

    state.xp = state.xp + xp_gained
    state.coins = state.coins + coins

    blocked = quality_blocks_clear(level, progress)
    cleared_now = all_waves_passed(progress) and not blocked and level.id not in state.cleared
    opened_level = None
    if cleared_now:
        state.cleared.append(level.id)
        opened_level = next_level(state, level)

    return Reward(progress.best_score, old_best, progress.stars, xp_gained, coins,
                  state.combo, multiplier, cleared_now, opened_level, old_stars,
                  level.id in state.cleared, quality_blocked=blocked)
