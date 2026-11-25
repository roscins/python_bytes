"""Tests for engine/loop.py, using scripted input instead of a keyboard."""

import unittest

import json

from engine.game_state import GameState
from engine.loop import FRAME_SECONDS, WELCOME, move_cursor_up, run, show_frames, welcome_text
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
        """Run a game with scripted lines; return the state and the output.

        The pause between animation frames is recorded in self.pauses
        instead of waiting, so the tests run fast.
        """
        state = GameState(make_levels("1-1", "1-2"))
        player = ScriptedPlayer(lines, end_with)
        output = []
        self.pauses = []
        run(state, read_line=player.read_line, write=output.append,
            save_path=save_path, pause=self.pauses.append)
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
        self.assertIn("LEVEL 1-2 · LEVEL 1-2", "\n".join(output))
        self.assertIn("You are at [1-2] Level 1-2.", "\n".join(output))
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


    def test_slither_is_drawn_as_an_animation(self):
        """Playing 1-2 after 1-1 draws frames over each other, with pauses."""
        state, output = self.play(["play 1-1", "play 1-2", "quit"])
        self.assertGreater(len(self.pauses), 0)
        # Normal answers start with a letter; a redrawn frame starts with
        # the escape code that moves the cursor up.
        moved_up = []
        for text in output:
            if text.startswith("\x1b["):
                moved_up.append(text)
        self.assertEqual(len(moved_up), len(self.pauses))


class TestShowFrames(unittest.TestCase):
    """Check drawing an animation, frame by frame."""

    def test_each_frame_is_drawn_over_the_one_before(self):
        """The first frame is written as it is; later ones move up first."""
        output = []
        pauses = []
        show_frames(["a\nb", "c\nd", "e\nf\nmore"], output.append, pauses.append)
        self.assertEqual(output, [
            "a\nb",
            move_cursor_up(2) + "c\nd",
            move_cursor_up(2) + "e\nf\nmore",
        ])
        self.assertEqual(pauses, [FRAME_SECONDS, FRAME_SECONDS])

    def test_move_cursor_up_code(self):
        """Moving up 3 lines is ESC [ 3 F."""
        self.assertEqual(move_cursor_up(3), "\x1b[3F")


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
