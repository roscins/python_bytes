"""Tests for render/typewriter.py, render/reactions.py, render/title_art.py and the 256-colour fallback."""

import unittest

from render.ansi import strip_ansi, to_256, visible_length
from render.palette import load_palette
from render.reactions import REACTION_NAMES, ART_FOLDER, load_reaction_art, reaction_lines, side_by_side
from render.title_art import GLYPHS, LOGO_TEXT, load_title_art, logo_canvas, title_frames
from render.typewriter import play_frames, typewriter_frames


class TestTypewriterFrames(unittest.TestCase):
    """The text appears a few letters at a time."""

    def test_the_last_frame_is_the_whole_text(self):
        """Nothing is lost."""
        text = "The lab is dark. One terminal blinks."
        self.assertEqual(typewriter_frames(text, step=3)[-1], text)

    def test_every_frame_is_the_start_of_the_next(self):
        """The text only grows."""
        frames = typewriter_frames("Snek wakes up, slowly.", step=2)
        for index in range(1, len(frames)):
            self.assertTrue(frames[index].startswith(frames[index - 1]))

    def test_the_first_frame_is_short(self):
        """It starts almost empty."""
        self.assertLessEqual(len(typewriter_frames("Hello there, technician.", step=3)[0]), 3)

    def test_step_sets_how_many_letters_come_at_once(self):
        """Bigger steps, fewer frames."""
        text = "a" * 30
        self.assertLess(len(typewriter_frames(text, step=5)), len(typewriter_frames(text, step=1)))

    def test_a_pause_after_punctuation(self):
        """A full stop holds the frame a little longer (the same frame comes again)."""
        frames = typewriter_frames("Hi. Yo", step=1)
        self.assertGreater(frames.count("Hi."), 1)

    def test_empty_text(self):
        """One empty frame."""
        self.assertEqual(typewriter_frames("", step=3), [""])

    def test_newlines_are_kept(self):
        """The story has lines."""
        self.assertEqual(typewriter_frames("a\nb", step=1)[-1], "a\nb")


class TestPlayFrames(unittest.TestCase):
    """Showing frames with timing that the caller provides."""

    def test_every_frame_is_shown_with_a_pause_between(self):
        """No skip pressed."""
        shown, slept = [], []
        skipped = play_frames(["a", "b", "c"], shown.append, slept.append, lambda: False, 0.05)
        self.assertEqual(shown, ["a", "b", "c"])
        self.assertEqual(slept, [0.05, 0.05])
        self.assertFalse(skipped)

    def test_enter_jumps_to_the_last_frame(self):
        """The rest is skipped, and the last frame is shown."""
        shown, slept = [], []
        presses = iter([False, True])
        skipped = play_frames(["a", "b", "c", "d"], shown.append, slept.append, lambda: next(presses), 0.05)
        self.assertEqual(shown, ["a", "b", "d"])
        self.assertTrue(skipped)

    def test_a_single_frame_needs_no_pause(self):
        """Just shown."""
        shown, slept = [], []
        play_frames(["only"], shown.append, slept.append, lambda: False, 0.05)
        self.assertEqual((shown, slept), (["only"], []))

    def test_no_delay_means_no_waiting(self):
        """The plain mode: all frames at once, never sleeping."""
        shown, slept = [], []
        play_frames(["a", "b"], shown.append, slept.append, lambda: False, 0)
        self.assertEqual(slept, [])


class TestReactions(unittest.TestCase):
    """Snek's faces."""

    @classmethod
    def setUpClass(cls):
        """Load the real sprites once."""
        cls.art = load_reaction_art()

    def test_the_four_faces_exist(self):
        """idle, happy, dizzy, celebrate."""
        self.assertEqual(sorted(REACTION_NAMES), ["celebrate", "dizzy", "happy", "idle"])

    def test_each_is_16_by_16_and_uses_the_palette(self):
        """The art guide's size and colours."""
        palette = load_palette(ART_FOLDER / "palette.txt")
        for name in REACTION_NAMES:
            sprite = self.art.sprites[name]
            with self.subTest(name=name):
                self.assertEqual(len(sprite), 16)
                for row in sprite:
                    self.assertEqual(len(row), 16)
                    for pixel in row:
                        self.assertTrue(pixel == "." or pixel in palette, pixel)

    def test_the_faces_are_different_from_each_other(self):
        """Happy is not dizzy is not celebrating."""
        sprites = [tuple(self.art.sprites[name]) for name in REACTION_NAMES]
        self.assertEqual(len(set(sprites)), 4)

    def test_lines_are_8_rows_of_16_cells(self):
        """16 pixels tall is 8 terminal rows."""
        for name in REACTION_NAMES:
            lines = reaction_lines(name, self.art)
            self.assertEqual(len(lines), 8)
            for line in lines:
                self.assertEqual(visible_length(line), 16)

    def test_unknown_face_is_an_error(self):
        """A typo is caught."""
        with self.assertRaises(KeyError):
            reaction_lines("angry", self.art)


