"""Check tools/check_level.py: PASS or FAIL, with one short line per problem.

The tests copy the real Level 1-1 into a temporary folder, break one thing
in the copy, and read what the tool prints.
"""

import io
import unittest
from pathlib import Path

from tests.helpers import make_temporary_folder
from tools.check_level import check_file, main

PROJECT_FOLDER = Path(__file__).parent.parent
LEVEL_1_1 = PROJECT_FOLDER / "levels" / "w1" / "1-1-hello-terminal" / "level.toml"
LEVELS_FOLDER = PROJECT_FOLDER / "levels"

BUILD_REFERENCE_END = 'print("HELLO, TECHNICIAN")\n\'\'\'\nwrong'


def write_level(test, replacements=()):
    """Copy Level 1-1 into a temporary folder, changing text, and return the new path.

    `replacements` is a list of (old, new) pairs; each old text must be in
    the file exactly once, so a typo in a test cannot go unnoticed.
    """
    text = LEVEL_1_1.read_text(encoding="utf-8")
    for old, new in replacements:
        test.assertEqual(text.count(old), 1, old)
        text = text.replace(old, new)
    folder = make_temporary_folder(test) / "w1" / "1-1-hello-terminal"
    folder.mkdir(parents=True)
    path = folder / "level.toml"
    path.write_text(text, encoding="utf-8")
    return path


def run_tool(arguments, levels_folder=LEVELS_FOLDER):
    """Run main() with `arguments` and return (exit code, printed lines)."""
    out = io.StringIO()
    code = main(arguments, out, levels_folder)
    return code, out.getvalue().splitlines()


class TestPassing(unittest.TestCase):
    """A good level."""

    def test_real_level_passes(self):
        """The real Level 1-1 prints PASS 1-1 and exits with 0."""
        code, lines = run_tool([str(LEVEL_1_1)])
        self.assertEqual(lines, ["PASS 1-1"])
        self.assertEqual(code, 0)

    def test_a_folder_is_accepted_instead_of_a_file(self):
        """The folder of a level means its level.toml."""
        code, lines = run_tool([str(LEVEL_1_1.parent)])
        self.assertEqual(lines, ["PASS 1-1"])

    def test_no_arguments_checks_every_level_pack(self):
        """With no arguments the tool walks levels/ and every level passes."""
        code, lines = run_tool([])
        self.assertEqual(code, 0)
        self.assertIn("PASS 1-1", lines)
        for line in lines:
            self.assertTrue(line.startswith("PASS "), line)

    def test_no_arguments_in_an_empty_folder_is_an_error(self):
        """Nothing to check is reported, with exit code 1."""
        empty = make_temporary_folder(self)
        code, lines = run_tool([], levels_folder=empty)
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 1)

    def test_several_files(self):
        """Every file gets its own result, and the exit code is 1 if one fails."""
        good = write_level(self)
        bad = write_level(self, [('title = "Hello, Terminal"', 'title = "Other"')])
        code, lines = run_tool([str(good), str(bad)])
        self.assertEqual(lines[0], "PASS 1-1")
        self.assertEqual(lines[1], "FAIL 1-1")
        self.assertEqual(code, 1)


class TestFailing(unittest.TestCase):
    """One thing broken at a time."""

    def fails_with(self, replacements, text):
        """Check that the broken level fails with a line containing `text`."""
        path = write_level(self, replacements)
        code, lines = run_tool([str(path)])
        self.assertEqual(code, 1)
        self.assertEqual(lines[0], "FAIL 1-1")
        found = False
        for line in lines[1:]:
            self.assertTrue(line.startswith("  "), line)
            if text in line:
                found = True
        self.assertTrue(found, lines)
        return lines

    def test_construct_from_a_later_level(self):
        """round() in a reference solution is a rule 1 problem."""
        lines = self.fails_with([(BUILD_REFERENCE_END, 'print(round(1))\n\'\'\'\nwrong')],
                                "call:round")
        self.assertTrue("wave 2 (build) reference" in " ".join(lines))

    def test_reference_that_fails_its_tests(self):
        """A reference that prints the wrong text fails the wave's tests."""
        self.fails_with([('reference = \'\'\'print("SNEK ONLINE")\'\'\'',
                          'reference = \'\'\'print("NOPE")\'\'\'')],
                        "reference")

    def test_wrong_solution_that_passes(self):
        """A wrong solution must fail; this one is the reference with a comment."""
        self.fails_with([('wrong = \'\'\'print(SNEK ONLINE)\'\'\'',
                          'wrong = \'\'\'print("SNEK ONLINE")  # same\'\'\'')],
                        "wrong solution")

    def test_level_file_differs_from_concepts_toml(self):
        """A different power-up is reported."""
        self.fails_with([('power_up = "status"', 'power_up = "other"')], "power")

    def test_style_limit(self):
        """The word "easy" in a brief breaks the style guide."""
        old = 'brief = "Fill in the blank so Snek says SNEK ONLINE."'
        self.fails_with([(old, 'brief = "An easy one: fill in the blank so Snek says SNEK ONLINE."')],
                        "easy")

    def test_loader_error_is_one_line_without_a_traceback(self):
        """A missing power_up is reported by the loader."""
        path = write_level(self, [('power_up = "status"\n', "")])
        code, lines = run_tool([str(path)])
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("FAIL "))
        self.assertIn("power_up", lines[1])
        self.assertNotIn("Traceback", "\n".join(lines))

    def test_level_missing_from_concepts_toml(self):
        """An id that concepts.toml does not know."""
        path = write_level(self, [('id = "1-1"', 'id = "9-9"')])
        # The folder name must start with the id, so rename the folder.
        renamed = path.parent.with_name("9-9-hello")
        path.parent.rename(renamed)
        code, lines = run_tool([str(renamed / "level.toml")])
        self.assertEqual(lines[0], "FAIL 9-9")
        self.assertIn("concepts.toml", lines[1])

    def test_missing_file(self):
        """A path that does not exist."""
        code, lines = run_tool(["no/such/level.toml"])
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("FAIL "))

    def test_problem_lines_are_short(self):
        """No line is longer than 120 characters."""
        path = write_level(self, [(BUILD_REFERENCE_END, 'print(round(1))\n\'\'\'\nwrong')])
        code, lines = run_tool([str(path)])
        for line in lines:
            self.assertLessEqual(len(line), 120, line)


class TestCheckFile(unittest.TestCase):
    """check_file() gives the name and the list of problems."""

    def test_good_file(self):
        """No problems."""
        name, problems = check_file(LEVEL_1_1)
        self.assertEqual(name, "1-1")
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
