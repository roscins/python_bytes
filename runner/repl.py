"""The quick console: run a line of Python and keep the variables for the next line.

A ReplSession owns one worker process (runner/repl_worker.py). The first
line starts it; every line after that runs in the same process, so
`x = 5` and then `x * 2` work like in the Python console.

If a line takes too long, or the player closes the worker with exit(), the
process is stopped and a new one starts with the next line. The variables
are gone then, and the result says so (was_reset).
"""

import codeop
import json
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

WORKER_FILE = Path(__file__).parent / "repl_worker.py"

# How many seconds one line may run.
DEFAULT_TIMEOUT = 2.0


def classify(source):
    """Say what a typed piece of code is: "complete", "incomplete" or "invalid".

    "incomplete" means Python wants more lines (an open bracket, or a block
    like a for loop that is not ended by a blank line yet). "invalid" means
    more typing cannot make it Python, for example a command with a typo.
    """
    try:
        compiled = codeop.compile_command(source, "<repl>", "single")
    except (SyntaxError, OverflowError, ValueError):
        return "invalid"
    if compiled is None:
        return "incomplete"
    return "complete"


class ReplResult:
    """What one line did.

    Attributes:
        output: what the line printed (and the value of an expression).
        error: the traceback if it failed, or "".
        timed_out: True if the line ran too long and the console was stopped.
        was_reset: True if the worker had to be replaced, so variables are gone.
        output_cut: True if the output was too long and was cut.
    """

    def __init__(self, output="", error="", timed_out=False, was_reset=False, output_cut=False):
        """Remember every part of the result."""
        self.output = output
        self.error = error
        self.timed_out = timed_out
        self.was_reset = was_reset
        self.output_cut = output_cut


class ReplSession:
    """One quick console: a worker process that is started on the first line.

    Attributes:
        timeout: seconds one line may run.
        process: the running worker (a subprocess.Popen), or None.
    """

    def __init__(self, timeout=DEFAULT_TIMEOUT):
        """Prepare a console; nothing is started yet."""
        self.timeout = timeout
        self.process = None
        self.replies = queue.Queue()
        self.folder = None

    def start(self):
        """Start a worker process, in a temporary folder of its own."""
        self.folder = tempfile.mkdtemp(prefix="python-bytes-console-")
        self.replies = queue.Queue()
        self.process = subprocess.Popen(
            [sys.executable, "-I", "-u", str(WORKER_FILE)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            cwd=self.folder, text=True, encoding="utf-8",
        )
        reader = threading.Thread(target=self.read_replies, args=(self.process, self.replies), daemon=True)
        reader.start()

    @staticmethod
    def read_replies(process, replies):
        """Move each line the worker prints to a queue; put None there when it ends."""
        for line in process.stdout:
            replies.put(line)
        replies.put(None)

    def stop(self):
        """Stop the worker process and delete its folder."""
        process = self.process
        self.process = None
        if process is not None:
            if process.poll() is None:
                process.kill()
            process.wait()
            for stream in (process.stdin, process.stdout):
                if stream is not None:
                    try:
                        stream.close()
                    except OSError:
                        pass
        if self.folder is not None:
            shutil.rmtree(self.folder, ignore_errors=True)
            self.folder = None

    def close(self):
        """End the console for good (called when the game ends)."""
        self.stop()

    def run(self, source):
        """Run `source` in the console and return a ReplResult."""
        if self.process is None:
            self.start()
        try:
            self.process.stdin.write(json.dumps({"source": source}) + "\n")
            self.process.stdin.flush()
        except OSError:
            return self.reset(ReplResult())
        try:
            line = self.replies.get(timeout=self.timeout)
        except queue.Empty:
            return self.reset(ReplResult(timed_out=True))
        if line is None:
            # The worker ended by itself, for example after exit().
            return self.reset(ReplResult())
        reply = json.loads(line)
        return ReplResult(reply["output"], reply["error"], output_cut=reply.get("output_cut", False))

    def reset(self, result):
        """Replace the worker after a time-out or a crash; mark the result as a reset."""
        self.stop()
        result.was_reset = True
        return result
