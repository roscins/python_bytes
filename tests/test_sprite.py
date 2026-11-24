"""Tests for render/sprite.py and render/__main__.py."""

import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from render import __main__ as render_main
from render.sprite import (
    LOWER_HALF_BLOCK,
    RESET,
    UPPER_HALF_BLOCK,
    SpriteError,
    draw_cell,
    load_sprite,
    render_sprite,
)
from render.palette import background, foreground, load_palette
from tests.test_palette import write_temporary_file

ART_FOLDER = Path(__file__).parent.parent / "art"

# A small palette for tests, so they do not depend on art/palette.txt.
PALETTE = {"1": (194, 195, 199), "2": (29, 43, 83)}


class TestDrawCell(unittest.TestCase):
    """Check the four cases of drawing two stacked pixels."""

    def test_both_transparent_is_a_space(self):
        """Two empty pixels become a plain space."""
        self.assertEqual(draw_cell(".", ".", PALETTE), RESET + " ")

    def test_only_bottom_pixel_uses_lower_half(self):
        """Only a bottom pixel: draw the lower half block in that colour."""
        expected = RESET + foreground(PALETTE["1"]) + LOWER_HALF_BLOCK
        self.assertEqual(draw_cell(".", "1", PALETTE), expected)

    def test_only_top_pixel_uses_upper_half(self):
        """Only a top pixel: draw the upper half block in that colour."""
        expected = RESET + foreground(PALETTE["1"]) + UPPER_HALF_BLOCK
        self.assertEqual(draw_cell("1", ".", PALETTE), expected)

    def test_two_pixels_use_foreground_and_background(self):
        """Two pixels: top is the text colour, bottom is the background."""
        expected = foreground(PALETTE["1"]) + background(PALETTE["2"]) + UPPER_HALF_BLOCK
        self.assertEqual(draw_cell("1", "2", PALETTE), expected)


class TestLoadSprite(unittest.TestCase):
    """Check reading sprite files, good and broken."""

    def test_reads_rows_and_skips_comments(self):
        """Comment and blank lines are skipped; pixel rows are kept."""
        path = write_temporary_file(self, "# a comment\n12\n\n21\n")
        self.assertEqual(load_sprite(path, PALETTE), ["12", "21"])

    def test_odd_number_of_rows_gets_a_transparent_row(self):
        """Three rows become four, with a transparent row at the bottom."""
        path = write_temporary_file(self, "12\n21\n11\n")
        self.assertEqual(load_sprite(path, PALETTE), ["12", "21", "11", ".."])

    def test_uneven_rows_are_an_error(self):
        """All rows must be as wide as the first, and the error says where."""
        path = write_temporary_file(self, "12\n121\n")
        with self.assertRaisesRegex(SpriteError, "line 2"):
            load_sprite(path, PALETTE)

    def test_unknown_code_is_an_error(self):
        """A pixel that is not in the palette is rejected."""
        path = write_temporary_file(self, "12\n19\n")
        with self.assertRaisesRegex(SpriteError, "'9' is not in the palette"):
            load_sprite(path, PALETTE)

    def test_empty_file_is_an_error(self):
        """A file with only comments has nothing to draw."""
        path = write_temporary_file(self, "# nothing here\n")
        with self.assertRaisesRegex(SpriteError, "no rows"):
            load_sprite(path, PALETTE)

    def test_sprite_error_is_a_value_error(self):
        """Code that catches ValueError also catches SpriteError."""
        self.assertTrue(issubclass(SpriteError, ValueError))


class TestRobot(unittest.TestCase):
    """Check the real robot sprite with the real palette."""

    def setUp(self):
        """Load the game's palette and the robot sprite."""
        self.palette = load_palette(ART_FOLDER / "palette.txt")
        self.robot = load_sprite(ART_FOLDER / "robot.txt", self.palette)

    def test_robot_is_eight_by_eight(self):
        """The robot sprite has 8 rows of 8 pixels each."""
        self.assertEqual(len(self.robot), 8)
        for row in self.robot:
            self.assertEqual(len(row), 8)

    def test_eight_rows_become_four_lines(self):
        """Two pixel rows share one terminal line."""
        self.assertEqual(len(render_sprite(self.robot, self.palette)), 4)

    def test_every_line_ends_with_reset(self):
        """Each line resets colours so the next line starts clean."""
        for line in render_sprite(self.robot, self.palette):
            self.assertTrue(line.endswith(RESET))


class TestAriaOffline(unittest.TestCase):
    """Check the ARIA reference sprite from the art style guide."""

    def setUp(self):
        """Load the game's palette and the ARIA sprite."""
        self.palette = load_palette(ART_FOLDER / "palette.txt")
        self.aria = load_sprite(ART_FOLDER / "aria-offline.txt", self.palette)

    def test_aria_is_sixteen_by_sixteen(self):
        """ARIA is 16 x 16 pixels, as the art style guide says."""
        self.assertEqual(len(self.aria), 16)
        for row in self.aria:
            self.assertEqual(len(row), 16)

    def test_aria_draws_as_eight_lines(self):
        """Sixteen pixel rows become eight terminal lines."""
        self.assertEqual(len(render_sprite(self.aria, self.palette)), 8)

    def test_aria_file_has_no_comments(self):
        """The art style guide says sprite files contain only pixel rows."""
        with open(ART_FOLDER / "aria-offline.txt", encoding="utf-8") as sprite_file:
            for line in sprite_file:
                self.assertFalse(line.startswith("#"))


class TestCommandLine(unittest.TestCase):
    """Check python -m render by calling its main function."""

    def run_main(self, arguments):
        """Run main with `arguments`; return the exit code and what it printed."""
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = render_main.main(arguments)
        return exit_code, output.getvalue()

    def test_draws_the_robot(self):
        """Drawing the robot prints four lines and succeeds."""
        exit_code, text = self.run_main([str(ART_FOLDER / "robot.txt")])
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(text.splitlines()), 4)

    def test_no_file_shows_usage(self):
        """Without a file name, it explains how to use it."""
        exit_code, text = self.run_main([])
        self.assertEqual(exit_code, 2)
        self.assertIn("Usage", text)

    def test_missing_file_is_reported(self):
        """A file that does not exist gives a message, not a crash."""
        exit_code, text = self.run_main(["no/such/sprite.txt"])
        self.assertEqual(exit_code, 1)
        self.assertIn("Cannot draw the sprite", text)


if __name__ == "__main__":
    unittest.main()
