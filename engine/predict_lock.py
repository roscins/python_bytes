"""While a predict wave is unanswered, the game does not run code for the player.

A predict wave asks what a program prints, so being able to run it would
give the answer away. The wave is unanswered from the moment the player
first sees it until they pass it. "Seen" means the wave has a code buffer,
and buffers are saved, so restarting the game does not lift the lock.
"""


def unanswered_predict(state):
    """Return (level, wave number) of a predict wave seen but not passed, or None."""
    for level in state.levels:
        for number in sorted(state.buffers.get(level.id, {})):
            wave = level.waves[number - 1]
            if wave.mode != "predict":
                continue
            progress = state.progress.get(level.id)
            if progress is None or not progress.wave_is_perfect(number, wave):
                return level, number
    return None


def locked_message(state):
    """Return why code cannot run now, or "" if it can."""
    found = unanswered_predict(state)
    if found is None:
        return ""
    level, number = found
    return (f"Snek will not run code while a prediction is open. First answer wave {number} "
            f"of {level.id}: play {level.id}, then :wave {number}.")
