"""Tests for engine/level_pack.py, using level packs in temporary folders."""

import unittest

from engine.level_pack import LevelError, load_level, load_levels
from render.boss_screen import boss_name
from tests.helpers import (
    VALID_BOSS_TOML,
    VALID_LEVEL_TOML,
    make_temporary_folder,
    write_level_pack,
)


class TestLoadLevel(unittest.TestCase):
    """Check reading one level.toml file, good and broken."""

    def load(self, text, level_folder="1-1-hello-terminal"):
        """Write `text` as a level pack in a new temporary folder and load it."""
        levels_folder = make_temporary_folder(self)
        path = write_level_pack(levels_folder, "w1", level_folder, text)
        return load_level(path)

    def broken(self, old, new):
        """Return the valid level text with `old` replaced by `new`."""
        self.assertIn(old, VALID_LEVEL_TOML)
        return VALID_LEVEL_TOML.replace(old, new)

    def test_reads_every_part_of_a_level(self):
        """A valid file gives a Level with all its parts."""
        level = self.load(VALID_LEVEL_TOML)
        self.assertEqual(level.id, "1-1")
        self.assertEqual(level.title, "Hello, Terminal")
        self.assertEqual(level.world, 1)
        self.assertEqual(level.new_concepts, ["print()", "string literals"])
        self.assertEqual(level.power_up, "status")
        self.assertIn('print("SYSTEM CHECK")', level.cutscene)
        self.assertEqual(len(level.tips), 2)
        self.assertEqual(level.folder.name, "1-1-hello-terminal")

    def test_reads_waves_and_their_tests(self):
        """Each [[wave]] becomes a Wave, with its [[wave.test]] tables."""
        level = self.load(VALID_LEVEL_TOML)
        build, debug = level.waves
        self.assertEqual(build.kind, "build")
        self.assertEqual(build.reference, 'print("OK")')
        self.assertEqual(build.tests, [{"expected_stdout": "OK\n"}])
        self.assertIsNone(build.mode)
        self.assertEqual(debug.mode, "predict")
        self.assertEqual(debug.answer, "ONE")
        self.assertIsNone(debug.reference)
        self.assertEqual(debug.tests, [])

    def test_wave_time_limit_is_read(self):
        """A wave may say how many seconds its program may run."""
        text = self.broken('kind = "build"', 'kind = "build"\ntime_limit = 10')
        level = self.load(text)
        self.assertEqual(level.waves[0].time_limit, 10)
        self.assertIsNone(level.waves[1].time_limit)

    def test_wave_time_limit_must_be_a_whole_number_of_seconds(self):
        """0, negative numbers, text, decimals and true are rejected."""
        cases = [("0", "must be at least 1"), ("-5", "must be at least 1"),
                 ('"ten"', "must be a whole number"), ("2.5", "must be a whole number"),
                 ("true", "must be a whole number")]
        for value, message in cases:
            with self.subTest(value=value):
                text = self.broken('kind = "build"', f'kind = "build"\ntime_limit = {value}')
                with self.assertRaisesRegex(LevelError, f"time_limit {message}"):
                    self.load(text)

    def test_not_toml_is_an_error(self):
        """A file that is not TOML is rejected, naming the file."""
        with self.assertRaisesRegex(LevelError, "level.toml: not valid TOML"):
            self.load("this = is = not toml")

    def test_missing_level_table_is_an_error(self):
        """Without [level] there is nothing to load."""
        with self.assertRaisesRegex(LevelError, r"needs a \[level\] table"):
            self.load('title = "Hello"\n')

    def test_missing_part_is_an_error(self):
        """Each required part is named when it is missing."""
        # Each key, with the exact text that sets it in VALID_LEVEL_TOML.
        parts = {
            "id": 'id = "1-1"\n',
            "title": 'title = "Hello, Terminal"\n',
            "world": "world = 1\n",
            "new_concepts": 'new_concepts = ["print()", "string literals"]\n',
            "power_up": 'power_up = "status"\n',
            "cutscene": 'cutscene = """\nprint("SYSTEM CHECK")\n"""\n',
            "tips": 'tips = ["print(...) shows text.", "Text in quotes is a string literal."]\n',
        }
        for key in parts:
            with self.subTest(key=key):
                text = self.broken(parts[key], "")
                with self.assertRaisesRegex(LevelError, f"{key} is missing"):
                    self.load(text)

    def test_world_must_be_a_whole_number(self):
        """world = "one" or world = true is rejected."""
        for value in ['"one"', "true", "1.5"]:
            with self.subTest(value=value):
                with self.assertRaisesRegex(LevelError, "world must be a whole number"):
                    self.load(self.broken("world = 1", f"world = {value}"))

    def test_title_must_be_text(self):
        """title = 42 is rejected."""
        with self.assertRaisesRegex(LevelError, "title must be text"):
            self.load(self.broken('title = "Hello, Terminal"', "title = 42"))

    def test_tips_must_be_a_list_of_text(self):
        """tips = "one tip" or tips = [1, 2] is rejected."""
        tips_line = 'tips = ["print(...) shows text.", "Text in quotes is a string literal."]'
        with self.assertRaisesRegex(LevelError, "tips must be a list"):
            self.load(self.broken(tips_line, 'tips = "one tip"'))
        with self.assertRaisesRegex(LevelError, "every item in tips"):
            self.load(self.broken(tips_line, "tips = [1, 2]"))

    def test_too_few_or_too_many_concepts_is_an_error(self):
        """A level has 2 to 4 new concepts."""
        concepts_line = 'new_concepts = ["print()", "string literals"]'
        for concepts in ['["print()"]', '["a", "b", "c", "d", "e"]']:
            with self.subTest(concepts=concepts):
                text = self.broken(concepts_line, f"new_concepts = {concepts}")
                with self.assertRaisesRegex(LevelError, "2 to 4 new concepts"):
                    self.load(text)

    def test_one_tip_per_concept(self):
        """Three tips for two concepts is an error."""
        tips_line = 'tips = ["print(...) shows text.", "Text in quotes is a string literal."]'
        text = self.broken(tips_line, 'tips = ["one", "two", "three"]')
        with self.assertRaisesRegex(LevelError, "one tip per new concept"):
            self.load(text)

    def test_folder_must_start_with_the_level_id(self):
        """Level 1-1 cannot live in a folder called 1-2-something."""
        with self.assertRaisesRegex(LevelError, "folder name must start with the level id"):
            self.load(VALID_LEVEL_TOML, level_folder="1-2-hello-terminal")

    def test_level_without_waves_is_an_error(self):
        """A level needs at least one wave."""
        text = VALID_LEVEL_TOML[: VALID_LEVEL_TOML.index("[[wave]]")]
        with self.assertRaisesRegex(LevelError, "at least one"):
            self.load(text)

    def test_unknown_wave_kind_is_an_error(self):
        """A wave's kind must be fill-in, build or debug."""
        text = self.broken('kind = "build"', 'kind = "boss"')
        with self.assertRaisesRegex(LevelError, "wave 1: kind must be one of"):
            self.load(text)

    def test_wave_without_wrong_solution_is_an_error(self):
        """Every wave needs a typical wrong solution."""
        text = self.broken('wrong = "print(OK)"\n', "")
        with self.assertRaisesRegex(LevelError, "wave 1: wrong is missing"):
            self.load(text)

    def test_build_wave_without_reference_is_an_error(self):
        """A wave that is not a predict wave needs a reference solution."""
        text = self.broken("reference = 'print(\"OK\")'\n", "")
        with self.assertRaisesRegex(LevelError, "wave 1: reference is missing"):
            self.load(text)

    def test_predict_wave_without_answer_is_an_error(self):
        """A predict wave needs the right answer instead of a reference."""
        text = self.broken('answer = "ONE"\n', "")
        with self.assertRaisesRegex(LevelError, "wave 2: answer is missing"):
            self.load(text)


