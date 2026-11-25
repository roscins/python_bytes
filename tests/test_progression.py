"""Check grader/progression.py: the curriculum data and the six rules.

Rules 2-6 are tested on small made-up curricula, one broken rule at a
time, and on the real levels/concepts.toml, which must break none.
Rule 1 is tested on pieces of code against the real curriculum.
"""

import unittest
from pathlib import Path

from engine.level_pack import load_level
from tests.helpers import make_full_level as make_level
from grader.progression import (
    check_code,
    check_curriculum,
    check_item,
    check_level_code,
    check_level_matches,
    load_curriculum,
    parse_curriculum,
)

PROJECT_FOLDER = Path(__file__).parent.parent
LEVEL_1_1 = PROJECT_FOLDER / "levels" / "w1" / "1-1-hello-terminal" / "level.toml"


def make_item(item_id, world, difficulty, **changes):
    """Return a table for one item of a made-up curriculum.

    The item is a normal level that adds one construct and covers outcome
    B1. Keyword arguments replace any of the fields.
    """
    item = {
        "id": item_id,
        "world": world,
        "title": "Title " + item_id,
        "concepts": ["one", "two"],
        "constructs": ["construct:" + item_id],
        "recycles": [],
        "difficulty": difficulty,
        "outcomes": ["B1"],
        "power_up": "up-" + item_id,
        "mission": "Do something.",
    }
    item.update(changes)
    return item


def make_boss(world, difficulty, **changes):
    """Return a table for the boss of a made-up world."""
    boss = {
        "id": f"boss-{world}",
        "world": world,
        "title": "Boss",
        "boss": True,
        "constructs": [],
        "recycles": [],
        "difficulty": difficulty,
        "outcomes": ["B1"],
        "mission": "Fight.",
    }
    boss.update(changes)
    return boss


def make_curriculum(items, codes=("B1",)):
    """Build a Curriculum from item tables, with the given outcome codes."""
    return parse_curriculum({"meta": {"outcome_codes": list(codes)}, "level": items})


def good_items():
    """Return two worlds of items that break no rule."""
    return [
        make_item("1-1", 1, 1),
        make_item("1-2", 1, 2, recycles=["1-1"]),
        make_boss(1, 2, recycles=["1-1", "1-2"]),
        make_item("2-1", 2, 1),
        make_boss(2, 2),
    ]


def problems_with(items, codes=("B1",)):
    """Return the problems check_curriculum finds in a made-up curriculum."""
    return check_curriculum(make_curriculum(items, codes))


def mentions(problems, text):
    """Return True if any problem contains `text`."""
    for problem in problems:
        if text in problem:
            return True
    return False


class TestLoading(unittest.TestCase):
    """Reading levels/concepts.toml and asking what is allowed."""

    @classmethod
    def setUpClass(cls):
        """Load the real curriculum once."""
        cls.curriculum = load_curriculum()

    def test_all_items_are_loaded_in_file_order(self):
        """48 items: 40 levels and 8 bosses, World 1 first."""
        ids = self.curriculum.ids()
        self.assertEqual(len(ids), 48)
        self.assertEqual(ids[0], "1-1")
        self.assertEqual(ids[5], "boss-1")
        self.assertEqual(ids[-1], "boss-8")

    def test_find_gives_the_item_or_none(self):
        """find() returns the item, or None for an unknown id."""
        self.assertEqual(self.curriculum.find("1-3").title, "Power Calculations")
        self.assertIsNone(self.curriculum.find("9-9"))

    def test_first_level_allows_only_its_own_constructs(self):
        """In 1-1 only print and string literals are allowed."""
        allowed = self.curriculum.allowed_set("1-1")
        self.assertEqual(allowed, {"call:print", "Constant:str"})

    def test_allowed_constructs_grow_and_say_where_they_came_from(self):
        """Level 1-2 allows 1-1's constructs and adds its own, with their origin."""
        pairs = self.curriculum.allowed_constructs("1-2")
        self.assertEqual(pairs[0], ("call:print", "1-1"))
        self.assertIn(("call:type", "1-2"), pairs)
        self.assertNotIn("call:round", self.curriculum.allowed_set("1-2"))

    def test_new_constructs_are_only_this_levels(self):
        """new_constructs lists what one item adds."""
        self.assertIn("call:round", self.curriculum.new_constructs("1-3"))
        self.assertNotIn("call:print", self.curriculum.new_constructs("1-3"))

    def test_boss_allows_what_its_world_allows(self):
        """A boss adds nothing, so it allows exactly what the last level allows."""
        self.assertEqual(self.curriculum.allowed_set("boss-1"), self.curriculum.allowed_set("1-5"))

    def test_unknown_id_raises_key_error(self):
        """Asking about an id that is not there is an error."""
        with self.assertRaises(KeyError):
            self.curriculum.allowed_set("9-9")

    def test_real_curriculum_breaks_no_rule(self):
        """levels/concepts.toml passes rules 2-6 and the extra checks."""
        self.assertEqual(check_curriculum(self.curriculum), [])


