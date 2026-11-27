"""Tests for engine/display.py: every answer of the game as a full screen.

The terminal is a fake: `write` collects what would be drawn, `sleep` records
the pauses, `skipped` is a switch. No real terminal and no real time.
"""

import re
import unittest

from engine.screens import split_screens
from engine.commands import handle_line
from engine.display import Display, split_sections
from engine.game_state import GameState
from engine.hud import hud_info
from engine.terminal import ENTER_FULLSCREEN, LEAVE_FULLSCREEN
from render.ansi import strip_ansi
from render.reactions import load_reaction_art, reaction_lines
from tests.helpers import make_full_level, type_code

ROW = re.compile(r"\x1b\[(\d+);1H")


class FakeTerminal:
    """What the display writes to, how big the window is, and the player's Enter key."""

    def __init__(self, columns=80, rows=24):
        """Start with an empty record."""
        self.columns = columns
        self.rows = rows
        self.written = []
        self.slept = []
        self.skip = False
        self.typed = []

    def write(self, text):
        """Collect what is written."""
        self.written.append(text)

    def size(self):
        """Return (columns, rows)."""
        return self.columns, self.rows

    def sleep(self, seconds):
        """Record a pause instead of waiting."""
        self.slept.append(seconds)

    def skipped(self):
        """Return the Enter switch."""
        return self.skip

    def read_line(self, prompt):
        """Pretend to read a line; Enter by default."""
        self.typed.append(prompt)
        return ""

    def text(self):
        """Return everything written, as one text."""
        return "".join(self.written)

    def last_frame_rows(self):
        """Return the rows of the last drawn frame as {row number: text without colours}."""
        text = ""
        for chunk in reversed(self.written):
            if ROW.search(chunk) and "\x1b[1;1H" in chunk:
                text = chunk
                break
        rows = {}
        parts = ROW.split(text)
        for index in range(1, len(parts) - 1, 2):
            rows[int(parts[index])] = strip_ansi(parts[index + 1])
        return rows


def make_display(**options):
    """Return (display, terminal, state): a game with Level 1-1, and a display on a fake terminal."""
    state = GameState([make_full_level()])
    terminal = FakeTerminal(options.pop("columns", 80), options.pop("rows", 24))
    display = Display(state, terminal.write, size=terminal.size, sleep=terminal.sleep,
                      skipped=terminal.skipped, read_line=terminal.read_line, **options)
    return display, terminal, state


class TestSections(unittest.TestCase):
    """Cutting a command's answer into titled panels."""

    def test_the_intro_of_a_level(self):
        """Story, tips and the wave."""
        state = GameState([make_full_level()])
        titles = []
        for screen in split_screens(handle_line(state, "play 1-1")):
            titles.extend(title for title, _ in split_sections(screen))
        self.assertEqual(titles, ["STORY", "TIPS", "CODE"])

    def test_results_followed_by_the_next_wave(self):
        """The results panel and the code panel."""
        state = GameState([make_full_level()])
        handle_line(state, "play 1-1")
        handle_line(state, ':edit 1 print("a")')
        answer = handle_line(state, ":submit")
        sections = split_sections(answer[-1] if isinstance(answer, list) else answer)
        titles = [title for title, _ in sections]
        self.assertEqual(titles[0], "RESULTS")
        self.assertEqual(titles[-1], "CODE")

    def test_the_lines_inside_the_results_do_not_start_new_panels(self):
        """WAVE 1 · FILL-IN ... and LEVEL SCORE belong to the results."""
        state = GameState([make_full_level()])
        handle_line(state, "play 1-1")
        type_code(state, 'print("b")')
        sections = split_sections(handle_line(state, ":submit"))
        self.assertEqual([title for title, _ in sections], ["RESULTS"])
        text = "\n".join(sections[0][1])
        self.assertIn("LEVEL SCORE", text)
        self.assertIn("Not yet.", text)

    def test_a_wave_screen_is_one_code_panel(self):
        """:show."""
        state = GameState([make_full_level()])
        handle_line(state, "play 1-1")
        sections = split_sections(handle_line(state, ":show"))
        self.assertEqual([title for title, _ in sections], ["CODE"])

    def test_any_other_text_is_a_note(self):
        """An error or a message."""
        self.assertEqual(split_sections("Unknown command: x.")[0][0], "SNEK")

    def test_blank_lines_inside_a_section_are_kept(self):
        """The code panel has blank lines in it."""
        sections = split_sections("WAVE 1 of 3 · BUILD\nbrief\n\nYOUR CODE:\n  1 | x\n\n:submit")
        self.assertEqual(len(sections), 1)
        self.assertIn("", sections[0][1])


