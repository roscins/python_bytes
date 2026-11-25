"""Tests for the unkillable save: atomic writes, save version 3 and AutoSaver.

A save must survive the process being killed at any moment, so these tests
break the write halfway and check that the old save is still whole.
"""

import json
import os
import unittest

from engine.autosave import AutoSaver
from engine.game_state import GameState
from engine.save_file import (
    SAVE_VERSION,
    SaveError,
    load_progress,
    save_progress,
    write_atomically,
)
from tests.helpers import make_full_level, make_levels, make_temporary_folder


class TestWriteAtomically(unittest.TestCase):
    """The text goes to a temporary file first, and replaces the old file in one step."""

    def setUp(self):
        """A folder to write in."""
        self.folder = make_temporary_folder(self)
        self.path = self.folder / "save.json"

    def test_writes_the_text(self):
        """The file holds exactly the text."""
        write_atomically(self.path, "hello")
        self.assertEqual(self.path.read_text(encoding="utf-8"), "hello")

    def test_a_crash_before_the_replace_keeps_the_old_save(self):
        """If the replace never happens, the old file is whole and no temp file is left."""
        write_atomically(self.path, "old")

        def crash(source, target):
            raise OSError("power cut")

        with self.assertRaises(OSError):
            write_atomically(self.path, "new", replace=crash)
        self.assertEqual(self.path.read_text(encoding="utf-8"), "old")
        self.assertEqual(os.listdir(self.folder), ["save.json"])

    def test_the_data_is_forced_to_disk_before_the_replace(self):
        """fsync is called on the temporary file before os.replace."""
        events = []
        write_atomically(self.path, "x",
                         replace=lambda a, b: (events.append("replace"), os.replace(a, b)),
                         fsync=lambda fd: events.append("fsync"))
        self.assertLess(events.index("fsync"), events.index("replace"))

    def test_temporary_name_has_the_process_id(self):
        """Two running games never share a temporary file."""
        names = []
        write_atomically(self.path, "x", replace=lambda a, b: (names.append(a.name), os.replace(a, b)))
        self.assertIn(str(os.getpid()), names[0])

    def test_a_locked_target_is_retried(self):
        """On Windows another program can lock the file for a moment (PermissionError)."""
        calls = []

        def flaky(source, target):
            calls.append(1)
            if len(calls) < 3:
                raise PermissionError("locked")
            os.replace(source, target)

        write_atomically(self.path, "x", replace=flaky, sleep=lambda seconds: None)
        self.assertEqual(len(calls), 3)
        self.assertEqual(self.path.read_text(encoding="utf-8"), "x")

    def test_a_target_that_stays_locked_gives_up(self):
        """After a few tries the error is raised and the temp file is cleaned up."""
        def locked(source, target):
            raise PermissionError("locked")

        with self.assertRaises(PermissionError):
            write_atomically(self.path, "x", replace=locked, sleep=lambda seconds: None)
        self.assertEqual(os.listdir(self.folder), [])


