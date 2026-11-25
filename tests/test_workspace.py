"""Tests for engine/workspace.py (names, starting text, the :where export), engine/submission.py and engine/results_screen.py."""

import unittest

from engine.level_pack import Level, Wave
from engine.results_screen import results_text
from engine.submission import grade_text
from engine.workspace import export_wave, level_folder, starting_text, wave_file_name
from tests.helpers import make_temporary_folder


def make_three_wave_level():
    """Return a level with a fill-in, a build and a predict wave."""
    fill_in = Wave("fill-in", "Fill in.", starter="print(___)", reference='print("OK")',
                   wrong="print(OK)", tests=[{"expected_stdout": "OK\n"}, {"require": ["Call"]}])
    build = Wave("build", "Print HI.", reference='# Greet\nprint("HI")', wrong='print("HI")',
                 tests=[{"expected_stdout": "HI\n"}, {"require_comment": True}])
    predict = Wave("debug", "What does it print?", mode="predict", code='print("ONE")',
                   answer="ONE", wrong="TWO")
    return Level("1-1", "Hello", 1, ["print()", "strings"], "status", 'print("HI")',
                 ["tip", "tip"], [fill_in, build, predict])


class TestWorkspace(unittest.TestCase):
    """Check the file names, the starting text and the export."""

    def setUp(self):
        """Make a temporary folder and a level."""
        self.root = make_temporary_folder(self)
        self.level = make_three_wave_level()

    def test_file_names(self):
        """Code waves get .py files; the predict wave gets a .txt file."""
        self.assertEqual(wave_file_name(self.level.waves[0], 1), "wave1.py")
        self.assertEqual(wave_file_name(self.level.waves[2], 3), "wave3.txt")

    def test_starting_text(self):
        """A fill-in wave starts from its starter; the others start empty."""
        self.assertEqual(starting_text(self.level.waves[0]), "print(___)\n")
        self.assertEqual(starting_text(self.level.waves[1]), "")
        self.assertEqual(starting_text(self.level.waves[2]), "")

    def test_export_writes_the_file_in_the_level_folder(self):
        """The copy is where :where says."""
        path = export_wave(self.level, 2, 'print("HI")\n', self.root)
        self.assertEqual(path, level_folder(self.level, self.root) / "wave2.py")
        self.assertEqual(path.read_text(encoding="utf-8"), 'print("HI")\n')

    def test_export_of_a_predict_wave_is_a_text_file(self):
        """wave3.txt."""
        path = export_wave(self.level, 3, "ONE\n", self.root)
        self.assertEqual(path.name, "wave3.txt")

    def test_export_overwrites_with_the_current_code(self):
        """It is a copy of what the game holds now."""
        export_wave(self.level, 2, "old\n", self.root)
        path = export_wave(self.level, 2, "new\n", self.root)
        self.assertEqual(path.read_text(encoding="utf-8"), "new\n")

    def test_nothing_in_the_game_reads_the_files_back(self):
        """grade_submission and prepare_workspace are gone: the code lives in the game."""
        import engine.submission
        import engine.workspace

        self.assertFalse(hasattr(engine.submission, "grade_submission"))
        self.assertFalse(hasattr(engine.workspace, "prepare_workspace"))
        self.assertFalse(hasattr(engine.workspace, "read_wave_file"))


class TestGradingTypedCode(unittest.TestCase):
    """Check grading typed code, and the results text."""

    def setUp(self):
        """The three-wave level."""
        self.level = make_three_wave_level()

    def submission(self, number, text):
        """Grade `text` as wave `number`."""
        return grade_text(self.level.waves[number - 1], number, text)

    def test_empty_code_is_not_graded(self):
        """A wave with no code has no result yet."""
        for text in ["", "   \n\n"]:
            self.assertIsNone(self.submission(2, text).result)
        text = results_text(self.level, [self.submission(2, "")])
        self.assertIn("WAVE 2 · BUILD  not started: type your code first", text)

    def test_results_text_reports_each_wave(self):
        """Passed waves get a tick; failed checks and quality rules are explained."""
        submissions = [
            self.submission(1, 'print("OK")'),
            self.submission(2, 'print("HI")'),
            self.submission(3, "ONE"),
        ]
        text = results_text(self.level, submissions)
        self.assertIn("LEVEL 1-1 · RESULTS", text)
        self.assertIn("WAVE 1 · FILL-IN  2/2 tests passed ✓", text)
        self.assertIn("WAVE 2 · BUILD  1/2 tests passed ✗", text)
        self.assertIn("  ✗ has a comment", text)
        self.assertIn("  Code quality 3/4", text)
        self.assertIn("WAVE 3 · DEBUG  1/1 test passed ✓", text)

    def test_only_the_graded_waves_are_in_the_results(self):
        """A submit grades one wave; the others are not mentioned."""
        text = results_text(self.level, [self.submission(3, "ONE")])
        self.assertIn("WAVE 3", text)
        self.assertNotIn("WAVE 1", text)


if __name__ == "__main__":
    unittest.main()
