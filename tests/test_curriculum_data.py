"""Check that levels/concepts.toml and docs/curriculum.md agree, and have the right shape.

The two files describe the same curriculum: the toml for the progression
checker, the markdown for people. If they differ, the checker enforces
one thing and the students read another. These tests also check the shape
of the data the checker will rely on. The six progression rules are
tested together with the checker itself.
"""

import tomllib
import unittest
from pathlib import Path

PROJECT_FOLDER = Path(__file__).parent.parent
CONCEPTS_FILE = PROJECT_FOLDER / "levels" / "concepts.toml"
CURRICULUM_FILE = PROJECT_FOLDER / "docs" / "curriculum.md"

WORLD_COUNT = 8
LEVELS_PER_WORLD = 5
MIN_CONCEPTS = 2
MAX_CONCEPTS = 4


def load_concepts():
    """Return the list of level tables from levels/concepts.toml."""
    with open(CONCEPTS_FILE, "rb") as file:
        return tomllib.load(file)


def label_for(level):
    """Return how curriculum.md names a level: "1-1" for a level, "Boss 1" for a boss."""
    if level.get("boss", False):
        number = level["id"].split("-")[1]
        return "Boss " + number
    return level["id"]


def read_table_rows():
    """Return the rows of every level table in curriculum.md, as a dict.

    The key is the first cell ("1-1" or "Boss 1"); the value is the list of
    all the cells in that row. Only rows whose first cell looks like a
    level or a boss are kept, so the outcome tables are skipped.
    """
    rows = {}
    text = CURRICULUM_FILE.read_text(encoding="utf-8")
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = []
        for cell in line.strip().strip("|").split("|"):
            cells.append(cell.strip())
        first = cells[0]
        looks_like_level = first[:1].isdigit() and "-" in first
        if looks_like_level or first.startswith("Boss "):
            rows[first] = cells
    return rows


class TestConceptsFile(unittest.TestCase):
    """Check the shape of levels/concepts.toml."""

    def setUp(self):
        """Load the file once for each test."""
        self.data = load_concepts()
        self.levels = self.data["level"]

    def test_meta_matches_the_curriculum(self):
        """The file says 5 levels per world and lists all 31 outcome codes."""
        self.assertEqual(self.data["meta"]["levels_per_world"], LEVELS_PER_WORLD)
        self.assertEqual(len(self.data["meta"]["outcome_codes"]), 31)

    def test_ids_are_unique(self):
        """No two items share an id."""
        ids = []
        for level in self.levels:
            ids.append(level["id"])
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_world_has_five_levels_then_a_boss(self):
        """Each of the 8 worlds is five levels, then its boss, in that order."""
        for world in range(1, WORLD_COUNT + 1):
            items = []
            for level in self.levels:
                if level["world"] == world:
                    items.append(level)
            expected_ids = []
            for number in range(1, LEVELS_PER_WORLD + 1):
                expected_ids.append(f"{world}-{number}")
            expected_ids.append(f"boss-{world}")
            ids = []
            for item in items:
                ids.append(item["id"])
            self.assertEqual(ids, expected_ids, f"world {world}")
            self.assertTrue(items[-1].get("boss", False))

    def test_worlds_come_in_order(self):
        """The file lists World 1 first and World 8 last."""
        worlds = []
        for level in self.levels:
            worlds.append(level["world"])
        self.assertEqual(worlds, sorted(worlds))

    def test_levels_have_two_to_four_concepts(self):
        """A level has 2-4 headline concepts; a boss has none."""
        for level in self.levels:
            if level.get("boss", False):
                self.assertNotIn("concepts", level, level["id"])
            else:
                count = len(level["concepts"])
                self.assertTrue(MIN_CONCEPTS <= count <= MAX_CONCEPTS,
                                f"{level['id']} has {count} concepts")

    def test_every_level_has_a_power_up_and_no_boss_does(self):
        """Levels earn a power-up; bosses do not; no two levels share one."""
        seen = []
        for level in self.levels:
            if level.get("boss", False):
                self.assertNotIn("power_up", level, level["id"])
            else:
                self.assertIn("power_up", level, level["id"])
                seen.append(level["power_up"])
        self.assertEqual(len(seen), len(set(seen)))

    def test_every_item_has_a_mission_and_outcomes(self):
        """Every item says what the player does and which outcomes it covers."""
        for level in self.levels:
            self.assertTrue(level["mission"].strip(), level["id"])
            self.assertTrue(level["outcomes"], level["id"])

    def test_outcomes_are_known_codes(self):
        """Every outcome named by an item is one of the listed codes."""
        codes = self.data["meta"]["outcome_codes"]
        for level in self.levels:
            for outcome in level["outcomes"]:
                self.assertIn(outcome, codes, level["id"])


class TestCurriculumTables(unittest.TestCase):
    """Check that the tables in docs/curriculum.md repeat concepts.toml."""

    def setUp(self):
        """Load the toml and the tables once for each test."""
        self.levels = load_concepts()["level"]
        self.rows = read_table_rows()

    def test_every_item_has_a_row_and_no_row_is_extra(self):
        """The tables list exactly the items in the toml."""
        labels = []
        for level in self.levels:
            labels.append(label_for(level))
        self.assertEqual(sorted(self.rows), sorted(labels))

    def test_rows_repeat_the_toml(self):
        """Title, concepts, difficulty, outcomes and power-up agree."""
        for level in self.levels:
            label = label_for(level)
            cells = self.rows[label]
            self.assertEqual(cells[1], level["title"], label)
            self.assertEqual(cells[3], str(level["difficulty"]), label)
            self.assertEqual(cells[4], ", ".join(level["outcomes"]), label)
            if level.get("boss", False):
                self.assertIn(level["mission"], cells[2], label)
                self.assertEqual(cells[5], "–", label)
            else:
                self.assertEqual(cells[2], "; ".join(level["concepts"]), label)
                self.assertEqual(cells[5], "`" + level["power_up"] + "`", label)


if __name__ == "__main__":
    unittest.main()
