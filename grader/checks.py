"""The tests a level can run on a player's code, one function per kind of test.

Each [[wave.test]] table in a level.toml has one key that says what kind of
test it is (see TEST_KINDS and docs/design/phase-2-grader.md). run_check
picks the right function, runs it and returns a CheckResult: did the code
pass, and if not, a message that helps the player fix it.
"""

import ast
import io
import json
import math
import tokenize

from runner.process import DEFAULT_TIME_LIMIT, run_code, run_files

# The keys that say what kind of test a [[wave.test]] table is.
TEST_KINDS = [
    "expected_stdout",
    "expected_stdout_contains",
    "call",
    "require",
    "forbid",
    "require_comment",
]

# Friendly names for the Python constructs levels ask for most. Any other
# AST node type is shown by its own name.
CONSTRUCT_NAMES = {
    "Call": "a function call",
    "Assign": "an assignment (=)",
    "AugAssign": "an update like += or -=",
    "BinOp": "an arithmetic operator",
    "Compare": "a comparison",
    "BoolOp": "and / or",
    "If": "an if statement",
    "While": "a while loop",
    "For": "a for loop",
    "Break": "break",
    "Continue": "continue",
    "FunctionDef": "a function definition (def)",
    "Return": "return",
    "ClassDef": "a class",
    "Try": "try / except",
    "With": "a with block",
    "List": "a list",
    "Tuple": "a tuple",
    "Set": "a set",
    "Dict": "a dictionary",
    "JoinedStr": "an f-string",
    "Lambda": "a lambda",
    "ListComp": "a list comprehension",
}

# The files used for a function test: the player's code, a small script
# that calls the function, and the call to make.
PLAYER_FILE = "player.py"
CALL_FILE = "call.json"
CALL_SCRIPT_FILE = "call_function.py"

# The call script prints the result on a line starting with this marker, so
# it can be told apart from anything the player's code prints.
RESULT_MARKER = "@@PYTHON-BYTES-RESULT@@ "

CALL_SCRIPT = '''"""Load player.py, call one of its functions and print the result as JSON."""

import importlib.util
import json

MARKER = "@@PYTHON-BYTES-RESULT@@ "


def as_json_value(value):
    """Turn a set into a sorted list, so json.dumps can write it."""
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    raise TypeError(f"cannot write {value!r} as JSON")


with open("call.json", encoding="utf-8") as call_file:
    call = json.load(call_file)

spec = importlib.util.spec_from_file_location("player", "player.py")
player = importlib.util.module_from_spec(spec)
spec.loader.exec_module(player)

if not hasattr(player, call["name"]):
    print(MARKER + "MISSING")
else:
    function = getattr(player, call["name"])
    result = function(*call["args"])
    try:
        print(MARKER + "VALUE " + json.dumps(result, default=as_json_value))
    except TypeError:
        print(MARKER + "OTHER " + repr(result))
'''


class CheckResult:
    """The result of one check on the player's code.

    Attributes:
        passed: True if the code passed the check.
        name: what was checked, for example "prints the right output".
        message: why the check failed, to help the player; "" if it passed.
    """

    def __init__(self, passed, name, message=""):
        """Remember the result, the name and the message."""
        self.passed = passed
        self.name = name
        self.message = message


def normalise_output(text):
    """Return `text` without spaces at the ends of lines or blank lines at the end.

    Output is compared after this, so an invisible trailing space or a
    missing last new line never fails a player.
    """
    lines = []
    for line in text.splitlines():
        lines.append(line.rstrip())
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def indent_block(text):
    """Return `text` with every line indented by 4 spaces, for messages."""
    if text == "":
        return "    (nothing)"
    lines = []
    for line in text.splitlines():
        lines.append("    " + line)
    return "\n".join(lines)


def construct_name(node_type):
    """Return the friendly name of an AST node type, for example "a while loop"."""
    return CONSTRUCT_NAMES.get(node_type, node_type)