class TestRuleTwo(unittest.TestCase):
    """Bosses add no constructs."""

    def test_good_curriculum_passes(self):
        """The made-up good curriculum breaks nothing."""
        self.assertEqual(problems_with(good_items()), [])

    def test_boss_with_constructs_is_reported(self):
        """A boss that lists a construct breaks rule 2."""
        items = good_items()
        items[2] = make_boss(1, 2, constructs=["call:print"], recycles=["1-1", "1-2"])
        problems = problems_with(items)
        self.assertTrue(mentions(problems, "rule 2"))
        self.assertTrue(mentions(problems, "boss-1"))


class TestRuleThree(unittest.TestCase):
    """A level adds a construct, unless it is a technique level."""

    def test_level_without_constructs_is_reported(self):
        """An empty list breaks rule 3."""
        items = good_items()
        items[1] = make_item("1-2", 1, 2, constructs=[], recycles=["1-1"])
        self.assertTrue(mentions(problems_with(items), "rule 3"))

    def test_technique_level_may_add_nothing(self):
        """technique = true allows an empty list."""
        items = good_items()
        items[1] = make_item("1-2", 1, 2, constructs=[], technique=True, recycles=["1-1"])
        self.assertEqual(problems_with(items), [])


class TestRuleFour(unittest.TestCase):
    """Every outcome code appears in a non-boss level."""

    def test_outcome_only_in_a_boss_is_reported(self):
        """B2 appears only in a boss, so nothing teaches it."""
        items = good_items()
        items[2] = make_boss(1, 2, outcomes=["B1", "B2"], recycles=["1-1", "1-2"])
        problems = problems_with(items, codes=("B1", "B2"))
        self.assertTrue(mentions(problems, "rule 4"))
        self.assertTrue(mentions(problems, "B2"))

    def test_outcome_in_a_level_is_fine(self):
        """B2 in a level is enough."""
        items = good_items()
        items[1] = make_item("1-2", 1, 2, outcomes=["B1", "B2"], recycles=["1-1"])
        self.assertEqual(problems_with(items, codes=("B1", "B2")), [])

    def test_unknown_outcome_code_is_reported(self):
        """An item cannot name a code that meta does not list."""
        items = good_items()
        items[1] = make_item("1-2", 1, 2, outcomes=["B1", "Z9"], recycles=["1-1"])
        problems = problems_with(items)
        self.assertTrue(mentions(problems, "Z9"))


