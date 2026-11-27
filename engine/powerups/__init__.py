"""Power-ups: small tools that show the idea a level has just taught.

See docs/design/phase-3-power-ups.md. A power-up is earned by clearing the
level that names it (power_up in level.toml). It is typed at the map as
"read ..." and inside a wave as ":read ...". Each tool has its own module
here; the table of tools is below.
"""

from engine.powerups.calc import do_calc
from engine.powerups.memory import do_memory
from engine.powerups.read import do_read
from engine.predict_lock import locked_message
from engine.predict_lock import unanswered_predict

# What may follow a name in a line of Python that assigns to it, as in "read = 5".
ASSIGNMENT_STARTS = ["+=", "-=", "*=", "/=", "//=", "%=", "**=", "|=", "&=", "^=", ","]


class PowerUp:
    """One tool.

    Attributes:
        function: takes (state, text after the name) and returns the answer.
        description: the line shown by help.
        runs_code: takes the state and says whether using the tool now would
            run the player's code.
    """

    def __init__(self, function, description, runs_code):
        """Remember the three parts of the tool."""
        self.function = function
        self.description = description
        self.runs_code = runs_code


def never(state):
    """Return False: for tools that only look and never run code."""
    return False


def inside_a_wave(state):
    """Return True while coding: then memory runs the wave's code."""
    return state.coding


def always(state):
    """Return True: calc works out code wherever it is used."""
    return True


POWER_UPS = {
    "calc": PowerUp(do_calc, "shows the order of working out, for example: calc 2 + 3 * 4", always),
    "memory": PowerUp(do_memory, "draws which names point to which values", inside_a_wave),
    "read": PowerUp(do_read, 'index numbers under a text, for example: read "ABC" [0:2]', never),
}


def is_python_line(rest):
    """Return True if `rest` (what follows the name) shows the line is Python, like "= 5"."""
    rest = rest.lstrip()
    if rest.startswith("=") and not rest.startswith("=="):
        return True
    for start in ASSIGNMENT_STARTS:
        if rest.startswith(start):
            return True
    return False


def level_that_gives(state, name):
    """Return the level whose power-up is `name`, or None if no level pack has it."""
    for level in state.levels:
        if level.power_up == name:
            return level
    return None


def is_earned(state, name):
    """Return True if the player has cleared the level that gives this power-up."""
    level = level_that_gives(state, name)
    return level is not None and level.id in state.cleared


def in_open_prediction(state):
    """Return True if the player is inside a predict wave that is not passed yet."""
    found = unanswered_predict(state)
    if found is None or not state.coding:
        return False
    level = state.find_level(state.current_level)
    if level is None:
        return False
    wave = level.waves[state.current_wave - 1]
    if wave.mode != "predict":
        return False
    return not state.progress_for(level).wave_is_perfect(state.current_wave, wave)


def use_power_up(state, name, text):
    """Use the power-up `name` on `text`, or say why it cannot be used now."""
    power_up = POWER_UPS[name]
    if not is_earned(state, name):
        level = level_that_gives(state, name)
        if level is None:
            return f"You have not earned {name} yet."
        return f"Clear {level.id} to earn {name}."
    if in_open_prediction(state):
        return "Snek will not help with a prediction. Type your answer and :submit."
    if power_up.runs_code(state):
        locked = locked_message(state)
        if locked:
            return locked
    return power_up.function(state, text.strip())


def earned_help_lines(state):
    """Return the help lines of the power-ups the player has earned."""
    lines = []
    for name in POWER_UPS:
        if is_earned(state, name):
            lines.append(f"  {name:<8} {POWER_UPS[name].description}")
    if lines:
        lines.insert(0, "Power-ups you have earned (with a colon while coding):")
    return lines
