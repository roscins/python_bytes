"""Tests for render/ansi.py, render/panel.py, render/hud.py and render/screen.py.

Everything here is a pure function: text in, text out. No terminal is needed.
"""

import unittest

from render.ansi import fit, pad, strip_ansi, visible_length
from render.hud import HudInfo, hud_lines
from render.panel import panel, wrap_lines
from render.screen import MIN_COLUMNS, MIN_ROWS, compose_screen, draw_commands, paginate, too_small_message

RED = "\x1b[31m"
RESET = "\x1b[0m"


class TestAnsi(unittest.TestCase):
    """Width of text that has colour codes in it."""

    def test_strip_and_length(self):
        """Colour codes take no room."""
        text = f"{RED}hello{RESET} you"
        self.assertEqual(strip_ansi(text), "hello you")
        self.assertEqual(visible_length(text), 9)

    def test_pad_uses_the_visible_length(self):
        """Pad to a width with spaces after the visible text."""
        self.assertEqual(pad(f"{RED}ab{RESET}", 5), f"{RED}ab{RESET}   ")
        self.assertEqual(pad("abcdef", 3), "abcdef")

    def test_fit_cuts_the_visible_text_and_closes_colours(self):
        """Never longer than the width, and never leaves a colour open."""
        cut = fit(f"{RED}abcdefgh{RESET}", 5)
        self.assertEqual(strip_ansi(cut), "abcde")
        self.assertTrue(cut.endswith(RESET))

    def test_fit_leaves_short_text_alone(self):
        """Nothing to cut."""
        self.assertEqual(fit("abc", 5), "abc")

    def test_fit_counts_wide_symbols_as_one_cell(self):
        """Stars and box characters are one cell wide in the game's layout."""
        self.assertEqual(visible_length("★☆│"), 3)


class TestWrap(unittest.TestCase):
    """Long lines are wrapped; code and coloured lines are cut instead."""

    def test_wraps_text_at_word_boundaries(self):
        """A long sentence becomes several lines of at most the width."""
        lines = wrap_lines(["one two three four five six seven"], 12)
        self.assertTrue(len(lines) > 1)
        for line in lines:
            self.assertLessEqual(len(line), 12)

    def test_indented_lines_keep_their_indent_when_wrapped(self):
        """A tip or a code line keeps its leading spaces on the first line."""
        lines = wrap_lines(["    print(1)"], 40)
        self.assertEqual(lines, ["    print(1)"])

    def test_blank_lines_stay(self):
        """Empty lines are kept."""
        self.assertEqual(wrap_lines(["a", "", "b"], 10), ["a", "", "b"])

    def test_coloured_lines_are_cut_not_wrapped(self):
        """A highlighted code line stays one line."""
        coloured = f"{RED}{'x' * 30}{RESET}"
        lines = wrap_lines([coloured], 10)
        self.assertEqual(len(lines), 1)
        self.assertEqual(visible_length(lines[0]), 10)


class TestPanel(unittest.TestCase):
    """Boxes with box-drawing characters."""

    def test_shape(self):
        """Top line with the title, one line per text line, bottom line."""
        box = panel("STORY", ["hello", "world"], 20)
        self.assertEqual(len(box), 4)
        self.assertEqual(box[0], "┌─ STORY " + "─" * 10 + "┐")
        self.assertEqual(box[1], "│ hello" + " " * 12 + "│")
        self.assertEqual(box[3], "└" + "─" * 18 + "┘")

    def test_every_line_is_exactly_the_width(self):
        """Corners and sides line up."""
        for text in (["short"], ["a long line " * 10], [f"{RED}coloured{RESET}"], []):
            for line in panel("T", text, 30):
                self.assertEqual(visible_length(line), 30, line)

    def test_ascii_version(self):
        """No non-ASCII character at all."""
        box = panel("STORY", ["hello"], 20, ascii_only=True)
        for line in box:
            self.assertTrue(line.isascii(), line)
        self.assertEqual(box[0][0], "+")
        self.assertEqual(box[1][0], "|")

    def test_long_text_is_wrapped_inside(self):
        """The box grows taller, not wider."""
        box = panel("T", ["word " * 30], 30)
        self.assertGreater(len(box), 3)

    def test_empty_title(self):
        """A panel without a title is just a box."""
        self.assertEqual(panel("", ["x"], 10)[0], "┌" + "─" * 8 + "┐")