class TestRuleFive(unittest.TestCase):
    """Difficulty never decreases; boss at least the maximum; new world starts low."""

    def test_decrease_inside_a_world_is_reported(self):
        """1-2 easier than 1-1 breaks rule 5."""
        items = good_items()
        items[0] = make_item("1-1", 1, 2)
        items[1] = make_item("1-2", 1, 1, recycles=["1-1"])
        problems = problems_with(items)
        self.assertTrue(mentions(problems, "rule 5"))
        self.assertTrue(mentions(problems, "1-2"))

    def test_boss_below_the_world_maximum_is_reported(self):
        """A boss easier than its hardest level breaks rule 5."""
        items = good_items()
        items[2] = make_boss(1, 1, recycles=["1-1", "1-2"])
        self.assertTrue(mentions(problems_with(items), "boss-1"))

    def test_new_world_must_start_below_the_previous_boss(self):
        """World 2 starting at 2 after a boss of 2 breaks rule 5 (limit is 1)."""
        items = good_items()
        items[3] = make_item("2-1", 2, 2)
        problems = problems_with(items)
        self.assertTrue(mentions(problems, "2-1"))
        self.assertTrue(mentions(problems, "rule 5"))

    def test_new_world_may_start_one_below_the_previous_boss(self):
        """Boss 2, next world 1: allowed."""
        self.assertEqual(problems_with(good_items()), [])

    def test_equal_difficulty_is_fine(self):
        """Difficulty may stay the same."""
        items = good_items()
        items[1] = make_item("1-2", 1, 1, recycles=["1-1"])
        self.assertEqual(problems_with(items), [])


class TestRuleSix(unittest.TestCase):
    """recycles names only earlier items."""

    def test_recycling_a_later_item_is_reported(self):
        """1-1 cannot recycle 1-2."""
        items = good_items()
        items[0] = make_item("1-1", 1, 1, recycles=["1-2"])
        problems = problems_with(items)
        self.assertTrue(mentions(problems, "rule 6"))
        self.assertTrue(mentions(problems, "1-2"))

    def test_recycling_an_unknown_item_is_reported(self):
        """An id that does not exist is reported."""
        items = good_items()
        items[1] = make_item("1-2", 1, 2, recycles=["7-7"])
        self.assertTrue(mentions(problems_with(items), "7-7"))

    def test_recycling_itself_is_reported(self):
        """An item is not earlier than itself."""
        items = good_items()
        items[1] = make_item("1-2", 1, 2, recycles=["1-2"])
        self.assertTrue(mentions(problems_with(items), "rule 6"))

    def test_recycling_a_boss_of_an_earlier_world_is_fine(self):
        """5-1 recycles boss-4 in the real curriculum, so bosses can be recycled."""
        items = good_items()
        items[3] = make_item("2-1", 2, 1, recycles=["boss-1"])
        self.assertEqual(problems_with(items), [])


class TestExtraChecks(unittest.TestCase):
    """Limits that are not numbered rules."""

    def test_too_few_or_too_many_concepts(self):
        """A level has 2 to 4 concepts."""
        items = good_items()
        items[1] = make_item("1-2", 1, 2, concepts=["only one"], recycles=["1-1"])
        self.assertTrue(mentions(problems_with(items), "concepts"))
        items[1] = make_item("1-2", 1, 2, concepts=["a", "b", "c", "d", "e"], recycles=["1-1"])
        self.assertTrue(mentions(problems_with(items), "concepts"))

    def test_duplicate_ids_are_reported(self):
        """Two items with the same id."""
        items = good_items()
        items[1] = make_item("1-1", 1, 2)
        self.assertTrue(mentions(problems_with(items), "twice"))

    def test_check_item_reports_only_that_item(self):
        """check_item looks at one item."""
        items = good_items()
        items[1] = make_item("1-2", 1, 2, constructs=[], recycles=["1-1"])
        curriculum = make_curriculum(items)
        self.assertEqual(check_item(curriculum, "1-1"), [])
        self.assertTrue(mentions(check_item(curriculum, "1-2"), "rule 3"))

    def test_check_item_unknown_id(self):
        """An unknown id is reported as a problem, not an exception."""
        self.assertTrue(mentions(check_item(make_curriculum(good_items()), "9-9"), "9-9"))


