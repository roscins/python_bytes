"""The approx power-up: the number a float really stores.

approx works out one or two expressions the way calc does (without eval)
and shows every digit of the stored value, which decimal.Decimal gives
exactly. With two expressions it also compares them.
"""

import ast

from engine.powerups.calc import CAN_DO, MAX_LENGTH, check_allowed, steps_for, value_of
from engine.powerups.values import NotAllowed, variable_values
from render.approx_view import approx_view

USAGE = "Usage: approx 0.1 + 0.2, or to compare two: approx 0.1 + 0.2, 0.3"


def expressions_in(text):
    """Return the one or two expression trees written in `text`."""
    tree = ast.parse(text, mode="eval").body
    if not isinstance(tree, ast.Tuple):
        return [tree]
    if len(tree.elts) != 2:
        raise NotAllowed("approx takes one or two expressions.\n" + USAGE)
    return list(tree.elts)


def number_of(state, tree):
    """Work out one expression and return its value, which must be a number."""
    check_allowed(tree)
    steps, error = steps_for(ast.unparse(tree), variable_values(state, tree))
    if error is not None:
        raise NotAllowed(f"Python stops: {type(error).__name__}: {error}")
    value = value_of(ast.parse(steps[-1][0], mode="eval").body)
    if type(value) not in (int, float):
        raise NotAllowed("approx looks at numbers only.")
    return value


def do_approx(state, text):
    """approx <expression>[, <expression>] - show the stored digits."""
    if text == "":
        return USAGE
    if len(text) > MAX_LENGTH:
        return f"approx takes at most {MAX_LENGTH} characters."
    try:
        values = [number_of(state, tree) for tree in expressions_in(text)]
        return approx_view(values)
    except SyntaxError:
        return "Python cannot read that. " + USAGE
    except (NotAllowed, RecursionError) as problem:
        return str(problem).replace(CAN_DO, CAN_DO.replace("calc", "approx"))
