"""Tests for engine/loop.py, using scripted input instead of a keyboard."""

import unittest

import json

from engine.game_state import GameState
from engine.loop import FRAME_SECONDS, move_cursor_up, run, show_frames, start_text
from engine.shutdown import ShutdownGuard
from tests.helpers import make_full_level, make_levels, make_temporary_folder


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
        instead of waiting, so the tests run fast. Level 1-1 starts out
        cleared, so 1-2 is open.
        """
        state = GameState(make_levels("1-1", "1-2"))
        state.cleared = ["1-1"]
        player = ScriptedPlayer(lines, end_with)
        output = []
        self.pauses = []
        run(state, read_line=player.read_line, write=output.append,
            save_path=save_path, pause=self.pauses.append)
        return state, output

    def test_no_welcome_or_help_text_is_printed(self):
        """The title screen came first; the loop adds nothing before the first command."""
        state, output = self.play(["quit"])
        self.assertEqual(output, ["Goodbye, technician."])

    def test_quit_ends_the_loop(self):
        """Lines after quit are never read."""
        state, output = self.play(["quit", "help"])
        self.assertFalse(state.running)
        self.assertNotIn("Commands:", "\n".join(output))

    def test_commands_run_in_order(self):
        """Each line is run as a command, and its answer is written out."""
        state, output = self.play(["play 1-2", ":map", "quit"])
        self.assertIn("LEVEL 1-2 · LEVEL 1-2", "\n".join(output))
        self.assertIn("You are at [1-2] Level 1-2.", "\n".join(output))
        self.assertEqual(state.current_level, "1-2")

    def test_blank_line_writes_nothing(self):
        """A blank line does not add an empty answer to the output."""
        state, output = self.play(["", "quit"])
        self.assertEqual(output, ["Goodbye, technician."])

    def test_ctrl_d_quits(self):
        """End of input (Ctrl-D) quits like typing quit."""
        state, output = self.play([], end_with=EOFError)
        self.assertFalse(state.running)
        self.assertEqual(output[-1], "Goodbye, technician.")

    def test_ctrl_d_starts_a_fresh_line(self):
        """After Ctrl-D an empty line is written, so goodbye is not on the prompt."""
        state, output = self.play([], end_with=EOFError)
        self.assertEqual(output, ["", "Goodbye, technician."])

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
        """If the save cannot be written, the player is told once, not after every line."""
        # A save path inside a file cannot work, because a file is not a folder.
        blocker = make_temporary_folder(self) / "not-a-folder"
        blocker.write_text("", encoding="utf-8")
        state, output = self.play(["map", "quit"], save_path=blocker / "save.json")
        self.assertFalse(state.running)
        messages = []
        for text in output:
            if text.startswith("Could not save your progress"):
                messages.append(text)
        self.assertEqual(len(messages), 1)


    def test_a_typed_line_is_saved_before_anything_else_happens(self):
        """Code lines are saved one by one, so a killed game loses at most the line being typed."""
        save_path = make_temporary_folder(self) / "save.json"
        state = GameState(make_levels("1-1"))
        seen = []

        def read_line(prompt):
            # What is on disk when the game asks for the NEXT line.
            if save_path.exists():
                with open(save_path, encoding="utf-8") as save_file:
                    seen.append(json.load(save_file)["buffers"].get("1-1", {}).get("1", ""))
            if len(seen) > 3:
                return ":quit"
            return ["play 1-1", 'print("a")', 'print("b")'][len(seen)] if len(seen) < 3 else ":quit"

        run(state, read_line=read_line, write=lambda text: None, save_path=save_path)
        self.assertIn('print("a")\n', seen)
        self.assertIn('print("a")\nprint("b")\n', seen)

    def test_eof_in_code_mode_quits_instead_of_adding_a_line(self):
        """Ctrl-D while typing code leaves the game; "quit" must not become a code line."""
        state = GameState(make_levels("1-1"))
        player = ScriptedPlayer(["play 1-1", "x = 1"])
        run(state, read_line=player.read_line, write=lambda text: None)
        self.assertFalse(state.running)
        self.assertEqual(state.wave_text(state.levels[0], 1), "x = 1\n")

    def test_prompt_shows_the_next_line_number_in_code_mode(self):
        """"> " at the map; " 1 | " then " 2 | " while typing."""
        state = GameState(make_levels("1-1"))
        state.plain = True
        player = ScriptedPlayer(["play 1-1", "x = 1", ":quit"])
        run(state, read_line=player.read_line, write=lambda text: None)
        # The line typed at the story's pause is not lost: it is the first line of code.
        self.assertEqual(player.prompts, ["> ", "Enter to continue (s skips) > ", "  2 | "])

    def test_a_stop_request_ends_the_loop_after_the_command(self):
        """The guard's `requested` flag stops the game once the command is done and saved."""
        save_path = make_temporary_folder(self) / "save.json"
        state = GameState(make_levels("1-1"))
        guard = ShutdownGuard()
        lines = ["play 1-1", "x = 1", "y = 2"]

        def read_line(prompt):
            if len(lines) == 1:
                guard.requested = True
            return lines.pop(0)

        run(state, read_line=read_line, write=lambda text: None, save_path=save_path, guard=guard)
        self.assertFalse(state.running)
        with open(save_path, encoding="utf-8") as save_file:
            self.assertEqual(json.load(save_file)["buffers"]["1-1"]["1"], "x = 1\ny = 2\n")

    def test_a_closed_terminal_saves_and_stops(self):
        """If writing fails because the window is gone, the game still saves and ends."""
        save_path = make_temporary_folder(self) / "save.json"
        state = GameState(make_levels("1-1"))

        def broken_write(text):
            raise BrokenPipeError

        run(state, read_line=ScriptedPlayer(["play 1-1", "x = 1"]).read_line,
            write=broken_write, save_path=save_path)
        self.assertFalse(state.running)
        self.assertTrue(save_path.exists())

    def test_slither_is_drawn_as_an_animation(self):
        """Playing 1-2 after 1-1 draws frames over each other, with pauses."""
        state, output = self.play(["play 1-1", ":play 1-2", ":quit"])
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


class TestStartText(unittest.TestCase):
    """Check the screen shown when the game starts or resumes."""

    def test_new_player_starts_at_the_map(self):
        """Not coding: the map."""
        text = start_text(GameState(make_levels("1-1")))
        self.assertIn("WORLD 1", text)
        self.assertIn("[1-1]", text)

    def test_a_player_who_was_typing_lands_on_the_wave_with_the_code(self):
        """Coding: the wave screen shows the code typed so far."""
        level = make_full_level()
        state = GameState([level])
        state.current_level = "1-1"
        state.current_wave = 2
        state.coding = True
        state.set_wave_text(level, 2, 'print("SYSTEM CHECK")\nprint("VOICE')
        text = start_text(state)
        self.assertIn("WAVE 2 of 3", text)
        self.assertIn('  1 │ print("SYSTEM CHECK")', text)
        self.assertIn('  2 │ print("VOICE', text)


if __name__ == "__main__":
    unittest.main()
