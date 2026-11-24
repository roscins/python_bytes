"""Tests for engine/loop.py, using scripted input instead of a keyboard."""

import unittest

import json

from engine.game_state import GameState
from engine.loop import WELCOME, run, welcome_text
from tests.helpers import make_levels, make_temporary_folder


class ScriptedPlayer:
    """A pretend player who types lines from a list, one per prompt.

    When the list runs out, it raises the error given as end_with, the
    same way input() does when the player presses Ctrl-D or Ctrl-C.
    """

    def __init__(self, lines, end_with=EOFError):
        """Remember the lines to type and the error to raise at the end."""
        self.lines = list(lines)
        self.end_with = end_with
        self.prompts = []

    def read_line(self, prompt):
        """Return the next scripted line, like input(prompt) would."""
        self.prompts.append(prompt)
        if not self.lines:
            raise self.end_with()
        return self.lines.pop(0)


class TestRun(unittest.TestCase):
    """Check the command loop from start to finish."""

    def play(self, lines, end_with=EOFError, save_path=None):
        """Run a game with scripted lines; return the state and the output."""
        state = GameState(make_levels("1-1", "1-2"))
        player = ScriptedPlayer(lines, end_with)
        output = []
        run(state, read_line=player.read_line, write=output.append, save_path=save_path)
        return state, output

    def test_welcome_is_shown_first(self):
        """The first thing the player sees is the welcome message."""
        state, output = self.play(["quit"])
        self.assertEqual(output[0], WELCOME)

    def test_quit_ends_the_loop(self):
        """Lines after quit are never read."""
        state, output = self.play(["quit", "help"])
        self.assertFalse(state.running)
        self.assertNotIn("Commands:", "\n".join(output))

    def test_commands_run_in_order(self):
        """Each line is run as a command, and its answer is written out."""
        state, output = self.play(["play 1-2", "map", "quit"])
        self.assertIn("Starting level 1-2: Level 1-2.", output)
        self.assertIn("[1-2] Level 1-2  <- you are here", "\n".join(output))
        self.assertEqual(state.current_level, "1-2")

    def test_blank_line_writes_nothing(self):
        """A blank line does not add an empty answer to the output."""
        state, output = self.play(["", "quit"])
        self.assertEqual(output, [WELCOME, "Goodbye, technician."])

    def test_ctrl_d_quits(self):
        """End of input (Ctrl-D) quits like typing quit."""
        state, output = self.play([], end_with=EOFError)
        self.assertFalse(state.running)
        self.assertEqual(output[-1], "Goodbye, technician.")

    def test_ctrl_d_starts_a_fresh_line(self):
        """After Ctrl-D an empty line is written, so goodbye is not on the prompt."""
        state, output = self.play([], end_with=EOFError)
        self.assertEqual(output, [WELCOME, "", "Goodbye, technician."])

    def test_ctrl_c_quits(self):
        """An interrupt (Ctrl-C) quits like typing quit."""
        state, output = self.play(["map"], end_with=KeyboardInterrupt)
        self.assertFalse(state.running)
        self.assertEqual(output[-1], "Goodbye, technician.")

    def test_progress_is_saved_after_each_command(self):
        """With a save path, the save holds the level that was started."""
        save_path = make_temporary_folder(self) / "save.json"
        self.play(["play 1-2", "quit"], save_path=save_path)
        with open(save_path, encoding="utf-8") as save_file:
            self.assertEqual(json.load(save_file)["current_level"], "1-2")

    def test_failed_save_is_reported_and_the_game_goes_on(self):
        """If the save cannot be written, the player is told, every time."""
        # A save path inside a file cannot work, because a file is not a folder.
        blocker = make_temporary_folder(self) / "not-a-folder"
        blocker.write_text("", encoding="utf-8")
        state, output = self.play(["map", "quit"], save_path=blocker / "save.json")
        self.assertFalse(state.running)
        messages = []
        for text in output:
            if text.startswith("Could not save your progress"):
                messages.append(text)
        self.assertEqual(len(messages), 2)


class TestWelcomeText(unittest.TestCase):
    """Check the first thing the player sees."""

    def test_new_player_sees_the_welcome(self):
        """Without a current level, only the welcome is shown."""
        self.assertEqual(welcome_text(GameState()), WELCOME)

    def test_returning_player_is_told_where_they_were(self):
        """With a current level, the player is welcomed back to it."""
        state = GameState(make_levels("1-1"))
        state.current_level = "1-1"
        self.assertIn("Welcome back. You were on level 1-1.", welcome_text(state))


if __name__ == "__main__":
    unittest.main()
