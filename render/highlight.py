"""Colour Python code for the terminal, using the tokenize module.

highlight_lines(code, color) returns the lines of `code` with ANSI colour
codes around keywords, built-in names, strings, numbers and comments. The
text itself never changes: without the colour codes it is exactly the code.

The colours are the 16 basic terminal colours, so they work in every
terminal (the pixel art uses 24-bit colour, which Terminal.app on macOS
does not have).

Players type code line by line, so the code is often unfinished: a string
that is not closed, a bracket that is still open. tokenize gives the tokens
it read and then raises an error. The tokens before the error are used, and
the rest of the code is coloured by a small scanner that works line by line.
"""

import builtins
import io
import keyword
import re
import tokenize

RESET = "\x1b[0m"

# The colour (the number inside ESC[...m) of each kind of token.
STYLES = {
    "keyword": "35",
    "builtin": "96",
    "string": "36",
    "number": "95",
    "comment": "90",
    "blank": "7",
}

BLANK = "___"

# For code that tokenize could not read: strings (also unclosed ones),
# comments, numbers and names, found one line at a time.
LINE_SCANNER = re.compile(
    r"(?P<comment>\#.*)"
    r"|(?P<string>[rRbBfFuU]{0,2}(?:\"(?:[^\"\\]|\\.)*(?:\"|$)|'(?:[^'\\]|\\.)*(?:'|$)))"
    r"|(?P<number>\b\d[\d_]*(?:\.\d+)?(?:[eE][+-]?\d+)?\b)"
    r"|(?P<name>[A-Za-z_]\w*)"
)

STRING_TOKENS = ["STRING", "FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END"]


def style_of_name(name):
    """Return the style of a name: keyword, builtin, blank, or None for an ordinary name."""
    if name == BLANK:
        return "blank"
    if keyword.iskeyword(name):
        return "keyword"
    if hasattr(builtins, name):
        return "builtin"
    return None


def style_of_token(token):
    """Return the style of a token from tokenize, or None if it is not coloured."""
    kind = tokenize.tok_name[token.type]
    if kind == "NAME":
        return style_of_name(token.string)
    if kind in STRING_TOKENS:
        return "string"
    if kind == "NUMBER":
        return "number"
    if kind == "COMMENT":
        return "comment"
    return None


def add_token_spans(spans, token, style, lines):
    """Record the spans of one token: (first column, end column, style) for each row it covers."""
    start_row, start_column = token.start
    end_row, end_column = token.end
    for row in range(start_row, end_row + 1):
        if row > len(lines):
            return
        first = 0
        last = len(lines[row - 1])
        if row == start_row:
            first = start_column
        if row == end_row:
            last = end_column
        if last > first:
            spans.setdefault(row, []).append((first, last, style))


def scan_line(line):
    """Return the spans of one line, found by the simple scanner."""
    spans = []
    for match in LINE_SCANNER.finditer(line):
        kind = match.lastgroup
        style = kind
        if kind == "name":
            style = style_of_name(match.group())
        if style is not None:
            spans.append((match.start(), match.end(), style))
    return spans


def find_spans(code, lines):
    """Return {row: [(first, end, style), ...]} for the code, rows counted from 1."""
    spans = {}
    last_row = 1
    try:
        for token in tokenize.generate_tokens(io.StringIO(code).readline):
            last_row = token.start[0]
            style = style_of_token(token)
            if style is not None:
                add_token_spans(spans, token, style, lines)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        # The row of the last token read may be half done: scan it and every
        # row after it again, line by line.
        for row in range(last_row, len(lines) + 1):
            spans[row] = scan_line(lines[row - 1])
    return spans


def paint_line(line, spans):
    """Return `line` with colour codes around each span."""
    result = ""
    position = 0
    for first, last, style in sorted(spans):
        if first < position:
            continue
        result = result + line[position:first]
        result = result + f"\x1b[{STYLES[style]}m" + line[first:last] + RESET
        position = last
    return result + line[position:]


def highlight_lines(code, color=True):
    """Return the lines of `code`, with colour codes if `color` is True."""
    lines = code.splitlines()
    if not color:
        return lines
    spans = find_spans(code, lines)
    painted = []
    for index in range(len(lines)):
        painted.append(paint_line(lines[index], spans.get(index + 1, [])))
    return painted
