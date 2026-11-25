"""Tests for engine/commands.py and engine/game_state.py."""

import unittest

from engine.commands import COMMANDS, handle_line, parse_command
from engine.game_state import GameState
from tests.helpers import make_levels, make_temporary_folder, type_code


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

    def test_current_world_follows_the_current_level(self):
        """The current world is the first level's world until a level is played."""
        levels = make_levels("1-1", "2-1")
        levels[1].world = 2
        state = GameState(levels)
        self.assertEqual(state.current_world(), 1)
        state.current_level = "2-1"
        self.assertEqual(state.current_world(), 2)
        self.assertIsNone(GameState().current_world())

    def test_levels_in_world(self):
        """levels_in_world keeps only that world's levels, in order."""
        levels = make_levels("1-1", "2-1", "1-2")
        levels[1].world = 2
        state = GameState(levels)
        ids = []
        for level in state.levels_in_world(1):
            ids.append(level.id)
        self.assertEqual(ids, ["1-1", "1-2"])

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
        self.assertIn("WORLD 1 · BOOT SECTOR", text)
        self.assertIn("[1-1]", text)
        self.assertIn("[1-2]", text)
        self.assertIn("Type play <level> to start, for example: play 1-1", text)

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
        self.assertIn("You are at [1-2] Level 1-2.", text)


class TestPlay(unittest.TestCase):
    """Check the play command."""

    def test_play_known_level_sets_current_level(self):
        """Playing a level that exists makes it the current level."""
        state = GameState(make_levels("1-1"))
        text = handle_line(state, "play 1-1")
        self.assertEqual(state.current_level, "1-1")
        self.assertTrue(text.startswith("LEVEL 1-1 · LEVEL 1-1"))

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


class TestSlithering(unittest.TestCase):
    """Check when play makes Snek slither across the map."""

    def test_first_play_shows_only_the_intro(self):
        """With no level before, there is nowhere to slither from."""
        state = GameState(make_levels("1-1", "1-2"))
        state.cleared = ["1-1"]
        answer = handle_line(state, "play 1-2")
        self.assertIsInstance(answer, str)
        self.assertIn("LEVEL 1-2", answer)

    def test_play_from_another_level_slithers(self):
        """From 1-1 to 1-2, the answer is frames ending with the intro."""
        state = GameState(make_levels("1-1", "1-2"))
        state.current_level = "1-1"
        state.cleared = ["1-1"]
        answer = handle_line(state, "play 1-2")
        self.assertIsInstance(answer, list)
        self.assertGreater(len(answer), 1)
        self.assertIn("WORLD 1", answer[0])
        self.assertIn("LEVEL 1-2 · LEVEL 1-2", answer[-1])
        self.assertNotIn("LEVEL 1-2 · LEVEL 1-2", answer[0])
        self.assertEqual(state.current_level, "1-2")

    def test_play_same_level_again_does_not_slither(self):
        """Playing the level Snek is already at shows only the intro."""
        state = GameState(make_levels("1-1", "1-2"))
        state.current_level = "1-1"
        self.assertIsInstance(handle_line(state, "play 1-1"), str)

    def test_play_in_another_world_does_not_slither(self):
        """Snek only slithers within one world's map."""
        levels = make_levels("1-1", "2-1")
        levels[1].world = 2
        state = GameState(levels)
        state.current_level = "1-1"
        self.assertIsInstance(handle_line(state, "play 2-1"), str)


def final_text(answer):
    """Return the text of an answer: the last frame of an animation, or the text itself."""
    if isinstance(answer, list):
        return answer[-1]
    return answer


class TestSubmit(unittest.TestCase):
    """Check the submit command."""

    def test_submit_before_play_asks_to_play_first(self):
        """Submitting without a level tells the player to start one."""
        text = handle_line(GameState(), "submit")
        self.assertIn("play", text)

    def test_submit_with_no_code_asks_for_code(self):
        """An empty wave is not graded."""
        state = GameState(make_levels("1-1"))
        handle_line(state, "play 1-1")
        self.assertIn("Your code is empty", handle_line(state, ":submit"))

    def test_submit_grades_the_code_typed_in_the_game(self):
        """After play, :submit grades the lines the player typed for the current wave."""
        levels = make_levels("1-1")
        levels[0].waves[0].tests = [{"expected_stdout": "OK\n"}]
        state = GameState(levels)
        handle_line(state, "play 1-1")
        type_code(state, 'print("OK")')
        text = final_text(handle_line(state, ":submit"))
        self.assertIn("LEVEL 1-1 · RESULTS", text)
        self.assertIn("WAVE 1 · BUILD  1/1 test passed", text)


class TestWorkspaceCommands(unittest.TestCase):
    """Check that play writes no files, and where saves the code of the wave to a file."""

    def test_play_writes_no_files(self):
        """The code lives in the game, so play makes no workspace folder."""
        root = make_temporary_folder(self)
        state = GameState(make_levels("1-1"), workspace_root=root)
        text = handle_line(state, "play 1-1")
        self.assertFalse((root / "1-1").exists())
        self.assertNotIn("Your files are in", text)
        self.assertTrue(state.coding)

    def test_where_saves_the_code_and_shows_the_path(self):
        """where writes the current wave's code to a file and prints its path."""
        root = make_temporary_folder(self)
        state = GameState(make_levels("1-1"), workspace_root=root)
        handle_line(state, "play 1-1")
        type_code(state, 'print("OK")')
        text = handle_line(state, ":where")
        path = (root / "1-1" / "wave1.py").resolve()
        self.assertIn(str(path), text)
        self.assertEqual(path.read_text(encoding="utf-8"), 'print("OK")\n')

    def test_where_before_play(self):
        """where without a level asks the player to start one."""
        self.assertIn("play <level>", handle_line(GameState(), "where"))

    def test_where_without_workspace(self):
        """where with no workspace folder says so."""
        state = GameState(make_levels("1-1"))
        handle_line(state, "play 1-1")
        self.assertEqual(handle_line(state, ":where"), "There is no workspace folder.")