def problem_with_run(result, time_limit=DEFAULT_TIME_LIMIT):
    """Return a message if the program crashed or timed out, or "" if it ran fine."""
    if result.timed_out:
        return (f"Your program ran for more than {time_limit:g} seconds. "
                "Is there a loop that never ends?")
    if result.exit_code != 0:
        number = result.error_line_number()
        if number is None:
            return f"Your program stopped with an error: {result.error_line()}"
        return f"Your program stopped with an error on line {number}: {result.error_line()}"
    return ""


def input_note(test):
    """Return " (input: ...)" for a test that has fake input, or ""."""
    if "stdin" in test:
        return f" (input: {test['stdin']!r})"
    return ""


def check_expected_stdout(test, code, time_limit=DEFAULT_TIME_LIMIT):
    """The program must print exactly test["expected_stdout"]."""
    name = "prints the right output" + input_note(test)
    result = run_code(code, test.get("stdin", ""), time_limit)
    problem = problem_with_run(result, time_limit)
    if problem:
        return CheckResult(False, name, problem)
    expected = normalise_output(test["expected_stdout"])
    printed = normalise_output(result.stdout)
    if printed == expected:
        return CheckResult(True, name)
    message = ("Expected this output:\n" + indent_block(expected)
               + "\nYour program printed:\n" + indent_block(printed))
    return CheckResult(False, name, message)


def check_expected_stdout_contains(test, code, time_limit=DEFAULT_TIME_LIMIT):
    """Every text in test["expected_stdout_contains"] must appear in the output."""
    pieces = test["expected_stdout_contains"]
    name = "prints " + ", ".join(pieces) + input_note(test)
    result = run_code(code, test.get("stdin", ""), time_limit)
    problem = problem_with_run(result, time_limit)
    if problem:
        return CheckResult(False, name, problem)
    printed = normalise_output(result.stdout)
    missing = []
    for piece in pieces:
        if piece not in printed:
            missing.append(piece)
    if not missing:
        return CheckResult(True, name)
    message = ("The output should contain: " + ", ".join(missing)
               + "\nYour program printed:\n" + indent_block(printed))
    return CheckResult(False, name, message)


def values_match(got, expected):
    """Return True if a value returned by the player's function matches `expected`.

    Numbers with a decimal point match when they are equal to about 9
    decimal places, so 0.1 + 0.2 matches 0.3. True and False only match
    True and False, not 1 and 0. Lists and dictionaries match when every
    item matches.
    """
    if isinstance(got, bool) or isinstance(expected, bool):
        return isinstance(got, bool) and isinstance(expected, bool) and got == expected
    if isinstance(got, (int, float)) and isinstance(expected, (int, float)):
        return math.isclose(got, expected, rel_tol=1e-9, abs_tol=1e-9)
    if isinstance(got, list) and isinstance(expected, list):
        if len(got) != len(expected):
            return False
        for index in range(len(got)):
            if not values_match(got[index], expected[index]):
                return False
        return True
    if isinstance(got, dict) and isinstance(expected, dict):
        if set(got) != set(expected):
            return False
        for key in got:
            if not values_match(got[key], expected[key]):
                return False
        return True
    return got == expected


def call_text(test):
    """Return the call a function test makes, for example "distance(3, 4)"."""
    arguments = []
    for argument in test.get("args", []):
        arguments.append(repr(argument))
    return f"{test['call']}({', '.join(arguments)})"


def find_result_line(stdout):
    """Return what the call script printed after the marker, or None."""
    found = None
    for line in stdout.splitlines():
        if line.startswith(RESULT_MARKER):
            found = line[len(RESULT_MARKER):]
    return found


def check_call(test, code, time_limit=DEFAULT_TIME_LIMIT):
    """Calling test["call"] with test["args"] must return test["expected"]."""
    call = call_text(test)
    name = f"{call} returns {test['expected']!r}"
    call_json = json.dumps({"name": test["call"], "args": test.get("args", [])})
    files = {PLAYER_FILE: code, CALL_FILE: call_json, CALL_SCRIPT_FILE: CALL_SCRIPT}
    result = run_files(files, CALL_SCRIPT_FILE, test.get("stdin", ""), time_limit)
    problem = problem_with_run(result, time_limit)
    if problem:
        return CheckResult(False, name, problem)
    found = find_result_line(result.stdout)
    if found is None or found == "MISSING":
        return CheckResult(False, name, f"Your code has no function named {test['call']}.")
    if found.startswith("VALUE "):
        got = json.loads(found[len("VALUE "):])
        if values_match(got, test["expected"]):
            return CheckResult(True, name)
        shown = repr(got)
    else:
        shown = found[len("OTHER "):]
    return CheckResult(False, name, f"{call} should return {test['expected']!r}, "
                                    f"but it returned {shown}.")