class TestRuleOne(unittest.TestCase):
    """Code may use only constructs from this level or an earlier one."""

    @classmethod
    def setUpClass(cls):
        """Load the real curriculum once."""
        cls.curriculum = load_curriculum()

    def check(self, level_id, code):
        """Return the rule 1 problems of `code` in level `level_id`."""
        return check_code(self.curriculum, level_id, code, "cutscene")

    def test_allowed_code_has_no_problems(self):
        """print("hi") is Level 1-1 code."""
        self.assertEqual(self.check("1-1", 'print("hi")'), [])

    def test_later_construct_is_reported_with_where_it_is_taught(self):
        """round() in 1-1 is reported, and the message says 1-3 teaches it."""
        problems = self.check("1-1", 'print(round(1))')
        self.assertTrue(mentions(problems, "call:round"))
        self.assertTrue(mentions(problems, "1-3"))
        self.assertTrue(mentions(problems, "cutscene"))
        self.assertTrue(mentions(problems, "line 1"))

    def test_the_same_code_is_fine_in_the_level_that_teaches_it(self):
        """round() is allowed in 1-3 and later."""
        self.assertEqual(self.check("1-3", "x = round(2.5)\nprint(x)"), [])
        self.assertEqual(self.check("2-1", "x = round(2.5)\nprint(x)"), [])

    def test_unlisted_construct_is_reported_as_not_listed(self):
        """`global` is in no level."""
        problems = self.check("8-5", "def f():\n    global x\n    x = 1")
        self.assertTrue(mentions(problems, "Global"))
        self.assertTrue(mentions(problems, "not listed"))

    def test_if_is_not_yet_allowed_in_1_4(self):
        """Comparisons arrive in 1-4, if only in 2-2."""
        code = "x = 1\nif x == 1:\n    print(x)"
        self.assertTrue(mentions(self.check("1-4", code), "If"))
        self.assertEqual(self.check("2-2", code), [])

    def test_comparison_operators_arrive_in_1_4(self):
        """print(0.1 + 0.2 == 0.3) is a 1-4 program."""
        code = "print(0.1 + 0.2 == 0.3)"
        self.assertTrue(mentions(self.check("1-3", code), "Compare:Eq"))
        self.assertEqual(self.check("1-4", code), [])

    def test_in_and_is_wait_for_their_levels(self):
        """`in` comes in 3-1 and `is` in 3-4, even though Compare is allowed earlier."""
        self.assertTrue(mentions(self.check("2-5", "print(1 in x)"), "Compare:In"))
        self.assertEqual(self.check("3-1", "x = [1]\nprint(1 in x)"), [])
        self.assertTrue(mentions(self.check("3-3", "print(x is y)"), "Compare:Is"))

    def test_main_guard_waits_for_5_1(self):
        """The main guard is not allowed before the level that teaches it."""
        code = 'if __name__ == "__main__":\n    print("hi")'
        self.assertTrue(mentions(self.check("4-5", code), "pattern:main_guard"))
        self.assertEqual(self.check("5-1", code), [])

    def test_builtin_method_waits_for_its_level(self):
        """append() comes in 3-1."""
        self.assertTrue(mentions(self.check("2-5", "x = 1\nx.append(1)"), "method:append"))

    def test_import_of_unlisted_module_is_reported(self):
        """random is in no level."""
        self.assertTrue(mentions(self.check("8-5", "import random"), "import:random"))

    def test_a_bare_node_allows_all_its_sub_forms(self):
        """If a level lists Compare itself, every comparison is allowed."""
        items = [make_item("1-1", 1, 1, constructs=["Compare", "Name", "Constant:int"])]
        curriculum = make_curriculum(items)
        problems = check_code(curriculum, "1-1", "a in b\na is b\na < 1", "x")
        self.assertEqual(problems, [])

    def test_code_that_does_not_parse_is_not_this_checks_business(self):
        """A syntax error gives no rule 1 problem; the limits check reports it."""
        self.assertEqual(self.check("1-1", "print("), [])

    def test_each_construct_is_reported_once(self):
        """Three uses of round() give one line."""
        problems = self.check("1-1", "round(1)\nround(2)\nround(3)")
        count = 0
        for problem in problems:
            if "call:round" in problem:
                count = count + 1
        self.assertEqual(count, 1)


