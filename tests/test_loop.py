"""Tests for engine/loop.py, using scripted input instead of a keyboard."""

import unittest

from engine.game_state import GameState
from engine.loop import WELCOME, run


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

    def play(self, lines, end_with=EOFError):
        """Run a game with scripted lines; return the state and the output."""
        state = GameState(["1-1", "1-2"])
        player = ScriptedPlayer(lines, end_with)
        output = []
        run(state, read_line=player.read_line, write=output.append)
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
        self.assertIn("Starting level 1-2.", output)
        self.assertIn("[1-2]  <- you are here", "\n".join(output))
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

    def test_ctrl_c_quits(self):
        """An interrupt (Ctrl-C) quits like typing quit."""
        state, output = self.play(["map"], end_with=KeyboardInterrupt)
        self.assertFalse(state.running)
        self.assertEqual(output[-1], "Goodbye, technician.")


if __name__ == "__main__":
    unittest.main()
