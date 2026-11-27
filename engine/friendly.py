"""Python's errors as friendly game messages.

When the player's code breaks, Python says things like "SyntaxError:
unterminated string literal (detected at line 2)". That is true, but it is
not where a beginner should start. Snek says it in plain words first:

    Snek tripped on line 2: a quote is missing.
      2 | print("hello)
    (Python says: SyntaxError: unterminated string literal (detected at line 2))

The real error always stays below, so the player also learns to read it.

friendly_error() turns the text of an error (a traceback, or just its last
line) into a FriendlyError. format_friendly() turns that into the text to
show. The functions return text and never print.
"""

import builtins
import difflib
import re

# The files whose lines are the player's own code. A traceback also holds
# lines of Python's library, and those are not the player's business.
PLAYER_FILES = ["main.py", "player.py", "<repl>", "<stdin>", "<string>"]

FILE_LINE = re.compile(r'File "([^"]+)", line (\d+)')
ERROR_LINE = re.compile(r"^([A-Za-z_][\w.]*)(?::\s*(.*))?$")

GREY = "\x1b[90m"
RESET = "\x1b[0m"

BRACKET_NAMES = {"(": "bracket (", ")": "bracket )", "[": "square bracket [", "]": "square bracket ]",
                 "{": "curly bracket {", "}": "curly bracket }"}


class FriendlyError:
    """An error explained in plain words.

    Attributes:
        headline: one sentence, for example "Snek tripped on line 2: a quote is missing."
        detail: the real error line from Python, kept to be shown below.
        line: the line of the player's code, or None if it is not known.
    """

    def __init__(self, headline, detail, line):
        """Remember the three parts."""
        self.headline = headline
        self.detail = detail
        self.line = line


def line_number_of(error_text):
    """Return the line of the player's code that an error text points to, or None.

    A traceback lists many lines; the last one in the player's file is
    where the error happened. Lines of libraries are ignored.
    """
    found = None
    for match in FILE_LINE.finditer(error_text):
        name = match.group(1).replace("\\", "/").split("/")[-1]
        if name in PLAYER_FILES:
            found = int(match.group(2))
    return found


def syntax_sentence(message):
    """Return what a SyntaxError or IndentationError says, in plain words."""
    rules = [
        (r"unterminated string literal", lambda m: "a quote is missing"),
        (r"unterminated triple-quoted string", lambda m: 'a triple quote """ is never closed'),
        (r"'(.)' was never closed", lambda m: f"a {BRACKET_NAMES.get(m.group(1), 'bracket ' + m.group(1))} was never closed"),
        (r"closing parenthesis '(.)' does not match", lambda m: "the brackets do not match each other"),
        (r"unmatched '(.)'", lambda m: f"there is a {m.group(1)} with no matching opening bracket"),
        (r"expected ':'", lambda m: "a colon : is missing at the end of the line"),
        (r"expected an indented block", lambda m: "this line must be indented (4 spaces) under the line above it"),
        (r"unexpected indent", lambda m: "this line is indented too far"),
        (r"unindent does not match", lambda m: "the indentation does not match any line above it"),
        (r"Perhaps you forgot a comma", lambda m: "something is missing between two items: a comma , maybe"),
        (r"invalid (?:decimal|hexadecimal|octal|binary) literal", lambda m: "a number is mixed up with letters"),
        (r"cannot assign to ([a-z ]+?)(?: here|\.|$)",
         lambda m: f"what is on the left of = must be a name, not a {m.group(1)}"),
        (r"unexpected EOF|EOF while scanning", lambda m: "the code ends too early: something is not finished"),
        (r"invalid character|non-printable", lambda m: "there is a strange character here (a curly quote?)"),
        (r"invalid syntax", lambda m: "Python cannot read this line"),
    ]
    for pattern, builder in rules:
        match = re.search(pattern, message)
        if match:
            return builder(match)
    return f"Python cannot read this: {message}"


def name_sentence(message):
    """Return the sentence for a NameError."""
    match = re.search(r"name '(.+)' is not defined", message)
    if match:
        return (f"I do not know the name {match.group(1)} "
                "(is it spelled right, and did you create it before this line?)")
    return f"a name is not known: {message}"


