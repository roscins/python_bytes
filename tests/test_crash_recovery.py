"""The unkillable save, tested for real: start the game, kill it, start it again.

Each test runs `python play.py --plain --save <temporary file>` as a separate
process, types to it through pipes, kills it, and starts a second process.
Nothing is faked: this is what a player who closes the window sees.
"""

import json
import os
import signal
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path

from tests.helpers import make_temporary_folder

PROJECT_FOLDER = Path(__file__).parent.parent
PLAY_FILE = PROJECT_FOLDER / "play.py"
WAIT_SECONDS = 20


class RunningGame:
    """A game running in its own process, which the test types to and reads from.

    A reader thread collects everything the game prints. wait_for(text)
    waits until `text` appears in what was printed after the last wait.
    """

    def __init__(self, test, save_path):
        """Start the game with its save file at `save_path`."""
        environment = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
        self.process = subprocess.Popen(
            [sys.executable, str(PLAY_FILE), "--plain", "--save", str(save_path)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            cwd=PROJECT_FOLDER, env=environment, text=True, encoding="utf-8",
        )
        test.addCleanup(self.stop)
        self.printed = ""
        self.mark = 0
        self.lock = threading.Lock()
        reader = threading.Thread(target=self.read_forever, daemon=True)
        reader.start()

    def read_forever(self):
        """Collect the game's output, one character at a time (prompts have no newline)."""
        while True:
            character = self.process.stdout.read(1)
            if character == "":
                return
            with self.lock:
                self.printed = self.printed + character

    def wait_for(self, text):
        """Wait until `text` appears after the last wait; return what came before it."""
        deadline = time.monotonic() + WAIT_SECONDS
        while time.monotonic() < deadline:
            with self.lock:
                position = self.printed.find(text, self.mark)
                if position != -1:
                    before = self.printed[self.mark:position]
                    self.mark = position + len(text)
                    return before
            time.sleep(0.01)
        with self.lock:
            tail = self.printed[self.mark:]
        raise AssertionError(f"Waited {WAIT_SECONDS} s for {text!r}. The game printed: {tail!r}")

    def type(self, line):
        """Type a line and press Enter."""
        self.process.stdin.write(line + "\n")
        self.process.stdin.flush()

    def everything(self):
        """Return everything printed so far."""
        with self.lock:
            return self.printed

    def stop(self):
        """Make sure the process is gone (called when the test ends)."""
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait()
        self.process.stdin.close()
        self.process.stdout.close()


class TestKillMinusNine(unittest.TestCase):
    """kill -9 cannot be caught: the save on disk must already hold everything."""

    def start_and_type_half_an_answer(self, save_path):
        """New game, enter Level 1-1, empty wave 1, type one whole line and half of another.

        Returns the running game, waiting at the prompt for line 3.
        """
        game = RunningGame(self, save_path)
        game.wait_for("PYTHON BYTES")
        game.wait_for("> ")
        game.type("1")                      # NEW GAME
        game.wait_for("Type play <level>")
        game.wait_for("> ")
        game.type("play 1-1")
        game.wait_for("WAVE 1 of 3 · FILL-IN")
        game.wait_for("  2 | ")             # the starter has one line, so the next is line 2
        game.type(":clear")
        game.wait_for("  1 | ")
        game.type('print("SYSTEM CHECK")')
        game.wait_for("  2 | ")
        game.type('print("VOICE')           # half an answer: the quote is not closed
        game.wait_for("  3 | ")             # the game saved before asking for line 3
        return game

    def test_kill_nine_then_continue_lands_exactly_there(self):
        """Start, enter 1-1, type half an answer, kill -9, relaunch, CONTINUE: same wave, same lines."""
        save_path = make_temporary_folder(self) / "save.json"
        game = self.start_and_type_half_an_answer(save_path)

        game.process.kill()                 # SIGKILL on Linux and macOS, TerminateProcess on Windows
        game.process.wait()
        self.assertNotEqual(game.process.returncode, 0)

        with open(save_path, encoding="utf-8") as save_file:
            saved = json.load(save_file)
        self.assertEqual(saved["buffers"]["1-1"]["1"], 'print("SYSTEM CHECK")\nprint("VOICE\n')

        again = RunningGame(self, save_path)
        again.wait_for("PYTHON BYTES")
        again.wait_for("CONTINUE (level 1-1, wave 1)")
        again.wait_for("> ")
        again.type("1")                     # CONTINUE
        screen = again.wait_for("  3 | ")
        self.assertIn("WAVE 1 of 3 · FILL-IN", screen)
        self.assertIn('  1 | print("SYSTEM CHECK")', screen)
        self.assertIn('  2 | print("VOICE', screen)
        # The player can go on exactly where they stopped.
        again.type('")')
        again.wait_for("  4 | ")
        again.type(":quit")
        again.process.wait(timeout=WAIT_SECONDS)
        self.assertEqual(again.process.returncode, 0)

    def test_the_save_is_never_half_written(self):
        """After the kill the save is a whole JSON file and there is no stray temp file left to confuse."""
        save_path = make_temporary_folder(self) / "save.json"
        game = self.start_and_type_half_an_answer(save_path)
        game.process.kill()
        game.process.wait()
        json.loads(save_path.read_text(encoding="utf-8"))
        # A temp file left by the killed process would be named save.json.<pid>.tmp.
        # The game only creates it for a moment, so at a prompt there is none.
        leftovers = [name for name in os.listdir(save_path.parent) if name.endswith(".tmp")]
        self.assertEqual(leftovers, [])


@unittest.skipIf(os.name == "nt", "these signals do not exist on Windows")
class TestStopSignals(unittest.TestCase):
    """SIGINT, SIGTERM and SIGHUP save and leave cleanly, with the exit code 128 + signal."""

    def check_signal(self, number):
        """Type one line, send the signal, and check the exit code and the save."""
        save_path = make_temporary_folder(self) / "save.json"
        game = RunningGame(self, save_path)
        game.wait_for("> ")
        game.type("1")
        game.wait_for("Type play <level>")
        game.wait_for("> ")
        game.type("play 1-1")
        game.wait_for("  2 | ")
        game.type(":clear")
        game.wait_for("  1 | ")
        game.type("x = 1")
        game.wait_for("  2 | ")
        game.process.send_signal(number)
        game.process.wait(timeout=WAIT_SECONDS)
        self.assertEqual(game.process.returncode, 128 + number)
        with open(save_path, encoding="utf-8") as save_file:
            saved = json.load(save_file)
        self.assertEqual(saved["buffers"]["1-1"]["1"], "x = 1\n")
        self.assertTrue(saved["coding"])

    def test_terminate(self):
        """kill <pid>."""
        self.check_signal(signal.SIGTERM)

    def test_hangup(self):
        """Closing the terminal window."""
        self.check_signal(signal.SIGHUP)

    def test_interrupt(self):
        """Ctrl-C."""
        self.check_signal(signal.SIGINT)


class TestStartCommand(unittest.TestCase):
    """python play.py is the one command that starts the game."""

    def test_help_text_of_the_command(self):
        """play.py --help works and names the options."""
        result = subprocess.run([sys.executable, str(PLAY_FILE), "--help"], capture_output=True,
                                text=True, cwd=PROJECT_FOLDER, timeout=WAIT_SECONDS)
        self.assertEqual(result.returncode, 0)
        self.assertIn("--plain", result.stdout)
        self.assertIn("--save", result.stdout)

    def test_title_screen_is_the_first_thing_and_quit_leaves(self):
        """No help text first: the title, then the menu."""
        save_path = make_temporary_folder(self) / "save.json"
        game = RunningGame(self, save_path)
        first = game.wait_for("> ")
        self.assertTrue(first.startswith("PYTHON BYTES"))
        self.assertNotIn("help", first.lower())
        game.type("2")                      # QUIT
        game.process.wait(timeout=WAIT_SECONDS)
        self.assertEqual(game.process.returncode, 0)


if __name__ == "__main__":
    unittest.main()
