"""Tests for engine/workspace.py, engine/submission.py and engine/results_screen.py."""

import unittest

from engine.level_pack import Level, Wave
from engine.results_screen import results_text
from engine.submission import grade_submission
from engine.workspace import prepare_workspace, read_wave_file, wave_file_name
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
    """Check the files made in a level's workspace."""

    def setUp(self):
        """Make a temporary workspace and a level."""
        self.root = make_temporary_folder(self)
        self.level = make_three_wave_level()

    def test_file_names(self):
        """Code waves get .py files; the predict wave gets a .txt file."""
        self.assertEqual(wave_file_name(self.level.waves[0], 1), "wave1.py")
        self.assertEqual(wave_file_name(self.level.waves[2], 3), "wave3.txt")

    def test_prepare_makes_the_files(self):
        """The fill-in file starts from the starter; the others start empty."""
        folder = prepare_workspace(self.level, self.root)
        self.assertEqual(folder, self.root / "1-1")
        self.assertEqual((folder / "wave1.py").read_text(encoding="utf-8"), "print(___)\n")
        self.assertEqual((folder / "wave2.py").read_text(encoding="utf-8"), "")
        self.assertEqual((folder / "wave3.txt").read_text(encoding="utf-8"), "")

    def test_prepare_never_overwrites(self):
        """Playing again keeps the player's work."""
        folder = prepare_workspace(self.level, self.root)
        (folder / "wave1.py").write_text('print("OK")', encoding="utf-8")
        prepare_workspace(self.level, self.root)
        self.assertEqual(read_wave_file(self.level, 1, self.root), 'print("OK")')

    def test_read_missing_file(self):
        """A file that is not there reads as None."""
        self.assertIsNone(read_wave_file(self.level, 2, self.root))


class TestSubmission(unittest.TestCase):
    """Check grading a whole level from its workspace, and the results text."""

    def setUp(self):
        """Make a workspace for the three-wave level."""
        self.root = make_temporary_folder(self)
        self.level = make_three_wave_level()
        self.folder = prepare_workspace(self.level, self.root)

    def write(self, name, text):
        """Write one wave file in the level's workspace."""
        (self.folder / name).write_text(text, encoding="utf-8")

    def test_empty_files_are_not_graded(self):
        """A wave whose file is empty has no result yet."""
        submissions = grade_submission(self.level, self.root)
        self.assertEqual(len(submissions), 3)
        self.assertIsNotNone(submissions[0].result)
        self.assertIsNone(submissions[1].result)
        self.assertIsNone(submissions[2].result)
        text = results_text(self.level, submissions)
        self.assertIn("WAVE 2 · BUILD  not started: type your code first", text)

    def test_only_some_waves(self):
        """wave_numbers picks which waves are graded."""
        submissions = grade_submission(self.level, self.root, wave_numbers=[3])
        self.assertEqual(len(submissions), 1)
        self.assertEqual(submissions[0].number, 3)

    def test_results_text_reports_each_wave(self):
        """Passed waves get a tick; failed checks and quality rules are explained."""
        self.write("wave1.py", 'print("OK")')
        self.write("wave2.py", 'print("HI")')
        self.write("wave3.txt", "ONE")
        text = results_text(self.level, grade_submission(self.level, self.root))
        self.assertIn("LEVEL 1-1 · RESULTS", text)
        self.assertIn("WAVE 1 · FILL-IN  2/2 tests passed ✓", text)
        self.assertIn("WAVE 2 · BUILD  1/2 tests passed ✗", text)
        self.assertIn("  ✗ has a comment", text)
        self.assertIn("  Code quality 3/4", text)
        self.assertIn("WAVE 3 · DEBUG  1/1 test passed ✓", text)


if __name__ == "__main__":
    unittest.main()