def type_sentence(message):
    """Return the sentence for a TypeError."""
    if re.search(r'can only concatenate str \(not "\w+"\) to str', message):
        return "you cannot add a number to text with +: turn the number into text with str()"
    match = re.search(r"unsupported operand type\(s\) for ([^:]+): '(\w+)' and '(\w+)'", message)
    if match:
        return (f"you cannot use {match.group(1)} between a {match.group(2)} and a {match.group(3)}: "
                "convert one of them (int(), float() or str())")
    match = re.search(r"'(\w+)' object is not callable", message)
    if match:
        return f"a {match.group(1)} cannot be called like a function (is a name used twice?)"
    if re.search(r"positional argument", message):
        return "a function got the wrong number of values"
    return f"the types do not fit together: {message}"


def value_sentence(message):
    """Return the sentence for a ValueError."""
    match = re.search(r"invalid literal for int\(\) with base 10: (.*)", message)
    if match:
        return f"{match.group(1)} is not a whole number, so int() cannot convert it"
    match = re.search(r"could not convert string to float: (.*)", message)
    if match:
        return f"{match.group(1)} is not a number, so float() cannot convert it"
    return f"the value has the right type but the wrong content: {message}"


def attribute_sentence(message):
    """Return the sentence for an AttributeError."""
    match = re.search(r"'(\w+)' object has no attribute '(\w+)'", message)
    if match:
        return f"a {match.group(1)} has no .{match.group(2)} (check the spelling)"
    match = re.search(r"module '(\w+)' has no attribute '(\w+)'", message)
    if match:
        return f"the module {match.group(1)} has no .{match.group(2)} (check the spelling)"
    return f"something has no such part: {message}"


def explain(type_name, message):
    """Return the plain-words sentence (without a final full stop) for an error type and message."""
    if type_name in ("SyntaxError", "IndentationError", "TabError"):
        return syntax_sentence(message)
    if type_name == "NameError":
        return name_sentence(message)
    if type_name == "TypeError":
        return type_sentence(message)
    if type_name == "ValueError":
        return value_sentence(message)
    if type_name == "AttributeError":
        return attribute_sentence(message)
    if type_name == "ZeroDivisionError":
        return "you divided by zero"
    if type_name == "IndexError":
        return "that position does not exist: the text or list is shorter than that"
    if type_name == "KeyError":
        return f"the key {message} is not in the dictionary"
    if type_name == "EOFError":
        return "the program asked for input, but there was none"
    if type_name == "RecursionError":
        return "a function calls itself again and again without stopping"
    if type_name in ("ModuleNotFoundError", "ImportError"):
        return f"a module could not be loaded: {message}"
    if type_name == "UnboundLocalError":
        return "a name is used in a function before it was given a value"
    if message:
        return f"Python says {type_name}: {message}"
    return f"Python says {type_name}"


def friendly_error(error_text):
    """Explain an error text (a whole traceback, or only its last line) in plain words."""
    lines = []
    for line in error_text.strip().splitlines():
        if line.strip() != "":
            lines.append(line)
    detail = ""
    if lines:
        detail = lines[-1].strip()
    number = line_number_of(error_text)

    match = ERROR_LINE.match(detail)
    if match:
        type_name = match.group(1).split(".")[-1]
        sentence = explain(type_name, match.group(2) or "")
    else:
        sentence = f"Python says: {detail}"
    if number is None:
        headline = f"Snek tripped: {sentence}."
    else:
        headline = f"Snek tripped on line {number}: {sentence}."
    return FriendlyError(headline, detail, number)


# print(...) and print ... without brackets; a comment may follow.
PRINT_CALL = re.compile(r"^\s*print\s*\((.*)\)\s*(?:#.*)?$")
PRINT_WITHOUT_BRACKETS = re.compile(r"^\s*print\s+(?![=(.\[])(.*?)\s*$")

# Text that is only words and punctuation: no quotes, =, brackets or operators.
PLAIN_WORDS = re.compile(r"^[\w .,!?:'-]+$")

