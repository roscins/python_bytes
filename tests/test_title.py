"""Tests for engine/title.py: the first screen, CONTINUE / NEW GAME / QUIT."""

import json
import unittest

from engine.save_file import save_progress
from engine.game_state import GameState
from engine.title import (
    CONTINUE,
    NEW,
    QUIT,
    ask_title,
    inspect_save,
    keep_old_save,
    title_text,
)
from tests.helpers import make_full_level, make_temporary_folder


class Typist:
    """Pretends to be the keyboard: gives out the typed lines, then end of input."""

    def __init__(self, *lines):
        """Remember the lines and the prompts the game showed."""
        self.lines = list(lines)
        self.prompts = []

    def __call__(self, prompt):
        """Return the next typed line, or raise EOFError when there are none."""
        self.prompts.append(prompt)
        if not self.lines:
            raise EOFError
        return self.lines.pop(0)


def info_for(test, make_save=False, damaged=False):
    """Return (SaveInfo, save path) for a game with or without a save."""
    path = make_temporary_folder(test) / "save.json"
    levels = [make_full_level()]
    if make_save:
        state = GameState(levels)
        state.current_level = "1-1"
        state.current_wave = 2
        state.coding = True
        save_progress(state, path)
    if damaged:
        path.write_text("{not json", encoding="utf-8")
    return inspect_save(path, levels, None), path


class TestInspectSave(unittest.TestCase):
    """What the title screen knows about the save."""

    def test_no_save(self):
        """A new player."""
        info, _ = info_for(self)
        self.assertEqual(info.status, "none")

    def test_good_save_says_where_the_player_is(self):
        """Level and wave."""
        info, _ = info_for(self, make_save=True)
        self.assertEqual(info.status, "ok")
        self.assertEqual((info.level_id, info.wave), ("1-1", 2))

    def test_damaged_save(self):
        """A save that is not JSON."""
        info, _ = info_for(self, damaged=True)
        self.assertEqual(info.status, "damaged")
        self.assertTrue(info.message)


class TestTitleText(unittest.TestCase):
    """What the title screen shows."""

    def test_new_player_has_no_continue(self):
        """Only NEW GAME and QUIT."""
        info, _ = info_for(self)
        text = title_text(info, plain=True)
        self.assertIn("PYTHON BYTES", text)
        self.assertNotIn("CONTINUE", text)
        self.assertIn("1  NEW GAME", text)
        self.assertIn("2  QUIT", text)

    def test_returning_player_sees_where_continue_goes(self):
        """CONTINUE says the level and wave."""
        info, _ = info_for(self, make_save=True)
        text = title_text(info, plain=True)
        self.assertIn("1  CONTINUE (level 1-1, wave 2)", text)
        self.assertIn("2  NEW GAME", text)
        self.assertIn("3  QUIT", text)

    def test_no_help_text_first(self):
        """The title does not explain commands."""
        info, _ = info_for(self, make_save=True)
        self.assertNotIn("help", title_text(info, plain=True).lower())

    def test_damaged_save_is_explained_in_one_line(self):
        """The player is told, and CONTINUE is not offered."""
        info, _ = info_for(self, damaged=True)
        text = title_text(info, plain=True)
        self.assertIn("damaged", text)
        self.assertNotIn("CONTINUE", text)


class TestAskTitle(unittest.TestCase):
    """Choosing from the menu."""

    def choose(self, info, *typed):
        """Run the menu with the typed lines; return (choice, typist, written lines)."""
        typist = Typist(*typed)
        written = []
        choice = ask_title(info, typist, written.append, plain=True)
        return choice, typist, written

    def test_enter_picks_continue_when_there_is_a_save(self):
        """The default is the first option."""
        info, _ = info_for(self, make_save=True)
        self.assertEqual(self.choose(info, "")[0], CONTINUE)

    def test_enter_picks_new_game_without_a_save(self):
        """The default is the first option."""
        info, _ = info_for(self)
        self.assertEqual(self.choose(info, "")[0], NEW)

    def test_numbers_and_letters(self):
        """1/2/3 and c/n/q."""
        info, _ = info_for(self, make_save=True)
        self.assertEqual(self.choose(info, "1")[0], CONTINUE)
        self.assertEqual(self.choose(info, "c")[0], CONTINUE)
        self.assertEqual(self.choose(info, "3")[0], QUIT)
        self.assertEqual(self.choose(info, "Q")[0], QUIT)
        self.assertEqual(self.choose(info, "n", "yes")[0], NEW)

    def test_new_game_over_a_save_needs_yes(self):
        """Anything but yes goes back to the menu; the answer after that decides."""
        info, _ = info_for(self, make_save=True)
        choice, typist, written = self.choose(info, "2", "no", "1")
        self.assertEqual(choice, CONTINUE)
        self.assertTrue(any(".old" in line for line in written))

    def test_new_game_without_a_save_needs_no_confirmation(self):
        """Nothing to lose."""
        info, _ = info_for(self)
        choice, typist, _ = self.choose(info, "1")
        self.assertEqual(choice, NEW)
        self.assertEqual(len(typist.prompts), 1)

    def test_nonsense_asks_again(self):
        """A wrong answer gets one short line, then the menu is asked again."""
        info, _ = info_for(self)
        choice, _, written = self.choose(info, "banana", "2")
        self.assertEqual(choice, QUIT)
        self.assertTrue(any("Type" in line for line in written))

    def test_end_of_input_quits(self):
        """Ctrl-D at the title leaves the game."""
        info, _ = info_for(self)
        self.assertEqual(self.choose(info)[0], QUIT)

    def test_continue_is_not_offered_for_a_damaged_save(self):
        """c does nothing there."""
        info, _ = info_for(self, damaged=True)
        choice, _, written = self.choose(info, "c", "1")
        self.assertEqual(choice, NEW)


class TestKeepOldSave(unittest.TestCase):
    """NEW GAME never deletes a save."""

    def test_the_old_save_is_kept_as_old(self):
        """It is moved, not removed."""
        info, path = info_for(self, make_save=True)
        before = path.read_text(encoding="utf-8")
        keep_old_save(path)
        self.assertFalse(path.exists())
        self.assertEqual(path.with_name("save.json.old").read_text(encoding="utf-8"), before)

    def test_an_older_old_save_is_replaced(self):
        """One generation only."""
        info, path = info_for(self, make_save=True)
        old = path.with_name("save.json.old")
        old.write_text("older", encoding="utf-8")
        keep_old_save(path)
        self.assertEqual(json.loads(old.read_text(encoding="utf-8"))["version"], 3)


if __name__ == "__main__":
    unittest.main()