class TestStartAndStop(unittest.TestCase):
    """Entering and leaving full screen."""

    def test_start_enters_and_stop_leaves(self):
        """The alternate screen."""
        display, terminal, _ = make_display()
        display.start()
        display.stop()
        self.assertEqual(terminal.written[0], ENTER_FULLSCREEN)
        self.assertEqual(terminal.written[-1], LEAVE_FULLSCREEN)

    def test_stop_without_start_does_nothing(self):
        """Safe to call always."""
        display, terminal, _ = make_display()
        display.stop()
        self.assertEqual(terminal.written, [])


class TestFrames(unittest.TestCase):
    """What a screen looks like."""

    def setUp(self):
        """A display, started."""
        self.display, self.terminal, self.state = make_display()
        self.display.start()

    def test_the_hud_is_on_the_first_two_rows_of_every_screen(self):
        """Whatever is shown."""
        for answer in ("Unknown command: x.", handle_line(self.state, "play 1-1"), handle_line(self.state, "map")):
            self.terminal.written.clear()
            self.display.show(answer)
            rows = self.terminal.last_frame_rows()
            self.assertIn("WORLD 1", rows[1])
            self.assertIn("COINS", rows[2])

    def test_every_row_is_80_wide_and_the_last_row_is_left_for_typing(self):
        """23 rows drawn in a 24-row window."""
        self.display.show("hello")
        rows = self.terminal.last_frame_rows()
        self.assertEqual(sorted(rows), list(range(1, 24)))
        for text in rows.values():
            self.assertEqual(len(text), 80)

    def test_a_panel_does_not_repeat_its_heading_inside(self):
        """The heading is the title, once."""
        self.display.show(handle_line(self.state, "play 1-1"))
        text = strip_ansi(self.terminal.text())
        self.assertNotIn("│ TIPS", text)
        self.assertNotIn("│ WAVE 1 of 3", text)

    def test_the_body_is_framed_in_a_titled_panel(self):
        """Box characters and a title."""
        self.display.show(handle_line(self.state, "play 1-1"))
        text = strip_ansi(self.terminal.text())
        self.assertIn("┌─ TIPS ", text)
        self.assertIn("┌─ WAVE 1 of 3 · FILL-IN ", text)
        self.assertIn("└", text)

    def test_the_map_is_drawn_as_it_is_not_in_a_panel(self):
        """Pixel art needs the full 80 cells."""
        self.terminal.written.clear()
        self.display.show(handle_line(self.state, "map"))
        rows = self.terminal.last_frame_rows()
        joined = "\n".join(rows.values())
        self.assertIn("[1-1]", joined)
        self.assertNotIn("┌─ SNEK", joined)

    def test_a_window_that_is_too_small_gets_a_polite_message(self):
        """Not a broken layout."""
        display, terminal, _ = make_display(columns=60, rows=20)
        display.start()
        display.show("hello")
        text = strip_ansi(terminal.text())
        self.assertIn("at least 80 x 24", text)

    def test_a_bigger_window_uses_more_rows(self):
        """The body grows, the frame has rows - 1 rows."""
        display, terminal, _ = make_display(rows=40)
        display.start()
        display.show("hello")
        self.assertEqual(len(terminal.last_frame_rows()), 39)

    def test_without_true_colour_the_codes_are_256_colour(self):
        """macOS Terminal."""
        display, terminal, state = make_display(truecolor=False)
        display.start()
        display.show(handle_line(state, "map"))
        self.assertNotIn(";2;", terminal.text())
        self.assertIn("38;5;", terminal.text())

    def test_with_true_colour_the_map_keeps_it(self):
        """Terminals that can."""
        self.display.show(handle_line(self.state, "map"))
        self.assertIn("38;2;", self.terminal.text())


class TestCodeScreen(unittest.TestCase):
    """While the player types, the screen follows."""

    def setUp(self):
        """A display on Level 1-1, in code mode."""
        self.display, self.terminal, self.state = make_display()
        self.display.start()
        self.display.show(handle_line(self.state, "play 1-1"))
        self.terminal.written.clear()

    def test_an_empty_answer_while_coding_redraws_the_code_with_the_new_line(self):
        """The line just typed is on the screen."""
        handle_line(self.state, ":clear")
        handle_line(self.state, 'print("typed line")')
        self.display.show("")
        text = "\n".join(self.terminal.last_frame_rows().values())
        self.assertIn('print("typed line")', text)

    def test_a_short_message_goes_to_the_status_line_and_the_code_stays(self):
        """:undo with nothing to undo."""
        self.display.show("There is nothing to undo.")
        rows = self.terminal.last_frame_rows()
        self.assertIn("There is nothing to undo.", rows[22])
        self.assertIn("YOUR CODE", "\n".join(rows.values()))

    def test_a_long_answer_replaces_the_code_view(self):
        """Help text is a panel of its own."""
        self.display.show(handle_line(self.state, ":help"))
        text = strip_ansi(self.terminal.text())
        self.assertIn("Commands", text)
        self.assertIn(":submit", text)


