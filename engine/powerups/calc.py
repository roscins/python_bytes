"""The calc power-up: show the order in which Python works out an expression.

calc does not use eval. It reads the expression into Python's syntax tree
and works out one part at a time, in the order Python does: the left side
completely, then the right side, then the operation between them. Each step
is shown with the part about to be worked out underlined.
"""

import ast
import math
import operator

from engine.powerups.values import NotAllowed, variable_values
from render.calc_view import calc_view

USAGE = "Usage: calc followed by an expression, for example: calc (74 - 2) * 3 + 10 // 4"
CAN_DO = "calc knows numbers, text, + - * / // % **, brackets, int(), float(), str() and round()."

MAX_LENGTH = 70             # of an expression, so every step fits on one line
MAX_INT_BITS = 2000         # about 600 digits
MAX_ROUND_DIGITS = 100
MAX_STEPS = 100             # a safety net: no line of 70 characters needs more

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
FUNCTIONS = {"int": int, "float": float, "str": str, "round": round}


def is_value(node):
    """Return True if `node` needs no more work: a literal, or a minus sign before a number."""
    if isinstance(node, ast.Constant):
        return True
    return (isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub)
            and isinstance(node.operand, ast.Constant)
            and type(node.operand.value) in (int, float))


def value_of(node):
    """Return the value written by a node for which is_value is True."""
    if isinstance(node, ast.Constant):
        return node.value
    return -node.operand.value


def value_node(value):
    """Return the node that writes `value`.

    A negative number becomes a minus sign before a number, so that Python's
    unparse puts brackets around it where they are needed: (-2) ** 2.
    """
    if type(value) in (int, float) and str(value).startswith("-"):
        return ast.UnaryOp(op=ast.USub(), operand=ast.Constant(-value))
    return ast.Constant(value)


def check_allowed(node):
    """Raise NotAllowed if the expression holds anything calc does not know."""
    if isinstance(node, ast.Constant) and type(node.value) in (int, float, str, bool):
        return
    if isinstance(node, ast.Name):
        return
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        check_allowed(node.operand)
        return
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        check_allowed(node.left)
        check_allowed(node.right)
        return
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in FUNCTIONS and not node.keywords):
        for argument in node.args:
            check_allowed(argument)
        return
    raise NotAllowed(CAN_DO)


def parts_of(node):
    """Return the parts of `node` that Python works out before the node itself, in order."""
    if isinstance(node, ast.BinOp):
        return [node.left, node.right]
    if isinstance(node, ast.UnaryOp):
        return [node.operand]
    if isinstance(node, ast.Call):
        return node.args
    return []


def next_to_work_out(node):
    """Return the node Python works out next, or None if `node` is already a value."""
    if is_value(node):
        return None
    for part in parts_of(node):
        found = next_to_work_out(part)
        if found is not None:
            return found
    return node


def check_size(node_operator, left, right):
    """Raise NotAllowed before an operation whose result would be huge."""
    if isinstance(node_operator, ast.Pow) and type(left) is int and type(right) is int:
        if abs(left) > 1 and abs(right) * abs(left).bit_length() > MAX_INT_BITS:
            raise NotAllowed("That power is too big for calc.")
    if isinstance(node_operator, ast.Mult):
        for text, count in [(left, right), (right, left)]:
            if isinstance(text, str) and isinstance(count, int) and len(text) * count > MAX_LENGTH:
                raise NotAllowed("That text would be too long for calc.")
    if isinstance(node_operator, ast.Mod) and isinstance(left, str):
        raise NotAllowed(CAN_DO)


def work_out(node, variables):
    """Return the value of one node whose parts are all values."""
    if isinstance(node, ast.Name):
        if node.id not in variables:
            raise NameError(f"name '{node.id}' is not defined")
        return variables[node.id]
    if isinstance(node, ast.BinOp):
        left = value_of(node.left)
        right = value_of(node.right)
        check_size(node.op, left, right)
        return OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.UAdd):
            return +value_of(node.operand)
        return -value_of(node.operand)
    arguments = [value_of(argument) for argument in node.args]
    if node.func.id == "round" and len(arguments) == 2:
        if isinstance(arguments[1], int) and abs(arguments[1]) > MAX_ROUND_DIGITS:
            raise NotAllowed("That is too many digits for round() in calc.")
    return FUNCTIONS[node.func.id](*arguments)


def check_result(value):
    """Raise NotAllowed if a value cannot be shown."""
    if type(value) not in (int, float, str, bool):
        raise NotAllowed("calc shows numbers and text only.")
    if type(value) is float and not math.isfinite(value):
        # Python has no way to write inf or nan back into a line of code.
        raise NotAllowed("calc stops here: the result is inf or nan, not an ordinary number.")
    if type(value) is int and value.bit_length() > MAX_INT_BITS:
        raise NotAllowed("That number is too big for calc.")
    if len(repr(value)) > MAX_LENGTH:
        raise NotAllowed("That result is too long for calc.")


class Replacer(ast.NodeTransformer):
    """Put one node of a syntax tree in the place of another."""

    def __init__(self, old, new):
        """Remember which node to replace and what to put there."""
        self.old = old
        self.new = new

    def visit(self, node):
        """Return the new node for the old one; otherwise look inside the node."""
        if node is self.old:
            return self.new
        return self.generic_visit(node)


def character_column(line, byte_column):
    """Turn a column counted in bytes (as ast counts) into one counted in characters."""
    return len(line.encode("utf-8")[:byte_column].decode("utf-8"))


def steps_for(expression, variables):
    """Return (steps, error): each step is (line, start, end) of the part underlined.

    The last step has start == end: it is the result. `error` is None, or
    the exception Python would raise at the last underlined part.
    """
    steps = []
    line = ast.unparse(ast.parse(expression, mode="eval").body)
    for _ in range(MAX_STEPS):
        tree = ast.parse(line, mode="eval").body
        node = next_to_work_out(tree)
        if node is None:
            steps.append((line, 0, 0))
            return steps, None
        steps.append((line, character_column(line, node.col_offset),
                      character_column(line, node.end_col_offset)))
        try:
            value = work_out(node, variables)
        except NotAllowed:
            raise
        except (ArithmeticError, NameError, TypeError, ValueError) as error:
            return steps, error
        check_result(value)
        line = ast.unparse(Replacer(node, value_node(value)).visit(tree))
        if len(line) > MAX_LENGTH:
            raise NotAllowed("That expression grows too long for calc.")
    raise NotAllowed("That expression takes too many steps for calc.")


def do_calc(state, text):
    """calc <expression> - show each step of working it out."""
    if text == "":
        return USAGE
    if len(text) > MAX_LENGTH:
        return f"calc takes at most {MAX_LENGTH} characters. Try a shorter part."
    try:
        tree = ast.parse(text, mode="eval").body
        check_allowed(tree)
        variables = variable_values(state, tree)
        steps, error = steps_for(text, variables)
    except SyntaxError:
        return "Python cannot read that expression. " + USAGE
    except (NotAllowed, RecursionError) as problem:
        return str(problem)
    return calc_view(steps, error)
