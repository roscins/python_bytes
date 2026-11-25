"""Tests for engine/save_file.py, using save files in temporary folders."""

import json
import unittest

from engine.game_state import GameState
from engine.scoring import STARTING_COINS
from engine.save_file import (
    SAVE_VERSION,
    SaveError,
    load_progress,
    save_progress,
    set_aside_broken_save,
)
from tests.helpers import make_levels, make_temporary_folder


class TestSaveAndLoad(unittest.TestCase):
    """Check that progress survives saving and loading."""

    def setUp(self):
        """Use a save path in a folder that does not exist yet."""
        self.save_path = make_temporary_folder(self) / "python-bytes" / "save.json"

    def write_save(self, data):
        """Write `data` as JSON to the save path."""
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        self.save_path.write_text(json.dumps(data), encoding="utf-8")

    def test_save_writes_every_part(self):
        """The save file holds the version, level, cleared levels, XP, coins, combo and progress."""
        state = GameState(make_levels("1-1"))
        state.current_level = "1-1"
        save_progress(state, self.save_path)
        with open(self.save_path, encoding="utf-8") as save_file:
            data = json.load(save_file)
        self.assertEqual(data, {"version": SAVE_VERSION, "current_level": "1-1", "current_wave": 1,
                                "coding": False, "cleared": [], "xp": 0, "coins": STARTING_COINS,
                                "combo": 0, "levels": {}, "buffers": {}})

    def test_scores_load_back(self):
        """XP, coins, combo and each level's progress survive a save and load."""
        levels = make_levels("1-1")
        state = GameState(levels)
        state.xp = 1240
        state.coins = 35
        state.combo = 4
        progress = state.progress_for(levels[0])
        progress.wave_best = [0.5]
        progress.hints_bought = [2]
        progress.best_score = 40
        save_progress(state, self.save_path)

        new_state = GameState(make_levels("1-1"))
        load_progress(new_state, self.save_path)
        self.assertEqual((new_state.xp, new_state.coins, new_state.combo), (1240, 35, 4))
        loaded = new_state.progress["1-1"]
        self.assertEqual(loaded.wave_best, [0.5])
        self.assertEqual(loaded.hints_bought, [2])
        self.assertEqual(loaded.best_score, 40)

    def test_version_1_save_still_loads(self):
        """A save from before scoring loads with no XP and the starting coins."""
        self.write_save({"version": 1, "current_level": "1-1", "cleared": ["1-1"]})
        state = GameState(make_levels("1-1"))
        self.assertTrue(load_progress(state, self.save_path))
        self.assertEqual(state.cleared, ["1-1"])
        self.assertEqual(state.xp, 0)
        self.assertEqual(state.coins, STARTING_COINS)
        self.assertEqual(state.progress, {})

    def test_progress_is_fitted_to_the_waves(self):
        """A level that now has more waves gets zeros for the new ones."""
        progress = {"wave_best": [1.0], "wave_attempts": [1], "hints_bought": [0],
                    "best_quality": 1.0, "quality_rewarded": True, "best_score": 100, "stars": 3}
        self.write_save({"version": 2, "current_level": None, "cleared": [], "xp": 0,
                         "coins": 0, "combo": 0, "levels": {"1-1": progress, "9-9": progress}})
        levels = make_levels("1-1")
        levels[0].waves = levels[0].waves * 2
        state = GameState(levels)
        load_progress(state, self.save_path)
        self.assertEqual(state.progress["1-1"].wave_best, [1.0, 0])
        self.assertNotIn("9-9", state.progress)

    def test_save_leaves_no_temporary_file(self):
        """Only save.json is left in the folder after saving."""
        save_progress(GameState(), self.save_path)
        names = []
        for path in self.save_path.parent.iterdir():
            names.append(path.name)
        self.assertEqual(names, ["save.json"])

    def test_saved_progress_loads_back(self):
        """What is saved is what is loaded."""
        state = GameState(make_levels("1-1", "1-2"))
        state.current_level = "1-2"
        state.cleared = ["1-1"]
        save_progress(state, self.save_path)

        new_state = GameState(make_levels("1-1", "1-2"))
        self.assertTrue(load_progress(new_state, self.save_path))
        self.assertEqual(new_state.current_level, "1-2")
        self.assertEqual(new_state.cleared, ["1-1"])

    def test_no_save_file_means_a_new_player(self):
        """Without a save file, load_progress returns False and changes nothing."""
        state = GameState(make_levels("1-1"))
        self.assertFalse(load_progress(state, self.save_path))
        self.assertIsNone(state.current_level)

    def test_removed_levels_are_dropped(self):
        """Level ids that are no longer in the game are not loaded."""
        self.write_save({"version": 1, "current_level": "9-9", "cleared": ["1-1", "9-8"]})
        state = GameState(make_levels("1-1"))
        load_progress(state, self.save_path)
        self.assertIsNone(state.current_level)
        self.assertEqual(state.cleared, ["1-1"])