class TestSideBySide(unittest.TestCase):
    """Text on the left, Snek on the right."""

    def test_columns_line_up(self):
        """Every row has the left text padded to its width, a gap, then the right."""
        rows = side_by_side(["aa", "b"], ["XX", "YY", "ZZ"], 5, gap=1)
        self.assertEqual(rows, ["aa    XX", "b     YY", "      ZZ"])

    def test_left_text_longer_than_its_column_is_cut(self):
        """The right side stays in place."""
        rows = side_by_side(["abcdefgh"], ["XX"], 4, gap=1)
        self.assertEqual(rows, ["abcd XX"])


class TestLogoAndTitle(unittest.TestCase):
    """The pixel-art PYTHON BYTES and Snek crossing the screen."""

    @classmethod
    def setUpClass(cls):
        """Load the real art once."""
        cls.art = load_title_art()

    def test_every_letter_of_the_logo_has_a_glyph(self):
        """P Y T H O N B E S."""
        for letter in set(LOGO_TEXT.replace(" ", "")):
            self.assertIn(letter, GLYPHS)

    def test_glyphs_are_5_wide_and_7_tall(self):
        """The pixel font."""
        for letter, rows in GLYPHS.items():
            with self.subTest(letter=letter):
                self.assertEqual(len(rows), 7)
                for row in rows:
                    self.assertEqual(len(row), 5)

    def test_the_logo_fits_the_80_pixel_screen(self):
        """And is centred."""
        canvas = logo_canvas(LOGO_TEXT)
        self.assertEqual(len(canvas[0]), 80)
        filled = [i for i, pixel in enumerate(canvas[1]) if pixel != "."]
        self.assertGreater(filled[0], 0)
        self.assertLess(filled[-1], 79)
        self.assertAlmostEqual(filled[0], 79 - filled[-1], delta=2)

    def test_frames_have_the_same_height_and_the_last_says_press_enter(self):
        """Snek moves, the logo stays."""
        frames = title_frames(self.art, step=8)
        heights = {len(frame.split("\n")) for frame in frames}
        self.assertEqual(len(heights), 1)
        self.assertIn("PRESS ENTER", strip_ansi(frames[-1]))
        self.assertNotIn("PRESS ENTER", strip_ansi(frames[0]))

    def test_snek_moves_across_the_screen(self):
        """Consecutive frames are different."""
        frames = title_frames(self.art, step=8)
        self.assertGreater(len(frames), 5)
        self.assertNotEqual(frames[1], frames[2])

    def test_the_logo_rows_do_not_change_between_frames(self):
        """Only Snek moves."""
        frames = title_frames(self.art, step=8)
        top = [frame.split("\n")[:4] for frame in frames]
        self.assertEqual(top[0], top[-1])


class TestTo256(unittest.TestCase):
    """Terminals without 24-bit colour (macOS Terminal) get 256 colours."""

    def test_true_colour_codes_become_256_colour_codes(self):
        """38;2;r;g;b -> 38;5;n and the same for the background."""
        text = "\x1b[38;2;255;0;0m\x1b[48;2;0;0;255mX\x1b[0m"
        result = to_256(text)
        self.assertNotIn(";2;", result)
        self.assertIn("\x1b[38;5;196m", result)
        self.assertIn("\x1b[48;5;21m", result)
        self.assertEqual(strip_ansi(result), "X")

    def test_greys_use_the_grey_ramp(self):
        """A mid grey is not turned into a colour of the cube."""
        result = to_256("\x1b[38;2;128;128;128mX")
        number = int(result.split("38;5;")[1].split("m")[0])
        self.assertTrue(232 <= number <= 255)

    def test_other_codes_are_untouched(self):
        """Resets, cursor moves, 16-colour codes."""
        for code in ("\x1b[0m", "\x1b[35m", "\x1b[2;3H", "\x1b[K"):
            self.assertEqual(to_256(code), code)

    def test_text_without_codes_is_the_same(self):
        """Nothing to do."""
        self.assertEqual(to_256("hello"), "hello")


if __name__ == "__main__":
    unittest.main()