class TestLoadTests(unittest.TestCase):
    """Check that the loader rejects [[wave.test]] tables the grader cannot run."""

    TEST_LINE = 'expected_stdout = "OK\\n"'

    def load_with_test(self, test_text):
        """Load the valid level with its one test table replaced by `test_text`."""
        self.assertIn(self.TEST_LINE, VALID_LEVEL_TOML)
        text = VALID_LEVEL_TOML.replace(self.TEST_LINE, test_text)
        levels_folder = make_temporary_folder(self)
        return load_level(write_level_pack(levels_folder, "w1", "1-1-hello-terminal", text))

    def test_every_kind_of_test_loads(self):
        """Each kind of test, written correctly, is accepted."""
        good_tests = [
            'expected_stdout = "OK\\n"\nstdin = "x\\n"',
            'expected_stdout_contains = ["OK"]',
            'call = "add"\nargs = [1, 2]\nexpected = 3',
            'require = ["While", "Call"]',
            'forbid = ["For"]',
            "require_comment = true",
        ]
        for test_text in good_tests:
            with self.subTest(test=test_text):
                self.load_with_test(test_text)

    def test_no_kind_or_two_kinds_is_an_error(self):
        """A test needs exactly one kind key."""
        for test_text in ['stdin = "x"', 'require = ["Call"]\nforbid = ["For"]']:
            with self.subTest(test=test_text):
                with self.assertRaisesRegex(LevelError, "test 1: a test needs exactly one of"):
                    self.load_with_test(test_text)

    def test_unknown_ast_node_is_an_error(self):
        """require = ["Loop"] is not a real AST node type."""
        with self.assertRaisesRegex(LevelError, "'Loop' is not a Python AST node type"):
            self.load_with_test('require = ["Loop"]')

    def test_call_needs_expected(self):
        """A call test without expected is rejected."""
        with self.assertRaisesRegex(LevelError, "needs an expected value"):
            self.load_with_test('call = "add"')

    def test_call_args_must_be_a_list(self):
        """args = 3 is rejected."""
        with self.assertRaisesRegex(LevelError, "args must be a list"):
            self.load_with_test('call = "add"\nargs = 3\nexpected = 3')

    def test_stdin_must_be_text(self):
        """stdin = 5 is rejected."""
        with self.assertRaisesRegex(LevelError, "stdin must be text"):
            self.load_with_test('expected_stdout = "OK"\nstdin = 5')


