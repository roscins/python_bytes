"""The code-quality rules: naming, indentation, comments and docstrings.

Every build wave is checked against these rules, and the share of rules
passed is the wave's code-quality score. Each rule returns a CheckResult
(see grader/checks.py), so the player sees which rule failed and why.

Only ast and tokenize from the standard library are used: no pycodestyle.
"""

import ast
import io
import re
import tokenize

from grader.checks import CheckResult, count_comments

# snake_case: lower-case letters, digits and underscores, for example
# battery_level or _hidden. Leading underscores are allowed.
SNAKE_CASE = re.compile(r"_*[a-z][a-z0-9_]*")

# UPPER_CASE, for constants, for example MAX_BATTERY.
UPPER_CASE = re.compile(r"_*[A-Z][A-Z0-9_]*")

# CapWords, for class names, for example WeldingRobot.
CAP_WORDS = re.compile(r"_*[A-Z][a-zA-Z0-9]*")

INDENT_WIDTH = 4

# The names of the rules, as the player sees them.
NAMING_RULE = "names are snake_case"
INDENT_RULE = "indents are 4 spaces"
COMMENT_RULE = "has a comment"
DOCSTRING_RULE = "functions and classes have docstrings"
ALL_RULES = [NAMING_RULE, INDENT_RULE, COMMENT_RULE, DOCSTRING_RULE]


def is_good_name(name):
    """Return True if a variable, function or argument name is snake_case or UPPER_CASE."""
    if name == "_":
        return True
    return SNAKE_CASE.fullmatch(name) is not None or UPPER_CASE.fullmatch(name) is not None


def argument_names(arguments):
    """Return the names of all arguments of a function definition."""
    names = []
    for argument in arguments.posonlyargs + arguments.args + arguments.kwonlyargs:
        names.append(argument.arg)
    if arguments.vararg is not None:
        names.append(arguments.vararg.arg)
    if arguments.kwarg is not None:
        names.append(arguments.kwarg.arg)
    return names


def badly_named(tree):
    """Return the names in `tree` that break the naming rule, each once, in the order they appear.

    ast.walk does not visit the code from top to bottom, so each bad name is
    stored with its line and column first, and the list is sorted by them.
    """
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if CAP_WORDS.fullmatch(node.name) is None:
                found.append((node.lineno, node.col_offset, node.name))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for name in [node.name] + argument_names(node.args):
                if not is_good_name(name):
                    found.append((node.lineno, node.col_offset, name))
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            if not is_good_name(node.id):
                found.append((node.lineno, node.col_offset, node.id))
    found.sort()
    bad = []
    for line, column, name in found:
        if name not in bad:
            bad.append(name)
    return bad


def check_naming(code):
    """Rule 1: names are snake_case (or UPPER_CASE constants); classes are CapWords."""
    bad = badly_named(ast.parse(code))
    if not bad:
        return CheckResult(True, NAMING_RULE)
    return CheckResult(False, NAMING_RULE,
                       "Use snake_case for these names, like battery_level: " + ", ".join(bad))


def check_indentation(code):
    """Rule 2: every indented block is indented by a multiple of 4 spaces, never tabs."""
    for token in tokenize.generate_tokens(io.StringIO(code).readline):
        if token.type != tokenize.INDENT:
            continue
        line_number = token.start[0]
        if "\t" in token.string:
            return CheckResult(False, INDENT_RULE,
                               f"Line {line_number} is indented with a tab. Use 4 spaces.")
        if len(token.string) % INDENT_WIDTH != 0:
            return CheckResult(False, INDENT_RULE,
                               f"Line {line_number} is indented by {len(token.string)} spaces. "
                               "Use 4 spaces for each level.")
    return CheckResult(True, INDENT_RULE)


def check_comment(code):
    """Rule 3: the code has at least one # comment."""
    if count_comments(code) > 0:
        return CheckResult(True, COMMENT_RULE)
    return CheckResult(False, COMMENT_RULE, "Add a # comment that explains your code.")


def check_docstrings(code):
    """Rule 4: every function and class has a docstring."""
    missing = []
    for node in ast.walk(ast.parse(code)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if ast.get_docstring(node) is None:
                missing.append(node.name)
    if not missing:
        return CheckResult(True, DOCSTRING_RULE)
    return CheckResult(False, DOCSTRING_RULE, "Add a docstring to: " + ", ".join(missing))


def failed_rules(message):
    """Return a failed CheckResult for every rule, all with the same message."""
    results = []
    for rule in ALL_RULES:
        results.append(CheckResult(False, rule, message))
    return results


def style_checks(code):
    """Check `code` against every code-quality rule; return a list of CheckResults."""
    if code.strip() == "":
        return failed_rules("Write some code first.")
    try:
        ast.parse(code)
    except SyntaxError:
        return failed_rules("Python cannot read your code, so its quality cannot be checked.")
    return [check_naming(code), check_indentation(code), check_comment(code),
            check_docstrings(code)]