class TestResultsAndSnek(unittest.TestCase):
    """Snek reacts to what the player did."""

    def setUp(self):
        """A display on Level 1-1."""
        self.display, self.terminal, self.state = make_display()
        self.display.start()
        handle_line(self.state, "play 1-1")
        self.art = load_reaction_art()

    def submit(self, code):
        """Type `code` into wave 1 and submit it; return the answer."""
        type_code(self.state, code)
        return handle_line(self.state, ":submit")

    def shown_face(self, answer):
        """Show the answer; return the name of the Snek face drawn (all its 8 lines), or None."""
        self.terminal.written.clear()
        self.display.show(answer)
        text = self.terminal.text()
        for name in ("celebrate", "dizzy", "happy", "idle"):
            lines = reaction_lines(name, self.art)
            if all(line in text for line in lines):
                return name
        return None

    def test_a_passed_wave_makes_snek_happy(self):
        """Wave 1 passes."""
        self.assertEqual(self.shown_face(self.submit('print("a")')), "happy")

    def test_a_failed_wave_makes_snek_dizzy(self):
        """Wrong output."""
        self.assertEqual(self.shown_face(self.submit('print("b")')), "dizzy")

    def test_clearing_the_level_makes_snek_celebrate(self):
        """The last wave."""
        self.submit('print("a")')
        type_code(self.state, '# say a\nprint("a")')
        handle_line(self.state, ":wave 2")
        type_code(self.state, '# say a\nprint("a")')
        handle_line(self.state, ":submit")
        handle_line(self.state, ":wave 3")
        type_code(self.state, "a")
        answer = handle_line(self.state, ":submit")
        self.assertIsInstance(answer, list)
        self.assertEqual(self.shown_face(answer), "celebrate")

    def test_the_results_are_in_a_results_panel_next_to_snek(self):
        """Text on the left."""
        self.terminal.written.clear()
        self.display.show(self.submit('print("a")'))
        text = strip_ansi(self.terminal.text())
        self.assertIn("┌─ LEVEL 1-1 · RESULTS", text)
        self.assertIn("tests passed", text)


class TestAnimations(unittest.TestCase):
    """Typed cutscenes, level clear, the combo flash."""

    def test_the_story_types_itself_out_and_enter_skips_it(self):
        """Many frames, with pauses; with Enter pressed, fewer."""
        display, terminal, state = make_display()
        display.start()
        answer = handle_line(state, "play 1-1")
        terminal.written.clear()
        display.show(answer)
        slow = len(terminal.written)
        self.assertGreater(len(terminal.slept), 5)

        display2, terminal2, state2 = make_display()
        display2.start()
        answer2 = handle_line(state2, "play 1-1")
        terminal2.written.clear()
        terminal2.skip = True
        display2.show(answer2)
        self.assertLess(len(terminal2.written), slow)
        self.assertIn("Hi.", strip_ansi(terminal2.text()))

    def test_the_story_is_complete_in_the_last_frame(self):
        """Nothing is lost by the typing."""
        display, terminal, state = make_display()
        display.start()
        display.show(handle_line(state, "play 1-1"))
        text = strip_ansi(terminal.text())
        self.assertIn("LEVEL 1-1 · HELLO, TERMINAL", text)
        self.assertIn("Hi.", text)
        self.assertIn("3 waves", text)

    def test_no_typing_pause_without_animation(self):
        """delay 0 is the animation switched off."""
        display, terminal, state = make_display(delay=0, type_delay=0)
        display.start()
        display.show(handle_line(state, "play 1-1"))
        self.assertEqual(terminal.slept, [])

    def test_the_combo_flashes_when_it_goes_up(self):
        """Three flashes, each a redraw with a pause."""
        display, terminal, state = make_display()
        display.start()
        state.combo = 1
        terminal.written.clear()
        display.after_command(0)
        self.assertEqual(len(terminal.slept), 6)
        self.assertTrue(any("\x1b[7m" in chunk and "COMBO x1" in chunk for chunk in terminal.written))

    def test_the_combo_does_not_flash_when_it_stays_or_drops(self):
        """No pause."""
        display, terminal, state = make_display()
        display.start()
        state.combo = 2
        display.after_command(2)
        display.after_command(5)
        self.assertEqual(terminal.slept, [])

    def test_the_cursor_is_hidden_during_an_animation_and_shown_after(self):
        """Never left hidden."""
        display, terminal, state = make_display()
        display.start()
        display.show(handle_line(state, "play 1-1"))
        text = terminal.text()
        self.assertIn("\x1b[?25l", text)
        self.assertLess(text.rindex("\x1b[?25l"), text.rindex("\x1b[?25h"))

    def test_level_clear_frames_are_animated_in_the_body(self):
        """The stars fill in: several frames and pauses."""
        display, terminal, state = make_display()
        display.start()
        handle_line(state, "play 1-1")
        handle_line(state, ":wave 3")
        type_code(state, "a")
        handle_line(state, ":submit")
        handle_line(state, ":wave 1")
        handle_line(state, ':edit 1 print("a")')
        handle_line(state, ":submit")
        handle_line(state, ":wave 2")
        type_code(state, '# a\nprint("a")')
        answer = handle_line(state, ":submit")
        self.assertIsInstance(answer, list)
        terminal.written.clear()
        display.show(answer)
        self.assertGreater(len(terminal.slept), 5)
        self.assertIn("NEW COMMAND: status", strip_ansi(terminal.text()))


