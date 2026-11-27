"""Wave data files: loading, the sandbox folder, grading and showing them."""

import unittest

from engine.commands import handle_line, run_command
from engine.game_state import GameState
from engine.level_pack import LevelError, load_level
from grader.wave_grader import grade_wave
from runner.process import run_code
from runner.repl import ReplSession
from tests.helpers import VALID_LEVEL_TOML, make_temporary_folder, write_level_pack

WAVE = '''
[[wave]]
kind = "build"
brief = "Copy the first line."
files = ["a.csv"]
reference = """
with open("a.csv") as source:
    first = source.readline()
with open("out.txt", "w") as target:
    target.write(first)
print(first.strip())
"""
wrong = 'print("1,2")'

[[wave.test]]
expected_stdout = "1,2"

[[wave.test]]
expected_stdout = "7,8"
files = { "a.csv" = "b.csv" }

[[wave.test]]
expected_file = { name = "out.txt", contents = "7,8" }
files = { "a.csv" = "b.csv" }
'''


def load(test, wave_text=WAVE):
    """Write a level with two data files and load it."""
    levels = make_temporary_folder(test)
    text = VALID_LEVEL_TOML.split("[[wave]]")[0] + wave_text
    path = write_level_pack(levels, "w1", "1-1-files", text)
    (path.parent / "files").mkdir()
    (path.parent / "files" / "a.csv").write_text("1,2\n", encoding="utf-8")
    (path.parent / "files" / "b.csv").write_text("7,8\n", encoding="utf-8")
    return load_level(path)


class TestDataFiles(unittest.TestCase):
    """From the level folder to the player's program."""

    def test_reference_passes_and_fixed_text_fails(self):
        """The second dataset catches printing the expected text."""
        wave = load(self).waves[0]
        self.assertTrue(grade_wave(wave, wave.reference).all_passed())
        self.assertEqual(grade_wave(wave, wave.wrong).passed_count(), 1)

    def test_bad_names_and_missing_files_are_rejected(self):
        """No folders, no .py, no reserved or unknown names."""
        for name in ["../a.csv", "x.py", "call.json", "none.csv"]:
            with self.subTest(name=name), self.assertRaises(LevelError):
                load(self, WAVE.replace('files = ["a.csv"]', f'files = ["{name}"]'))

    def test_a_run_reports_only_what_it_wrote(self):
        """The untouched data file is not listed."""
        result = run_code('open("n.txt", "w").write("hi")', data={"a.csv": "1\n"})
        self.assertEqual(result.written, {"n.txt": "hi"})

    def test_the_console_gets_a_copy(self):
        """Open works in the quick console."""
        session = ReplSession()
        self.addCleanup(session.close)
        session.data = {"a.csv": "1,2\n"}
        self.assertIn("1,2", session.run('open("a.csv").read()').output)

    def test_the_console_forgets_the_files_of_the_wave_before(self):
        """A new wave's files replace the old ones."""
        session = ReplSession()
        self.addCleanup(session.close)
        session.data = {"a.csv": "1\n"}
        session.run("1")
        session.data = {"b.csv": "2\n"}
        self.assertIn("False", session.run('__import__("os").path.exists("a.csv")').output)

    def test_show_where_and_run(self):
        """The player can read the file, export it and see what was written."""
        level = load(self)
        state = GameState([level])
        state.current_level = level.id
        state.coding = True
        state.workspace_root = make_temporary_folder(self)
        self.assertIn("1 | 1,2", handle_line(state, ":show a.csv"))
        self.assertIn("1 | 1,2", run_command(state, "show a.csv", colon=False))
        run_command(state, "where", colon=False)
        self.assertTrue((state.workspace_root / "1-1" / "a.csv").is_file())
        state.set_wave_text(level, 1, 'open("o.txt", "w").write("done")\n')
        self.assertIn("WROTE o.txt", handle_line(state, ":run"))


if __name__ == "__main__":
    unittest.main()
