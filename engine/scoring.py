"""The game's scoring rules: level scores, stars, XP, combos and unlocking.

Every number the game rewards with lives here as a constant, so the game
can be balanced in one place (Phase 8 of the plan). The functions are small
and do no input or output, so they are easy to test.
"""

# How much each wave counts towards the level score. Code quality is
# scored on the build wave.
WAVE_WEIGHTS = {"fill-in": 20, "build": 50, "debug": 15}
QUALITY_WEIGHT = 15

# A level is cleared, and the next one opens, at this score or more.
PASS_MARK = 70
TWO_STAR_MARK = 85
THREE_STAR_MARK = 100
MAX_STARS = 3

# From this world on, a level with a build wave also needs this share of the
# code-quality rules to be cleared.
QUALITY_GATE_WORLD = 3
QUALITY_GATE_SHARE = 0.5

# XP for each score point gained over the player's best.
XP_PER_POINT = 10

# The combo multiplies XP: (first-try waves in a row needed, multiplier),
# from the biggest to the smallest.
COMBO_STEPS = [(5, 2.0), (3, 1.5)]

# Coins for passing a wave on the first try, and for full code quality.
FIRST_TRY_COINS = 5
QUALITY_COINS = 5

# A new player starts with enough coins for one nudge.
STARTING_COINS = 10

# A predict wave shows its answer after this many wrong guesses, and then
# counts at this share of its score.
GUESSES_BEFORE_REVEAL = 3
REVEALED_SHARE = 0.5

# The three hint levels, cheapest first, with their prices in coins.
HINT_NAMES = ["nudge", "outline", "partial solution"]
HINT_PRICES = [5, 15, 30]


def level_score(waves, wave_shares, quality_share):
    """Return the level score, a whole percent from 0 to 100.

    `waves` are the level's Wave objects and `wave_shares` the share of
    tests passed in each (0.0 to 1.0). `quality_share` is the build wave's
    code-quality share, or None if the level has no build wave. Waves of a
    kind with no weight (for example a boss wave) count like a build wave.
    """
    total_weight = 0
    points = 0.0
    for index in range(len(waves)):
        weight = WAVE_WEIGHTS.get(waves[index].kind, WAVE_WEIGHTS["build"])
        total_weight = total_weight + weight
        points = points + weight * wave_shares[index]
    if quality_share is not None:
        total_weight = total_weight + QUALITY_WEIGHT
        points = points + QUALITY_WEIGHT * quality_share
    if total_weight == 0:
        return 0
    return round(100 * points / total_weight)


def stars_for(score, hints_used, full_quality=True):
    """Return the stars (0 to 3) for a level score.

    1 star at 70 %, 2 stars at 85 %, 3 stars only at 100 % with no hints and
    full code quality.
    """
    if score >= THREE_STAR_MARK and not hints_used and full_quality:
        return 3
    if score >= TWO_STAR_MARK:
        return 2
    if score >= PASS_MARK:
        return 1
    return 0


def combo_multiplier(combo):
    """Return the XP multiplier for a combo of `combo` first-try waves in a row."""
    for needed, multiplier in COMBO_STEPS:
        if combo >= needed:
            return multiplier
    return 1.0


def xp_for(old_best, new_best, multiplier):
    """Return the XP for raising the best score from `old_best` to `new_best`.

    No XP is given unless the best score went up, so replaying a level
    cannot farm XP.
    """
    if new_best <= old_best:
        return 0
    return round(XP_PER_POINT * (new_best - old_best) * multiplier)


def is_unlocked(levels, cleared, level):
    """Return True if `level` is open to play.

    The first level is always open. Every other level opens when the level
    before it in map order has been cleared (`cleared` is a list of ids).
    """
    for index in range(len(levels)):
        if levels[index].id == level.id:
            if index == 0:
                return True
            return levels[index - 1].id in cleared
    return False


def star_text(stars):
    """Return stars as text, for example "★★☆" for 2 of 3."""
    return "★" * stars + "☆" * (MAX_STARS - stars)
