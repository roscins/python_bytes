"""Hints: three per wave, bought with coins, cheapest first.

The first hint is a nudge, the second an outline of the approach and the
third a partial solution. A hint that was bought stays bought, so asking
again shows it for free. Any hint means the level can earn at most 2 stars.
"""

from engine.scoring import HINT_NAMES, HINT_PRICES


def hint_lines(wave, number, bought):
    """Return the lines showing the first `bought` hints of wave `number`."""
    lines = []
    for index in range(bought):
        lines.append(f"WAVE {number} · HINT {index + 1} of {len(HINT_NAMES)} ({HINT_NAMES[index]})")
        for line in wave.hints[index].splitlines():
            lines.append("  " + line)
    return lines


def ask_for_hint(state, level, number):
    """Buy the next hint for wave `number` of `level` if the player can; return the text to show.

    The hints already bought are shown again, followed by the new one.
    """
    wave = level.waves[number - 1]
    if not wave.hints:
        return f"Wave {number} has no hints."
    progress = state.progress_for(level)
    bought = progress.hints_bought[number - 1]

    if bought == len(HINT_NAMES):
        lines = hint_lines(wave, number, bought)
        lines.append("That was the last hint for this wave.")
        return "\n".join(lines)

    price = HINT_PRICES[bought]
    if state.coins < price:
        lines = hint_lines(wave, number, bought)
        lines.append(f"The next hint ({HINT_NAMES[bought]}) costs {price} coins, "
                     f"and you have {state.coins}. Pass waves on the first try to earn coins.")
        return "\n".join(lines)

    state.coins = state.coins - price
    bought = bought + 1
    progress.hints_bought[number - 1] = bought
    lines = hint_lines(wave, number, bought)
    lines.append(f"You paid {price} coins and have {state.coins} left. "
                 "With a hint, this level can earn at most 2 stars.")
    if bought < len(HINT_NAMES):
        lines.append(f"Type hint {number} again for the {HINT_NAMES[bought]} "
                     f"({HINT_PRICES[bought]} coins).")
    return "\n".join(lines)
