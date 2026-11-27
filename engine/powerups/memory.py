"""The memory power-up: which names point to which values.

At the map it draws the variables of the quick console. Inside a wave it
runs the code you have typed, in a separate process, and draws the
variables that are left at the end.
"""

from engine.friendly import format_friendly, friendly_error, friendly_timeout
from render.memory_view import memory_view
from runner.process import DEFAULT_TIME_LIMIT
from runner.repl import ReplSession

BLANK = "___"


def wave_memory(state, code):
    """Run `code` in a fresh console and return the drawing of what it leaves behind."""
    if BLANK in code:
        return f"There is still a {BLANK} blank in your code. Replace it first."
    session = ReplSession(DEFAULT_TIME_LIMIT)
    try:
        result = session.run(code, whole_program=True)
        if result.timed_out:
            return friendly_timeout(DEFAULT_TIME_LIMIT).headline
        if result.was_reset:
            return "Your code closed Python, so there is nothing to draw."
        lines = [memory_view(session.variables())]
        if result.error:
            lines.append("")
            lines.append("The drawing shows memory at the moment your code stopped:")
            lines.append(format_friendly(friendly_error(result.error), code, state.plain, state.color))
        return "\n".join(lines)
    finally:
        session.close()


def do_memory(state, text):
    """memory - draw names and values."""
    if text != "":
        return "memory takes nothing after it. Type just: memory"
    level = state.find_level(state.current_level)
    if state.coding and level is not None:
        return wave_memory(state, state.wave_text(level, state.current_wave))
    variables = []
    if state.repl is not None:
        variables = state.repl.variables()
    return memory_view(variables)