# Signs that it is code after all: math.pi, a - b, or a ' that is not inside a word.
CODE_SIGNS = re.compile(r"\w\.\w|(?<!\w)-|-(?!\w)|(?<![^\W\d])'|'(?![^\W\d])")

# The places where code gives something a name.
MADE_NAMES = re.compile(r"^\s*(?:(\w+)\s*[-+*/]?=(?!=)|(?:def|class|for|import)\s+(\w+))", re.MULTILINE)


def names_in(code):
    """Return the names the code creates, also when Python cannot read all of it."""
    names = []
    for match in MADE_NAMES.finditer(code):
        names.append(match.group(1) or match.group(2))
    return names


def unquoted_text(line):
    """Return (the words, has brackets) for a print of text without quotes, else None."""
    match = PRINT_CALL.match(line)
    brackets = match is not None
    if match is None:
        match = PRINT_WITHOUT_BRACKETS.match(line)
    if match is None:
        return None
    words = match.group(1).strip()
    if not PLAIN_WORDS.match(words) or CODE_SIGNS.search(words):
        return None
    if not any(character.isalpha() for character in words):
        return None
    return words, brackets


def quote_sentence(type_name, line, code):
    """Return what to say about missing quotes or a mistyped name on `line`, or None.

    The suggestion only reuses the player's own words.
    """
    if type_name not in ("SyntaxError", "NameError"):
        return None
    found = unquoted_text(line)
    if found is None:
        return None
    words, brackets = found
    made = names_in(code)
    used = re.findall(r"[^\W\d]\w*", words)
    for word in used:
        # A name the code creates: the problem is something else.
        if word in made:
            return None
    if len(used) == 1 and words == used[0]:
        close = difflib.get_close_matches(words, made + dir(builtins), n=1, cutoff=0.7)
        if close and close[0] in made:
            return f"I do not know the name {words}. Did you mean {close[0]}?"
    needs = "quotes"
    if not brackets:
        needs = "quotes and brackets"
    return f'Text needs {needs}: try print("{words}")'


def friendly_for_source(error_text, code):
    """Like friendly_error, but it also looks at the code, to suggest quotes."""
    error = friendly_error(error_text)
    lines = code.splitlines()
    if error.line is None or not 1 <= error.line <= len(lines):
        return error
    match = ERROR_LINE.match(error.detail)
    if match:
        sentence = quote_sentence(match.group(1).split(".")[-1], lines[error.line - 1], code)
        if sentence is not None:
            error.headline = sentence
    return error


def friendly_timeout(seconds):
    """Return the FriendlyError for a program that ran longer than `seconds`."""
    headline = (f"Snek got stuck: your program ran for more than {seconds:g} seconds. "
                "Is there a loop that never ends?")
    return FriendlyError(headline, "", None)


def format_friendly(error, source_text, plain=False, color=False):
    """Return the text to show for a FriendlyError.

    The headline, then the player's line of code (if the line number is
    known and the code has it), then the real error: in grey with `color`,
    otherwise marked "Python says".
    """
    lines = [error.headline]
    source_lines = source_text.splitlines()
    if error.line is not None and 1 <= error.line <= len(source_lines):
        bar = "|" if plain else "│"
        lines.append(f"{error.line:>3} {bar} {source_lines[error.line - 1]}")
    if error.detail:
        if color:
            lines.append(f"{GREY}{error.detail}{RESET}")
        else:
            lines.append(f"(Python says: {error.detail})")
    return "\n".join(lines)


def friendly_message(message):
    """Rewrite a grader message about a crash or a timeout in plain words.

    The grader says "Your program stopped with an error on line 2: NameError:
    ..." or "Your program ran for more than 2 seconds. ...". Any other
    message is returned unchanged.
    """
    match = re.match(r"Your program stopped with an error(?: on line (\d+))?: (.*)$", message, re.DOTALL)
    if match:
        text = match.group(2)
        if match.group(1):
            text = f'File "main.py", line {match.group(1)}\n{text}'
        return format_friendly(friendly_error(text), "", plain=True, color=False)
    match = re.match(r"Your program ran for more than (\S+) seconds", message)
    if match:
        return friendly_timeout(float(match.group(1))).headline
    return message
