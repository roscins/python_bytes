"""Tests for engine/save_file.py, using save files in temporary folders."""

import json
import unittest

from engine.game_state import GameState
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

    def test_save_writes_version_level_and_cleared(self):
        """The save file holds the version, the current level and cleared levels."""
        state = GameState(make_levels("1-1"))
        state.current_level = "1-1"
        save_progress(state, self.save_path)
        with open(self.save_path, encoding="utf-8") as save_file:
            data = json.load(save_file)
        self.assertEqual(data, {"version": SAVE_VERSION, "current_level": "1-1", "cleared": []})

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
        self.write_save({"version": SAVE_VERSION, "current_level": "9-9", "cleared": ["1-1", "9-8"]})
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
        self.check_broken('{"version": 99}', "expected version 1")

    def test_current_level_must_be_text_or_null(self):
        """current_level = 5 is rejected."""
        self.check_broken('{"version": 1, "current_level": 5}', "current_level")

    def test_cleared_must_be_a_list_of_ids(self):
        """cleared = "1-1" or cleared = [1] is rejected."""
        self.check_broken('{"version": 1, "cleared": "1-1"}', "cleared must be a list")
        self.check_broken('{"version": 1, "cleared": [1]}', "cleared must be a list")

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
