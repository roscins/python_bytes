"""Tests for engine/commands.py and engine/game_state.py."""

import unittest

from engine.commands import COMMANDS, handle_line, parse_command
from engine.game_state import DEFAULT_LEVELS, GameState


class TestGameState(unittest.TestCase):
    """Check what a new game starts with."""

    def test_new_game_uses_default_levels(self):
        """Without a level list, the game uses the World 1 levels."""
        state = GameState()
        self.assertEqual(state.levels, DEFAULT_LEVELS)

    def test_new_game_has_no_current_level_and_is_running(self):
        """A new game has not started a level and is running."""
        state = GameState()
        self.assertIsNone(state.current_level)
        self.assertTrue(state.running)

    def test_level_list_is_a_copy(self):
        """Changing the game's level list must not change the caller's list."""
        levels = ["1-1"]
        state = GameState(levels)
        state.levels.append("1-2")
        self.assertEqual(levels, ["1-1"])


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


class TestMap(unittest.TestCase):
    """Check the map command."""

    def test_map_lists_every_level(self):
        """Every level id appears on the map."""
        text = handle_line(GameState(["1-1", "1-2"]), "map")
        self.assertIn("[1-1]", text)
        self.assertIn("[1-2]", text)

    def test_map_marks_current_level(self):
        """The level being played is marked on the map."""
        state = GameState(["1-1", "1-2"])
        state.current_level = "1-2"
        text = handle_line(state, "map")
        self.assertIn("[1-2]  <- you are here", text)
        self.assertNotIn("[1-1]  <- you are here", text)


class TestPlay(unittest.TestCase):
    """Check the play command."""

    def test_play_known_level_sets_current_level(self):
        """Playing a level that exists makes it the current level."""
        state = GameState(["1-1"])
        text = handle_line(state, "play 1-1")
        self.assertEqual(state.current_level, "1-1")
        self.assertIn("1-1", text)

    def test_play_unknown_level_changes_nothing(self):
        """Playing a level that does not exist leaves the state alone."""
        state = GameState(["1-1"])
        text = handle_line(state, "play 9-9")
        self.assertIsNone(state.current_level)
        self.assertIn("no level 9-9", text)

    def test_play_without_level_shows_usage(self):
        """Typing play on its own explains how to use it."""
        state = GameState()
        text = handle_line(state, "play")
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
        state = GameState(["1-1"])
        state.current_level = "1-1"
        text = handle_line(state, "submit")
        self.assertIn("1-1", text)


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
