"""Tests for engine/commands.py and engine/game_state.py."""

import unittest

from engine.commands import COMMANDS, handle_line, parse_command
from engine.game_state import GameState
from tests.helpers import make_levels


class TestGameState(unittest.TestCase):
    """Check what a new game starts with."""

    def test_new_game_without_levels_has_none(self):
        """Without a level list, the game has no levels and nothing cleared."""
        state = GameState()
        self.assertEqual(state.levels, [])
        self.assertEqual(state.cleared, [])

    def test_new_game_has_no_current_level_and_is_running(self):
        """A new game has not started a level and is running."""
        state = GameState()
        self.assertIsNone(state.current_level)
        self.assertTrue(state.running)

    def test_level_list_is_a_copy(self):
        """Changing the game's level list must not change the caller's list."""
        levels = make_levels("1-1")
        state = GameState(levels)
        state.levels.append("anything")
        self.assertEqual(len(levels), 1)

    def test_find_level_by_id(self):
        """find_level returns the level with that id, or None."""
        state = GameState(make_levels("1-1", "1-2"))
        self.assertEqual(state.find_level("1-2").id, "1-2")
        self.assertIsNone(state.find_level("9-9"))


class TestParseCommand(unittest.TestCase):
    """Check how a typed line is split into a command and its arguments."""

    def test_command_with_argument(self):
        """The first word is the command, the rest are arguments."""
        self.assertEqual(parse_command("play 1-2"), ("play", ["1-2"]))

    def test_command_without_arguments(self):
        """A single word gives an empty argument list."""
        self.assertEqual(parse_command("help"), ("help", []))

    def test_command_name_is_lower_case(self):
        """Capital letters in the command name are ignored."""
        self.assertEqual(parse_command("HELP"), ("help", []))

    def test_extra_spaces_are_ignored(self):
        """Spaces around and between words do not matter."""
        self.assertEqual(parse_command("  play    1-1  "), ("play", ["1-1"]))

    def test_blank_line(self):
        """A blank line gives an empty name and no arguments."""
        self.assertEqual(parse_command("   "), ("", []))


class TestHelp(unittest.TestCase):
    """Check the help command."""

    def test_help_lists_every_command(self):
        """Every command in COMMANDS appears in the help text."""
        text = handle_line(GameState(), "help")
        for name in COMMANDS:
            self.assertIn(name, text)

    def test_help_shows_each_description(self):
        """Every command's description appears next to it in the help text."""
        text = handle_line(GameState(), "help")
        for name in COMMANDS:
            _, description = COMMANDS[name]
            self.assertIn(description, text)


class TestMap(unittest.TestCase):
    """Check the map command."""

    def test_map_lists_every_level(self):
        """Every level id appears on the map."""
        text = handle_line(GameState(make_levels("1-1", "1-2")), "map")
        self.assertIn("[1-1] Level 1-1", text)
        self.assertIn("[1-2] Level 1-2", text)

    def test_map_without_levels_says_so(self):
        """With no level packs, the map explains where they go."""
        text = handle_line(GameState(), "map")
        self.assertIn("No levels found", text)

    def test_map_without_current_level_marks_nothing(self):
        """Before any level is started, no level is marked."""
        text = handle_line(GameState(make_levels("1-1", "1-2")), "map")
        self.assertNotIn("you are here", text)

    def test_map_marks_current_level(self):
        """The level being played is marked on the map."""
        state = GameState(make_levels("1-1", "1-2"))
        state.current_level = "1-2"
        text = handle_line(state, "map")
        self.assertIn("[1-2] Level 1-2  <- you are here", text)
        self.assertNotIn("[1-1] Level 1-1  <- you are here", text)


class TestPlay(unittest.TestCase):
    """Check the play command."""

    def test_play_known_level_sets_current_level(self):
        """Playing a level that exists makes it the current level."""
        state = GameState(make_levels("1-1"))
        text = handle_line(state, "play 1-1")
        self.assertEqual(state.current_level, "1-1")
        self.assertEqual(text, "Starting level 1-1: Level 1-1.")

    def test_play_unknown_level_changes_nothing(self):
        """Playing a level that does not exist leaves the state alone."""
        state = GameState(make_levels("1-1"))
        text = handle_line(state, "play 9-9")
        self.assertIsNone(state.current_level)
        self.assertIn("no level 9-9", text)

    def test_play_without_level_shows_usage(self):
        """Typing play on its own explains how to use it."""
        state = GameState()
        text = handle_line(state, "play")
        self.assertIn("Usage", text)
        self.assertIsNone(state.current_level)

    def test_play_with_too_many_words_shows_usage(self):
        """Typing more than one level after play explains how to use it."""
        state = GameState(make_levels("1-1"))
        text = handle_line(state, "play 1-1 extra")
        self.assertIn("Usage", text)
        self.assertIsNone(state.current_level)


class TestSubmit(unittest.TestCase):
    """Check the submit placeholder."""

    def test_submit_before_play_asks_to_play_first(self):
        """Submitting without a level tells the player to start one."""
        text = handle_line(GameState(), "submit")
        self.assertIn("play", text)

    def test_submit_during_level_names_the_level(self):
        """Submitting during a level mentions that level."""
        state = GameState(make_levels("1-1"))
        state.current_level = "1-1"
        text = handle_line(state, "submit")
        self.assertIn("1-1", text)


class TestExtraWords(unittest.TestCase):
    """Check that commands without arguments reject words after them."""

    def test_each_command_without_arguments_rejects_extra_words(self):
        """help, map, submit and quit all explain that they take nothing."""
        for name in ["help", "map", "submit", "quit"]:
            text = handle_line(GameState(), f"{name} now")
            self.assertEqual(text, f"{name} does not take anything after it. Type just: {name}")

    def test_quit_with_extra_words_keeps_running(self):
        """"quit now" does not quit, so the player sees why."""
        state = GameState()
        handle_line(state, "quit now")
        self.assertTrue(state.running)


class TestQuitAndUnknown(unittest.TestCase):
    """Check quit, unknown commands and blank lines."""

    def test_quit_stops_the_game(self):
        """After quit the game is no longer running."""
        state = GameState()
        handle_line(state, "quit")
        self.assertFalse(state.running)

    def test_unknown_command_suggests_help(self):
        """An unknown command tells the player to type help."""
        state = GameState()
        text = handle_line(state, "dance")
        self.assertIn("Unknown command: dance", text)
        self.assertIn("help", text)
        self.assertTrue(state.running)

    def test_blank_line_returns_empty_text(self):
        """A blank line does nothing and shows nothing."""
        self.assertEqual(handle_line(GameState(), ""), "")


if __name__ == "__main__":
    unittest.main()