class TestBrokenSaves(unittest.TestCase):
    """Check that broken save files are recognised and set aside."""

    def setUp(self):
        """Use a save path in an empty temporary folder."""
        self.save_path = make_temporary_folder(self) / "save.json"

    def check_broken(self, text, message):
        """Write `text` as the save and check that loading it says `message`."""
        self.save_path.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(SaveError, message):
            load_progress(GameState(), self.save_path)

    def test_not_json_is_an_error(self):
        """A save that is not JSON is rejected."""
        self.check_broken("{not json", "not valid JSON")

    def test_json_that_is_not_an_object_is_an_error(self):
        """A save must be a JSON object, not a list."""
        self.check_broken("[1, 2]", "JSON object")

    def test_wrong_version_is_an_error(self):
        """A save from another version of the game is rejected."""
        self.check_broken('{"version": 99}', "expected version 3")

    def test_current_level_must_be_text_or_null(self):
        """current_level = 5 is rejected."""
        self.check_broken('{"version": 1, "current_level": 5}', "current_level")

    def test_cleared_must_be_a_list_of_ids(self):
        """cleared = "1-1" or cleared = [1] is rejected."""
        self.check_broken('{"version": 1, "cleared": "1-1"}', "cleared must be a list")
        self.check_broken('{"version": 1, "cleared": [1]}', "cleared must be a list")

    def test_scores_must_be_whole_numbers(self):
        """xp = -5 or coins = "ten" is rejected."""
        base = '"version": 2, "cleared": [], "combo": 0, "levels": {}'
        self.check_broken('{' + base + ', "xp": -5, "coins": 0}', "xp must be a whole number")
        self.check_broken('{' + base + ', "xp": 0, "coins": "ten"}', "coins must be a whole number")

    def test_levels_must_be_an_object(self):
        """levels = [] is rejected."""
        text = '{"version": 2, "cleared": [], "xp": 0, "coins": 0, "combo": 0, "levels": []}'
        self.check_broken(text, "levels must be a JSON object")

    def test_broken_level_progress_is_an_error(self):
        """A level's progress with a missing part is rejected, naming the level."""
        self.save_path.write_text(json.dumps({
            "version": 2, "cleared": [], "xp": 0, "coins": 0, "combo": 0,
            "levels": {"1-1": {"wave_best": [1.0]}},
        }), encoding="utf-8")
        with self.assertRaisesRegex(SaveError, "level 1-1: wave_attempts must be a list"):
            load_progress(GameState(make_levels("1-1")), self.save_path)

    def test_save_error_is_a_value_error(self):
        """Code that catches ValueError also catches SaveError."""
        self.assertTrue(issubclass(SaveError, ValueError))

    def test_broken_save_is_renamed(self):
        """set_aside_broken_save keeps the file as save.json.broken."""
        self.save_path.write_text("broken", encoding="utf-8")
        broken_path = set_aside_broken_save(self.save_path)
        self.assertEqual(broken_path.name, "save.json.broken")
        self.assertEqual(broken_path.read_text(encoding="utf-8"), "broken")
        self.assertFalse(self.save_path.exists())


if __name__ == "__main__":
    unittest.main()
