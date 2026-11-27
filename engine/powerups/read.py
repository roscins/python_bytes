"""The read power-up: a text with the index number under every character.

It runs nothing. The text is written in quotes, or is a variable: of the
quick console at the map, or, inside a wave, one that your code sets with
text in quotes.
"""

import ast

from render.read_view import read_view

USAGE = 'Usage: read "some text", or read name, with an optional slice: read name [0:5]'
MAX_CHARACTERS = 99


def whole_number_part(node):
    """Return the int written by `node` (None if there is no node).

    Raises ValueError if it is not a whole number written out, like 3 or -1.
    """
    if node is None:
        return None
    sign = 1
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        sign = -1
        node = node.operand
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return sign * node.value
    raise ValueError("indexes must be whole numbers")


def parse_selection(node):
    """Return the index or slice object written inside the square brackets."""
    if isinstance(node, ast.Slice):
        step = whole_number_part(node.step)
        if step == 0:
            raise ValueError("a step cannot be 0")
        return slice(whole_number_part(node.lower), whole_number_part(node.upper), step)
    return whole_number_part(node)


def text_in_code(code, name):
    """Return the text of the last top-level line `name = "..."` in `code`, or None."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    found = None
    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue
        for target in statement.targets:
            if isinstance(target, ast.Name) and target.id == name:
                found = None
                if isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str):
                    found = statement.value.value
    return found


def value_of_name(state, name):
    """Return the text held by the variable `name`, or None if there is no such text."""
    if state.coding:
        level = state.find_level(state.current_level)
        if level is not None:
            return text_in_code(state.wave_text(level, state.current_wave), name)
    if state.repl is None:
        return None
    for variable in state.repl.variables():
        if variable["name"] == name:
            return variable["text"]
    return None


def do_read(state, text):
    """read <text or name> [slice] - show the index of every character."""
    if text == "":
        return USAGE
    try:
        node = ast.parse(text, mode="eval").body
        selection = None
        if isinstance(node, ast.Subscript):
            selection = parse_selection(node.slice)
            node = node.value
    except (SyntaxError, ValueError):
        return USAGE
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        value = node.value
    elif isinstance(node, ast.Name):
        value = value_of_name(state, node.id)
        if value is None:
            return (f"read cannot find a text called {node.id}. Inside a wave it sees lines like "
                    f'{node.id} = "..."; at the map, your quick console variables.')
    else:
        return USAGE
    if value == "":
        return "That text is empty: it has no characters and len is 0."
    if len(value) > MAX_CHARACTERS:
        return f"That text has {len(value)} characters. read shows at most {MAX_CHARACTERS}."
    return read_view(value, selection, text.rpartition("[")[2], state.plain)