class TestSaveVersionThree(unittest.TestCase):
    """The save remembers where the player is and the code they typed."""

    def setUp(self):
        """A one-level game with the three-wave Level 1-1, and a save path."""
        self.level = make_full_level()
        self.save_path = make_temporary_folder(self) / "save.json"

    def new_state(self):
        """Return a fresh game with the same level."""
        return GameState([make_full_level()])

    def test_version_is_three(self):
        """Saves are written as version 3."""
        self.assertEqual(SAVE_VERSION, 3)

    def test_wave_mode_and_buffers_round_trip(self):
        """Level, wave, code mode and the typed lines come back exactly."""
        state = GameState([self.level])
        state.current_level = "1-1"
        state.current_wave = 2
        state.coding = True
        state.set_wave_text(self.level, 2, 'print("SYSTEM CHECK")\nprint("VOICE')
        save_progress(state, self.save_path)

        loaded = self.new_state()
        self.assertTrue(load_progress(loaded, self.save_path))
        self.assertEqual(loaded.current_level, "1-1")
        self.assertEqual(loaded.current_wave, 2)
        self.assertTrue(loaded.coding)
        self.assertEqual(loaded.wave_text(loaded.levels[0], 2), 'print("SYSTEM CHECK")\nprint("VOICE')

    def test_version_two_saves_still_load_and_are_not_coding(self):
        """An older save has no buffers: the player is simply not in a wave."""
        data = {"version": 2, "current_level": "1-1", "cleared": [], "xp": 0, "coins": 10,
                "combo": 0, "levels": {}}
        self.save_path.write_text(json.dumps(data), encoding="utf-8")
        state = self.new_state()
        self.assertTrue(load_progress(state, self.save_path))
        self.assertFalse(state.coding)
        self.assertEqual(state.current_wave, 1)

    def test_buffers_of_removed_levels_are_dropped(self):
        """A level that is no longer in the game cannot break the save."""
        state = GameState([self.level])
        state.set_wave_text(self.level, 1, "print(1)")
        save_progress(state, self.save_path)
        data = json.loads(self.save_path.read_text(encoding="utf-8"))
        data["buffers"]["9-9"] = {"1": "print(2)"}
        self.save_path.write_text(json.dumps(data), encoding="utf-8")
        loaded = self.new_state()
        load_progress(loaded, self.save_path)
        self.assertNotIn("9-9", loaded.buffers)

    def test_out_of_range_wave_is_put_back_to_one(self):
        """A save that names wave 9 of a three-wave level lands on wave 1."""
        state = GameState([self.level])
        state.current_level = "1-1"
        save_progress(state, self.save_path)
        data = json.loads(self.save_path.read_text(encoding="utf-8"))
        data["current_wave"] = 9
        self.save_path.write_text(json.dumps(data), encoding="utf-8")
        loaded = self.new_state()
        load_progress(loaded, self.save_path)
        self.assertEqual(loaded.current_wave, 1)

    def test_broken_buffers_are_an_error(self):
        """Buffers must be text."""
        state = GameState([self.level])
        save_progress(state, self.save_path)
        data = json.loads(self.save_path.read_text(encoding="utf-8"))
        data["buffers"] = {"1-1": {"1": 42}}
        self.save_path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(SaveError):
            load_progress(self.new_state(), self.save_path)

    def test_coding_without_a_level_is_not_coding(self):
        """If the saved level is gone, the player is back at the map."""
        state = GameState([self.level])
        state.current_level = "1-1"
        state.coding = True
        save_progress(state, self.save_path)
        loaded = GameState(make_levels("2-1"))
        load_progress(loaded, self.save_path)
        self.assertFalse(loaded.coding)


class TestAutoSaver(unittest.TestCase):
    """AutoSaver saves the game state and never raises."""

    def test_save_writes_the_file(self):
        """After save() there is a readable save."""
        path = make_temporary_folder(self) / "save.json"
        saver = AutoSaver(GameState(make_levels("1-1")), path)
        self.assertTrue(saver.save())
        self.assertTrue(path.exists())

    def test_a_failed_save_returns_false_and_keeps_the_error(self):
        """The game goes on; the loop can tell the player."""
        folder = make_temporary_folder(self)
        blocker = folder / "file"
        blocker.write_text("x", encoding="utf-8")
        saver = AutoSaver(GameState(make_levels("1-1")), blocker / "save.json")
        self.assertFalse(saver.save())
        self.assertIsNotNone(saver.last_error)

    def test_counts_saves(self):
        """Tests can see how often the game saved."""
        path = make_temporary_folder(self) / "save.json"
        saver = AutoSaver(GameState(make_levels("1-1")), path)
        saver.save()
        saver.save()
        self.assertEqual(saver.save_count, 2)


if __name__ == "__main__":
    unittest.main()