class TestPagingAndReading(unittest.TestCase):
    """Long answers and the typing row."""

    def test_the_story_is_a_page_of_its_own_so_the_wave_can_be_typed_at_once(self):
        """Story, Enter, tips, Enter, and the wave: one thing at a time."""
        display, terminal, state = make_display()
        display.start()
        display.show(handle_line(state, "play 1-1"))
        self.assertEqual(len(terminal.typed), 2)
        rows = "\n".join(terminal.last_frame_rows().values())
        self.assertNotIn("┌─ TIPS", rows)
        self.assertIn("┌─ WAVE 1 of 3", rows)

    def test_enter_during_the_title_animation_is_the_enter_to_continue(self):
        """One press, not two."""
        display, terminal, state = make_display()
        display.start()
        terminal.skip = True
        display.show_title()
        self.assertEqual(terminal.typed, [])
        self.assertIn("PRESS ENTER", strip_ansi(terminal.text()))

    def test_the_title_waits_for_enter_when_nothing_was_pressed(self):
        """The last frame says PRESS ENTER and waits."""
        display, terminal, state = make_display()
        display.start()
        display.show_title()
        self.assertEqual(len(terminal.typed), 1)

    def test_a_long_answer_is_split_in_pages_with_enter_for_more(self):
        """The player presses Enter between pages."""
        display, terminal, _ = make_display()
        display.start()
        long_text = "\n".join(f"line {i}" for i in range(60))
        display.show(long_text)
        self.assertGreaterEqual(len(terminal.typed), 1)
        self.assertIn("line 59", strip_ansi(terminal.text()))

    def test_read_moves_to_the_bottom_row_and_redraws_afterwards(self):
        """So the screen never scrolls when Enter is pressed."""
        display, terminal, _ = make_display()
        display.start()
        display.show("hello")
        terminal.written.clear()
        line = display.read(lambda prompt: "typed", "> ")
        self.assertEqual(line, "typed")
        text = terminal.text()
        self.assertTrue(text.startswith("\x1b[24;1H\x1b[K"))
        self.assertIn("\x1b[1;1H", text)

    def test_the_prompt_is_passed_to_the_reader(self):
        """The real input() shows it."""
        display, terminal, _ = make_display()
        display.start()
        seen = []
        display.read(lambda prompt: seen.append(prompt) or "", "  3 │ ")
        self.assertEqual(seen, ["  3 │ "])


class TestHudInfo(unittest.TestCase):
    """What the HUD gets from the game."""

    def test_at_the_map(self):
        """The world only."""
        state = GameState([make_full_level()])
        info = hud_info(state)
        self.assertEqual((info.world, info.level_id, info.coins), (1, None, state.coins))
        self.assertEqual(info.max_stars, 3)

    def test_in_a_level(self):
        """The level shows."""
        state = GameState([make_full_level()])
        handle_line(state, "play 1-1")
        self.assertEqual(hud_info(state).level_id, "1-1")

    def test_in_a_boss_fight_the_tries_show(self):
        """TRIES."""
        from tests.helpers import make_boss_level

        state = GameState([make_boss_level()])
        handle_line(state, "play boss-1")
        self.assertEqual(hud_info(state).tries, (3, 3))


if __name__ == "__main__":
    unittest.main()