class TestRuleOneOnLevels(unittest.TestCase):
    """Which fields of a level are checked."""

    @classmethod
    def setUpClass(cls):
        """Load the real curriculum once."""
        cls.curriculum = load_curriculum()

    def test_real_level_1_1_is_clean(self):
        """The existing Level 1-1 passes rule 1 in every field."""
        level = load_level(LEVEL_1_1)
        self.assertEqual(check_level_code(self.curriculum, level), [])

    def test_small_valid_level_is_clean(self):
        """The helper level is clean."""
        self.assertEqual(check_level_code(self.curriculum, make_level()), [])

    def test_reference_with_a_later_construct_is_reported_with_its_place(self):
        """The message names the wave and the field."""
        level = make_level(reference="print(round(1))")
        problems = check_level_code(self.curriculum, level)
        self.assertTrue(mentions(problems, "wave 2 (build) reference"))
        self.assertTrue(mentions(problems, "call:round"))

    def test_wrong_solution_is_checked_when_it_parses(self):
        """A wrong solution that parses must follow the rule too."""
        level = make_level(wrong="print(round(1))")
        self.assertTrue(mentions(check_level_code(self.curriculum, level), "wrong"))

    def test_wrong_solution_that_does_not_parse_is_skipped(self):
        """print(a b) is not Python, so it is not checked."""
        level = make_level(wrong="print(a b)")
        self.assertEqual(check_level_code(self.curriculum, level), [])

    def test_predict_answer_and_wrong_are_output_text(self):
        """The output a player types is never checked, even if it looks like code."""
        level = make_level()
        level.waves[2].answer = "round(1) global x"
        level.waves[2].wrong = "while True:"
        self.assertEqual(check_level_code(self.curriculum, level), [])

    def test_predict_code_is_checked(self):
        """The code a player must predict follows the rule."""
        level = make_level()
        level.waves[2].code = "print(round(1))"
        self.assertTrue(mentions(check_level_code(self.curriculum, level), "wave 3 (debug) code"))

    def test_cutscene_is_checked(self):
        """The cutscene follows the rule."""
        level = make_level()
        level.cutscene = "# >> Hi.\nx = 1"
        self.assertTrue(mentions(check_level_code(self.curriculum, level), "cutscene"))

    def test_starter_is_checked_when_it_parses_and_blanks_are_ignored(self):
        """A starter is checked, with ___ treated as a free name."""
        level = make_level()
        level.waves[0].starter = "print(round(___))"
        self.assertTrue(mentions(check_level_code(self.curriculum, level), "starter"))

    def test_level_not_in_the_curriculum_is_one_problem(self):
        """An unknown id cannot be checked."""
        level = make_level()
        level.id = "9-9"
        problems = check_level_code(self.curriculum, level)
        self.assertEqual(len(problems), 1)
        self.assertIn("9-9", problems[0])


class TestLevelMatchesCurriculum(unittest.TestCase):
    """The level.toml agrees with concepts.toml."""

    @classmethod
    def setUpClass(cls):
        """Load the real curriculum once."""
        cls.curriculum = load_curriculum()

    def test_real_level_1_1_matches(self):
        """Title, world, concepts and power-up are the same."""
        level = load_level(LEVEL_1_1)
        self.assertEqual(check_level_matches(self.curriculum, level), [])

    def test_differences_are_reported(self):
        """Each difference is one line."""
        level = make_level()
        level.title = "Other"
        level.world = 2
        level.power_up = "other"
        level.new_concepts = ["a", "b"]
        problems = check_level_matches(self.curriculum, level)
        self.assertEqual(len(problems), 4)

    def test_boss_flag_must_match(self):
        """A level file may not turn a level into a boss."""
        level = make_level()
        level.boss = True
        self.assertTrue(mentions(check_level_matches(self.curriculum, level), "boss"))

    def test_unknown_id(self):
        """A level that concepts.toml does not know."""
        level = make_level()
        level.id = "9-9"
        self.assertTrue(mentions(check_level_matches(self.curriculum, level), "concepts.toml"))


if __name__ == "__main__":
    unittest.main()
