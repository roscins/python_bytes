"""The explain power-up: which parts of a line are a call, a string or a comment.

It runs nothing. What the line would put on the screen is only shown when
everything inside print() is written out as text or numbers.
"""

import ast
import io
import tokenize

from render.explain_view import explain_view

USAGE = 'Usage: explain followed by one line of code, for example: explain print("HI")  # greet'
MAX_LENGTH = 40             # the line, so the labels fit beside it


def call_label(name):
    """Return the label of a call to `name`."""
    if name == "print":
        return "call: show something"
    return "call: run " + name[:20]


def marks_for(line):
    """Return (start, end, label) for every call name, string and comment in `line`."""
    marks = []
    previous = None
    fstring_start = None
    for token in tokenize.generate_tokens(io.StringIO(line).readline):
        kind = tokenize.tok_name[token.type]
        if kind == "FSTRING_START":
            fstring_start = token.start[1]
        elif kind == "FSTRING_END":
            marks.append((fstring_start, token.end[1], "string: an f-string"))
            fstring_start = None
        elif fstring_start is not None:
            continue
        elif kind == "STRING":
            label = "string: only text"
            if "#" in token.string:
                label = "string: this # is only text"
            marks.append((token.start[1], token.end[1], label))
        elif kind == "COMMENT":
            marks.append((token.start[1], token.end[1], "comment: Python skips it"))
        elif token.string == "(" and previous is not None and previous.type == tokenize.NAME:
            marks.append((previous.start[1], previous.end[1], call_label(previous.string)))
        previous = token
    marks.sort()
    return marks


def screen_text(tree):
    """Return what the line shows on screen, or None if that cannot be told without running it."""
    if not tree.body:
        return ""
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.Expr):
        return None
    call = tree.body[0].value
    if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name):
        return None
    if call.func.id != "print" or call.keywords:
        return None
    shown = []
    for argument in call.args:
        if not isinstance(argument, ast.Constant):
            return None
        shown.append(str(argument.value))
    return " ".join(shown)


def do_explain(state, text):
    """explain <line> - mark its parts."""
    if text == "":
        return USAGE
    if len(text) > MAX_LENGTH:
        return f"explain takes a line of at most {MAX_LENGTH} characters."
    try:
        tree = ast.parse(text)
        marks = marks_for(text)
    except (SyntaxError, ValueError, tokenize.TokenError) as error:
        return f"Python cannot read that line ({getattr(error, 'msg', error)}). Check quotes and brackets."
    return explain_view(text, marks, screen_text(tree))
