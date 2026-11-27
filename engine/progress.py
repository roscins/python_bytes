"""The player's progress in one level: best results, attempts and hints bought."""

from engine.scoring import REVEALED_SHARE


class LevelProgress:
    """Everything the game remembers about one level the player has worked on.

    Each list has one entry per wave, in wave order.

    Attributes:
        wave_best: the best share of tests passed in each wave (0.0 to 1.0).
        wave_attempts: how many times each wave has been graded.
        hints_bought: how many hints (0 to 3) were bought for each wave.
        best_quality: the best code-quality share of the build wave.
        passed_quality: the best code-quality share of build code that passed
            every test.
        quality_rewarded: True once the coins for full quality were given.
        best_score: the best level score, a whole percent.
        stars: the most stars earned (0 to 3).
        revealed: True for a predict wave whose answer the game showed.
    """

    def __init__(self, wave_count):
        """Start with no progress in a level of `wave_count` waves."""
        self.wave_best = [0.0] * wave_count
        self.wave_attempts = [0] * wave_count
        self.hints_bought = [0] * wave_count
        self.best_quality = 0.0
        self.passed_quality = 0.0
        self.quality_rewarded = False
        self.best_score = 0
        self.stars = 0
        self.revealed = [False] * wave_count

    def scored_shares(self):
        """Return the share of each wave that counts: less for a revealed answer."""
        shares = []
        for index in range(len(self.wave_best)):
            if self.revealed[index]:
                shares.append(REVEALED_SHARE)
            else:
                shares.append(self.wave_best[index])
        return shares

    def hints_used(self):
        """Return True if any hint was bought in this level."""
        return sum(self.hints_bought) > 0

    def wave_is_perfect(self, number, wave):
        """Return True if wave `number` (counting from 1) needs no more work.

        A wave is perfect when all of its tests passed, and for a build wave
        also every code-quality rule.
        """
        if self.wave_best[number - 1] < 1.0:
            return False
        if wave.kind == "build" and self.best_quality < 1.0:
            return False
        return True

    def to_dict(self):
        """Return the progress as a dict that can be written to JSON."""
        return {
            "wave_best": self.wave_best,
            "wave_attempts": self.wave_attempts,
            "hints_bought": self.hints_bought,
            "best_quality": self.best_quality,
            "passed_quality": self.passed_quality,
            "quality_rewarded": self.quality_rewarded,
            "best_score": self.best_score,
            "stars": self.stars,
            "revealed": self.revealed,
        }


def fit_list(values, length):
    """Return `values` cut or padded with zeros to `length` items.

    Used when a level gained or lost waves since the save was written.
    """
    fitted = list(values[:length])
    while len(fitted) < length:
        fitted.append(0)
    return fitted


def is_number(value):
    """Return True if `value` is an int or a float, but not True or False."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def progress_from_dict(data, wave_count):
    """Return a LevelProgress read from a dict made by to_dict.

    Raises ValueError if a part is missing or has the wrong type.
    """
    if not isinstance(data, dict):
        raise ValueError("level progress must be a JSON object")
    progress = LevelProgress(wave_count)
    for key in ["wave_best", "wave_attempts", "hints_bought"]:
        values = data.get(key)
        if not isinstance(values, list):
            raise ValueError(f"{key} must be a list")
        for value in values:
            if not is_number(value):
                raise ValueError(f"{key} must be a list of numbers")
    for key in ["best_quality", "best_score", "stars"]:
        if not is_number(data.get(key)):
            raise ValueError(f"{key} must be a number")
    if not isinstance(data.get("quality_rewarded"), bool):
        raise ValueError("quality_rewarded must be true or false")

    progress.wave_best = fit_list(data["wave_best"], wave_count)
    progress.wave_attempts = fit_list(data["wave_attempts"], wave_count)
    progress.hints_bought = fit_list(data["hints_bought"], wave_count)
    progress.best_quality = data["best_quality"]
    # Older saves have no "passed_quality": their best quality stands in.
    passed_quality = data.get("passed_quality", data["best_quality"])
    if not is_number(passed_quality):
        raise ValueError("passed_quality must be a number")
    progress.passed_quality = passed_quality
    progress.quality_rewarded = data["quality_rewarded"]
    progress.best_score = data["best_score"]
    progress.stars = data["stars"]
    # Saves from before answers could be revealed have no "revealed" list.
    revealed = data.get("revealed", [])
    if not isinstance(revealed, list) or not all(isinstance(value, bool) for value in revealed):
        raise ValueError("revealed must be a list of true or false")
    progress.revealed = [bool(value) for value in fit_list(revealed, wave_count)]
    return progress