class TestHud(unittest.TestCase):
    """The two lines at the top of every screen."""

    def info(self, **changes):
        """Return a HudInfo for Level 1-2."""
        values = dict(world=1, world_name="Boot Sector", level_id="1-2", level_title="Memory Cells",
                      stars=7, max_stars=18, coins=35, combo=3, tries=None, flash=False)
        values.update(changes)
        return HudInfo(**values)

    def test_two_lines_of_the_screen_width(self):
        """Always exactly 80 cells wide."""
        lines = hud_lines(self.info(), 80, color=False)
        self.assertEqual(len(lines), 2)
        for line in lines:
            self.assertEqual(visible_length(line), 80)

    def test_first_line_names_world_and_level(self):
        """WORLD 1 · BOOT SECTOR · 1-2 MEMORY CELLS."""
        first = hud_lines(self.info(), 80, color=False)[0]
        self.assertIn("WORLD 1 · BOOT SECTOR · 1-2 MEMORY CELLS", first)

    def test_second_line_has_stars_coins_and_combo(self):
        """No XP and no lives."""
        second = hud_lines(self.info(), 80, color=False)[1]
        self.assertIn("★ 7/18", second)
        self.assertIn("COINS 35", second)
        self.assertIn("COMBO x3", second)
        self.assertNotIn("XP", second)
        self.assertNotIn("LIVES", second)

    def test_no_combo_is_not_shown(self):
        """Zero combo says nothing."""
        self.assertNotIn("COMBO", hud_lines(self.info(combo=0), 80, color=False)[1])

    def test_a_boss_fight_shows_the_tries_left(self):
        """TRIES 2 of 3."""
        second = hud_lines(self.info(tries=(2, 3)), 80, color=False)[1]
        self.assertIn("TRIES 2 of 3", second)

    def test_at_the_map_there_is_no_level(self):
        """Only the world."""
        first = hud_lines(self.info(level_id=None, level_title=""), 80, color=False)[0]
        self.assertIn("WORLD 1 · BOOT SECTOR", first)
        self.assertNotIn("1-2", first)

    def test_colour_is_added_only_when_asked(self):
        """Plain has no escape codes."""
        for line in hud_lines(self.info(), 80, color=False):
            self.assertNotIn("\x1b", line)
        self.assertIn("\x1b[", "".join(hud_lines(self.info(), 80, color=True)))

    def test_flash_makes_the_combo_stand_out(self):
        """Inverse video around the combo while it flashes; the text stays the same."""
        steady = hud_lines(self.info(), 80, color=True)[1]
        flashing = hud_lines(self.info(flash=True), 80, color=True)[1]
        self.assertNotEqual(steady, flashing)
        self.assertEqual(strip_ansi(steady), strip_ansi(flashing))

    def test_long_titles_are_cut_to_fit(self):
        """A title longer than the line does not break the layout."""
        lines = hud_lines(self.info(level_title="Very " * 30), 80, color=False)
        self.assertEqual(visible_length(lines[0]), 80)


class TestPaginate(unittest.TestCase):
    """A body longer than the screen is split into pages."""

    def test_short_body_is_one_page(self):
        """Nothing to split."""
        self.assertEqual(paginate(["a", "b"], 5), [["a", "b"]])

    def test_long_body_is_split_in_equal_pages(self):
        """No page is taller than the height."""
        pages = paginate([str(i) for i in range(12)], 5)
        self.assertEqual([len(page) for page in pages], [5, 5, 2])

    def test_empty_body_is_one_empty_page(self):
        """Always at least one page."""
        self.assertEqual(paginate([], 5), [[]])


class TestCompose(unittest.TestCase):
    """The whole screen: HUD, body, status line."""

    def compose(self, body, rows=24, status=""):
        """Compose a frame of 80 x `rows` with a plain HUD."""
        hud = ["HUD ONE", "HUD TWO"]
        return compose_screen(hud, body, status, rows)

    def test_the_frame_has_one_row_less_than_the_window(self):
        """The last row is for the player's typing."""
        self.assertEqual(len(self.compose(["x"], rows=24)), 23)
        self.assertEqual(len(self.compose(["x"], rows=30)), 29)

    def test_every_row_is_the_full_width(self):
        """Padded, so old text is overwritten."""
        for line in self.compose(["short", "line"]):
            self.assertEqual(visible_length(line), 80)

    def test_hud_is_at_the_top_body_below_status_at_the_bottom(self):
        """The layout."""
        frame = self.compose(["BODY ONE"], status="STATUS")
        self.assertTrue(frame[0].startswith("HUD ONE"))
        self.assertTrue(frame[1].startswith("HUD TWO"))
        self.assertTrue(frame[3].startswith("BODY ONE"))
        self.assertTrue(frame[-1].startswith("STATUS"))

    def test_a_body_that_is_too_tall_is_cut_not_overflowing(self):
        """The frame keeps its size."""
        frame = self.compose([f"line {i}" for i in range(100)])
        self.assertEqual(len(frame), 23)

    def test_the_hud_is_on_every_composed_screen(self):
        """Whatever the body."""
        for body in ([], ["a"], ["a"] * 50):
            frame = self.compose(body)
            self.assertTrue(frame[0].startswith("HUD ONE"))

    def test_body_height_is_what_the_pages_use(self):
        """The body area is rows - 5 lines (HUD 2, rule 1, status 1, prompt 1)."""
        from render.screen import body_height

        self.assertEqual(body_height(24), 19)


class TestDrawCommands(unittest.TestCase):
    """The escape codes that put a frame on the screen."""

    def test_each_row_is_placed_and_cleared_to_the_end(self):
        """Absolute positions, so nothing scrolls."""
        text = draw_commands(["one", "two"])
        self.assertEqual(text, "\x1b[1;1Hone\x1b[K\x1b[2;1Htwo\x1b[K")

    def test_too_small_window(self):
        """A polite message that names the size."""
        message = too_small_message(60, 20)
        self.assertIn("80", message)
        self.assertIn("24", message)
        self.assertEqual((MIN_COLUMNS, MIN_ROWS), (80, 24))


if __name__ == "__main__":
    unittest.main()