class TestLoadHints(unittest.TestCase):
    """Check the optional hints of a wave."""

    def load_with_hints(self, hints_line):
        """Load the valid level with `hints_line` added to its first wave."""
        text = VALID_LEVEL_TOML.replace('wrong = "print(OK)"\n', 'wrong = "print(OK)"\n' + hints_line + "\n")
        levels_folder = make_temporary_folder(self)
        return load_level(write_level_pack(levels_folder, "w1", "1-1-hello-terminal", text))

    def test_three_hints_load(self):
        """Three hints are read in order; a wave without hints has none."""
        level = self.load_with_hints('hints = ["Nudge.", "Outline.", "Partial."]')
        self.assertEqual(level.waves[0].hints, ["Nudge.", "Outline.", "Partial."])
        self.assertEqual(level.waves[1].hints, [])

    def test_two_hints_is_an_error(self):
        """A wave with hints has exactly three."""
        with self.assertRaisesRegex(LevelError, "a wave has 3 hints"):
            self.load_with_hints('hints = ["Nudge.", "Outline."]')


class TestLoadLevels(unittest.TestCase):
    """Check finding every level in a levels folder."""

    def setUp(self):
        """Make an empty levels folder for each test."""
        self.levels_folder = make_temporary_folder(self)

    def write(self, world_folder, level_folder, level_id):
        """Write a valid level pack with the given id."""
        text = VALID_LEVEL_TOML.replace('id = "1-1"', f'id = "{level_id}"')
        write_level_pack(self.levels_folder, world_folder, level_folder, text)

    def test_missing_folder_gives_no_levels(self):
        """A levels folder that does not exist means there are no levels."""
        self.assertEqual(load_levels(self.levels_folder / "nothing-here"), [])

    def test_levels_come_in_map_order(self):
        """Levels are ordered by world folder, then by level folder name."""
        self.write("w2", "2-1-sensors", "2-1")
        self.write("w1", "boss-1-bootloader", "boss-1")
        self.write("w1", "1-2-memory", "1-2")
        self.write("w1", "1-1-hello", "1-1")
        ids = []
        for level in load_levels(self.levels_folder):
            ids.append(level.id)
        self.assertEqual(ids, ["1-1", "1-2", "boss-1", "2-1"])

    def test_same_id_twice_is_an_error(self):
        """Two folders cannot hold the same level id."""
        self.write("w1", "1-1-hello", "1-1")
        self.write("w1", "1-1-hello-again", "1-1")
        with self.assertRaisesRegex(LevelError, "1-1 is used twice"):
            load_levels(self.levels_folder)

    def test_the_last_boss_is_boss_8_in_world_8(self):
        """boss-8 loads from w8/, is a boss, and is shown as BOSS 8."""
        text = VALID_BOSS_TOML.replace('id = "boss-1"', 'id = "boss-8"').replace("world = 1", "world = 8")
        write_level_pack(self.levels_folder, "w8", "boss-8-factory-wakes", text)
        levels = load_levels(self.levels_folder)
        self.assertEqual(levels[0].id, "boss-8")
        self.assertEqual(levels[0].world, 8)
        self.assertTrue(levels[0].boss)
        self.assertEqual(boss_name(levels[0].id), "BOSS 8")

    def test_folders_without_level_toml_are_skipped(self):
        """Only folders with a level.toml file are levels."""
        (self.levels_folder / "w1" / "notes").mkdir(parents=True)
        self.write("w1", "1-1-hello", "1-1")
        self.assertEqual(len(load_levels(self.levels_folder)), 1)


if __name__ == "__main__":
    unittest.main()