def parse_problem(code):
    """Return a message if Python cannot read `code`, or "" if it can."""
    try:
        ast.parse(code)
    except SyntaxError as error:
        return f"Python cannot read your code: {error.msg} (line {error.lineno})."
    return ""


def node_types_used(code):
    """Return the set of AST node type names in `code`, for example {"Call", "Constant"}."""
    names = set()
    for node in ast.walk(ast.parse(code)):
        names.add(type(node).__name__)
    return names


def check_require(test, code):
    """The code must use every construct in test["require"]."""
    friendly = []
    for node_type in test["require"]:
        friendly.append(construct_name(node_type))
    name = "uses " + ", ".join(friendly)
    problem = parse_problem(code)
    if problem:
        return CheckResult(False, name, problem)
    used = node_types_used(code)
    missing = []
    for node_type in test["require"]:
        if node_type not in used:
            missing.append(construct_name(node_type))
    if not missing:
        return CheckResult(True, name)
    return CheckResult(False, name, "Your code must use " + ", ".join(missing) + ".")


def check_forbid(test, code):
    """The code must not use any construct in test["forbid"]."""
    friendly = []
    for node_type in test["forbid"]:
        friendly.append(construct_name(node_type))
    name = "does not use " + ", ".join(friendly)
    problem = parse_problem(code)
    if problem:
        return CheckResult(False, name, problem)
    used = node_types_used(code)
    found = []
    for node_type in test["forbid"]:
        if node_type in used:
            found.append(construct_name(node_type))
    if not found:
        return CheckResult(True, name)
    return CheckResult(False, name, "This task must be solved without " + ", ".join(found) + ".")


def count_comments(code):
    """Return how many # comments `code` has, or None if Python cannot read it.

    The AST leaves comments out, so they are found with tokenize, which
    splits code into its pieces (names, numbers, comments, ...).
    """
    count = 0
    try:
        for token in tokenize.generate_tokens(io.StringIO(code).readline):
            if token.type == tokenize.COMMENT:
                count = count + 1
    except (tokenize.TokenError, SyntaxError):
        return None
    return count


def check_require_comment(test, code):
    """The code must have at least one # comment."""
    name = "has a comment"
    comments = count_comments(code)
    if comments is None:
        return CheckResult(False, name, parse_problem(code) or "Python cannot read your code.")
    if comments > 0:
        return CheckResult(True, name)
    return CheckResult(False, name, "Add a # comment that says what your code does.")


# Which function runs each kind of test.
CHECK_FUNCTIONS = {
    "expected_stdout": check_expected_stdout,
    "expected_stdout_contains": check_expected_stdout_contains,
    "call": check_call,
    "require": check_require,
    "forbid": check_forbid,
    "require_comment": check_require_comment,
}


def test_kind(test):
    """Return the kind of a test table, for example "expected_stdout", or None."""
    for kind in TEST_KINDS:
        if kind in test:
            return kind
    return None


# The kinds of test that run the player's program, and so have a time limit.
RUNNING_KINDS = ["expected_stdout", "expected_stdout_contains", "call"]


def run_check(test, code, time_limit=DEFAULT_TIME_LIMIT):
    """Run one [[wave.test]] table on the player's code and return a CheckResult.

    `time_limit` is how many seconds the program may run, for the kinds of
    test that run it.
    """
    kind = test_kind(test)
    if kind is None:
        return CheckResult(False, "unknown test", "This test has no kind the grader knows.")
    check_function = CHECK_FUNCTIONS[kind]
    if kind in RUNNING_KINDS:
        return check_function(test, code, time_limit)
    return check_function(test, code)
