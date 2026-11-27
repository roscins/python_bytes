"""The worker behind the quick console: runs lines of Python and keeps the variables.

This file is run as its own program by runner/repl.py (python -I -u
repl_worker.py). It imports nothing from the game, so the player's code
cannot touch the game's own code by accident.

The conversation is one JSON line each way, so no output can be mixed up:

    game -> worker   {"source": "x = 1\\nprint(x)\\n"}
    worker -> game   {"output": "1\\n", "error": ""}

The power-ups can also ask what the variables are:

    game -> worker   {"variables": true}
    worker -> game   {"output": "", "error": "", "variables": [{"name": "x", ...}]}

Like the runner, this protects against mistakes (the game stops a worker
that runs too long); it is not a security sandbox.
"""

import builtins
import code
import contextlib
import io
import json
import sys

MAX_OUTPUT_CHARACTERS = 100_000
MAX_VALUE_CHARACTERS = 200


def refuse_input(prompt=""):
    """Replace input(): the worker's own input is the pipe to the game, so it cannot be used."""
    raise RuntimeError("input() does not work in the quick console. Use :run inside a wave.")


def cut(text):
    """Return `text` cut to MAX_OUTPUT_CHARACTERS, and whether it was cut."""
    if len(text) <= MAX_OUTPUT_CHARACTERS:
        return text, False
    return text[:MAX_OUTPUT_CHARACTERS], True


def describe_variables(namespace):
    """Return one description per variable of the console, in the order they were made.

    Each is a dict: name, type, repr (cut if very long), id (the same number
    means the same object) and text (the value itself if it is a short str).
    Modules, functions and the console's own __name__ are left out.
    """
    described = []
    for name, value in namespace.items():
        if name.startswith("__") or callable(value) or type(value).__name__ == "module":
            continue
        text = None
        if type(value) is str and len(value) <= MAX_VALUE_CHARACTERS:
            text = value
        described.append({"name": name, "type": type(value).__name__, "id": id(value),
                          "repr": repr(value)[:MAX_VALUE_CHARACTERS], "text": text})
    return described


def main():
    """Read requests from the game until its end of the pipe, and answer each one."""
    reply_channel = sys.stdout
    builtins.input = refuse_input
    interpreter = code.InteractiveInterpreter({"__name__": "__console__"})
    for line in sys.stdin:
        request = json.loads(line)
        if "variables" in request:
            reply = {"output": "", "error": "", "variables": describe_variables(interpreter.locals)}
            reply_channel.write(json.dumps(reply) + "\n")
            reply_channel.flush()
            continue
        output = io.StringIO()
        errors = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            interpreter.runsource(request["source"], "<repl>", request.get("mode", "single"))
        printed, output_cut = cut(output.getvalue())
        reply = {"output": printed, "error": errors.getvalue()[:MAX_OUTPUT_CHARACTERS], "output_cut": output_cut}
        reply_channel.write(json.dumps(reply) + "\n")
        reply_channel.flush()


if __name__ == "__main__":
    main()