class TestLocks(unittest.TestCase):
    """Check the 70 % unlock rule in play and map."""

    def test_locked_level_cannot_be_played(self):
        """1-2 is locked until 1-1 is cleared."""
        state = GameState(make_levels("1-1", "1-2"))
        text = handle_line(state, "play 1-2")
        self.assertEqual(text, "Level 1-2 is locked. Pass every wave of 1-1 first.")
        self.assertIsNone(state.current_level)

    def test_map_shows_the_hud_and_stars(self):
        """The map header has stars and coins (no XP); open levels show their stars."""
        levels = make_levels("1-1", "1-2")
        state = GameState(levels)
        state.xp = 1240
        state.progress_for(levels[0]).stars = 2
        text = handle_line(state, "map")
        self.assertIn("★ 2/6   COINS 10", text)
        self.assertNotIn("XP", text)
        self.assertIn("★★☆", text)


class TestScoredSubmit(unittest.TestCase):
    """Check that submit scores the level and unlocks the next one."""

    def setUp(self):
        """Two one-wave levels, and level 1-1 started."""
        levels = make_levels("1-1", "1-2")
        for level in levels:
            level.waves[0].tests = [{"expected_stdout": "OK\n"}]
        self.state = GameState(levels)
        handle_line(self.state, "play 1-1")

    def test_full_marks_clear_the_level(self):
        """A perfect build wave gives 100 %, 3 stars, XP, coins and opens 1-2."""
        type_code(self.state, '# Say OK\nprint("OK")\n')
        answer = handle_line(self.state, ":submit")
        self.assertIsInstance(answer, list)
        self.assertIn("LEVEL 1-1 CLEARED · LEVEL 1-1", answer[0])
        text = answer[-1]
        self.assertIn("LEVEL SCORE 100 %  ★★★", text)
        self.assertIn("+10 coins · combo 1", text)
        self.assertNotIn("XP", text)
        self.assertIn("LEVEL 1-1 CLEARED. Level 1-2 is open.", text)
        self.assertEqual(self.state.cleared, ["1-1"])
        self.assertFalse(self.state.coding)
        self.assertIsInstance(handle_line(self.state, "play 1-2"), list)

    def test_low_score_does_not_clear(self):
        """Failing the only test leaves the level locked behind, with no clear screen."""
        type_code(self.state, 'print("NO")\n')
        text = handle_line(self.state, ":submit")
        self.assertIsInstance(text, str)
        self.assertIn("Pass every wave to clear this level.", text)
        self.assertEqual(self.state.cleared, [])
        self.assertTrue(self.state.coding)

    def test_perfect_waves_are_not_graded_again(self):
        """After full marks, submit says the wave already passed and gives no XP."""
        type_code(self.state, '# Say OK\nprint("OK")\n')
        handle_line(self.state, ":submit")
        handle_line(self.state, "play 1-1")
        type_code(self.state, "broken(")
        text = handle_line(self.state, ":submit")
        self.assertIn("already passed", text)
        self.assertEqual(self.state.cleared, ["1-1"])


class TestHint(unittest.TestCase):
    """Check the hint command."""

    def setUp(self):
        """A level whose one wave has three hints, being played."""
        levels = make_levels("1-1")
        levels[0].waves[0].hints = ["Nudge.", "Outline.", "Partial."]
        self.state = GameState(levels)
        self.state.current_level = "1-1"

    def test_buying_hints_in_order(self):
        """Each hint costs coins; bought hints are shown again for free."""
        self.state.coins = 50
        first = handle_line(self.state, "hint 1")
        self.assertIn("WAVE 1 · HINT 1 of 3 (nudge)\n  Nudge.", first)
        self.assertIn("You paid 5 coins and have 45 left", first)
        self.assertIn("Type hint 1 again for the outline (15 coins)", first)
        second = handle_line(self.state, "hint 1")
        self.assertIn("Nudge.", second)
        self.assertIn("Outline.", second)
        self.assertEqual(self.state.coins, 30)
        handle_line(self.state, "hint 1")
        last = handle_line(self.state, "hint 1")
        self.assertIn("That was the last hint", last)
        self.assertEqual(self.state.coins, 0)

    def test_not_enough_coins(self):
        """Without enough coins, nothing is bought and the price is shown."""
        self.state.coins = 3
        text = handle_line(self.state, "hint 1")
        self.assertIn("costs 5 coins, and you have 3", text)
        self.assertEqual(self.state.progress_for(self.state.levels[0]).hints_bought, [0])

    def test_wave_without_hints(self):
        """A wave with no hints says so."""
        self.state.levels[0].waves[0].hints = []
        self.assertEqual(handle_line(self.state, "hint 1"), "Wave 1 has no hints.")

    def test_bad_wave_numbers(self):
        """hint needs one wave number that the level has."""
        self.assertIn("Usage", handle_line(self.state, "hint two"))
        self.assertIn("Usage", handle_line(self.state, "hint 1 2"))
        self.assertEqual(handle_line(self.state, "hint 4"), "Level 1-1 has waves 1 to 1.")

    def test_hint_before_play(self):
        """hint without a level asks the player to start one."""
        self.assertIn("play <level>", handle_line(GameState(), "hint 1"))


class TestExtraWords(unittest.TestCase):
    """Check that commands without arguments reject words after them."""

    def test_each_command_without_arguments_rejects_extra_words(self):
        """help, map, submit, where and quit all explain that they take nothing."""
        for name in ["help", "map", "submit", "where", "quit"]:
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
