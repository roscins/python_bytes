"""Check tools/level_brief.py: a short plain-text brief for one level."""

import io
import unittest

from grader.progression import load_curriculum
from tools.level_brief import brief_lines, main

MAX_LINES = 40
MAX_WIDTH = 100


def run_tool(arguments):
    """Run main() with `arguments` and return (exit code, printed lines)."""
    out = io.StringIO()
    code = main(arguments, out)
    return code, out.getvalue().splitlines()


class TestBrief(unittest.TestCase):
    """What the brief says."""

    @classmethod
    def setUpClass(cls):
        """Load the real curriculum once."""
        cls.curriculum = load_curriculum()

    def brief(self, level_id):
        """Return the brief of a level as one text."""
        return "\n".join(brief_lines(self.curriculum, level_id))

    def test_header_facts(self):
        """Id, title, world, difficulty, power-up and outcomes are there."""
        text = self.brief("1-3")
        self.assertIn("1-3", text)
        self.assertIn("Power Calculations", text)
        self.assertIn("World 1", text)
        self.assertIn("Boot Sector", text)
        self.assertIn("Difficulty: 2", text)
        self.assertIn("calc", text)
        self.assertIn("B2", text)

    def test_concepts_story_and_mission(self):
        """The headline concepts, the story and the mission."""
        text = self.brief("1-3")
        self.assertIn("round()", text)
        self.assertIn("battery controller", text)
        self.assertIn("remaining run-time", text)

    def test_recycled_levels_have_id_and_title(self):
        """1-3 recycles 1-2, which is called Memory Cells."""
        self.assertIn("1-2 Memory Cells", self.brief("1-3"))

    def test_level_without_recycles_says_none(self):
        """1-1 recycles nothing."""
        self.assertIn("Recycles: none", self.brief("1-1"))

    def test_constructs_are_cumulative_and_new_ones_are_marked(self):
        """1-3 allows 1-1's print, and marks its own round with a star."""
        text = self.brief("1-3")
        self.assertIn("print", text)
        self.assertNotIn("print*", text)
        self.assertIn("round*", text)
        self.assertIn("type", text)
        self.assertNotIn("type*", text)

    def test_later_constructs_are_not_in_the_brief(self):
        """1-3 does not allow while loops, which arrive in 2-3."""
        self.assertNotIn("While", self.brief("1-3"))
        self.assertIn("While*", self.brief("2-3"))

    def test_constructs_are_grouped_by_kind(self):
        """Lines start with the kind: call, method, import."""
        text = self.brief("4-3")
        self.assertIn("  call: ", text)
        self.assertIn("  method: ", text)
        self.assertIn("  import: ", text)

    def test_boss_brief(self):
        """A boss has no power-up and adds nothing."""
        text = self.brief("boss-1")
        self.assertIn("BOSS 1 (boss-1)", text)
        self.assertIn("none", text)
        self.assertNotIn("*", text)

    def test_technique_level_says_so(self):
        """2-5 teaches a method, not syntax."""
        self.assertIn("technique", self.brief("2-5"))

    def test_every_brief_fits_in_forty_short_lines(self):
        """Even the last level, which allows 170 constructs."""
        for level_id in self.curriculum.ids():
            lines = brief_lines(self.curriculum, level_id)
            with self.subTest(level=level_id):
                self.assertLessEqual(len(lines), MAX_LINES)
                for line in lines:
                    self.assertLessEqual(len(line), MAX_WIDTH, line)

    def test_every_allowed_construct_is_shown(self):
        """Nothing is left out, whatever the level."""
        text = self.brief("8-5")
        for construct in self.curriculum.allowed_set("8-5"):
            kind, _, name = construct.rpartition(":")
            with self.subTest(construct=construct):
                self.assertIn(name, text)


class TestCommandLine(unittest.TestCase):
    """The script's arguments and exit codes."""

    def test_known_id(self):
        """The brief is printed and the exit code is 0."""
        code, lines = run_tool(["1-1"])
        self.assertEqual(code, 0)
        self.assertIn("Hello, Terminal", "\n".join(lines))

    def test_unknown_id_is_one_line_and_exit_one(self):
        """An id that does not exist."""
        code, lines = run_tool(["9-9"])
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 1)
        self.assertIn("9-9", lines[0])

    def test_wrong_number_of_arguments(self):
        """No id, or two ids, prints one usage line and exits with 1."""
        for arguments in ([], ["1-1", "1-2"]):
            code, lines = run_tool(arguments)
            self.assertEqual(code, 1)
            self.assertEqual(len(lines), 1)
            self.assertIn("Usage", lines[0])


if __name__ == "__main__":
    unittest.main()
