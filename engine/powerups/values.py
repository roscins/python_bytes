"""The values of the variables a power-up expression uses.

At the map they are the quick console's variables. Inside a wave your code
is run in a separate process, and its variables are used.
"""

import ast

from runner.process import DEFAULT_TIME_LIMIT
from runner.repl import ReplSession

BLANK = "___"


class NotAllowed(Exception):
    """A power-up cannot do this; the message says why, for the player."""


def names_used(tree):
    """Return the variable names read by an expression (function names left out)."""
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            functions.append(node.func)
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node not in functions:
            names.append(node.id)
    return names


def plain_value(variable):
    """Return the number or text of a variable description, or raise NotAllowed."""
    name = variable["name"]
    kind = variable["type"]
    shown = variable["repr"]
    if kind == "str" and variable["text"] is not None:
        return variable["text"]
    if kind == "int" and len(shown) < 100:
        return int(shown)
    if kind == "float":
        return float(shown)
    if kind == "bool":
        return shown == "True"
    raise NotAllowed(f"calc and approx work with numbers and short text; {name} is something else.")


def console_variables(state):
    """Return the variable descriptions of the quick console."""
    if state.repl is None:
        return []
    return state.repl.variables()


def wave_variables(code):
    """Run `code` in a fresh console and return the variable descriptions it leaves."""
    if BLANK in code:
        raise NotAllowed(f"There is still a {BLANK} blank in your code. Replace it first.")
    session = ReplSession(DEFAULT_TIME_LIMIT)
    try:
        session.run(code, whole_program=True)
        return session.variables()
    finally:
        session.close()


def variable_values(state, tree):
    """Return {name: value} for the variables that `tree` uses and that exist."""
    wanted = names_used(tree)
    if not wanted:
        return {}
    level = state.find_level(state.current_level)
    if state.coding and level is not None:
        variables = wave_variables(state.wave_text(level, state.current_wave))
    else:
        variables = console_variables(state)
    values = {}
    for variable in variables:
        if variable["name"] in wanted:
            values[variable["name"]] = plain_value(variable)
    return values
