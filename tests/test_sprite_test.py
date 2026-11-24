"""Tests for render/sprite_test.py."""

import unittest

from render import sprite_test


class TestColourCodes(unittest.TestCase):
    """Check that palette colours turn into the right ANSI escape codes."""

    def test_foreground_uses_code_38(self):
        """A foreground colour starts with 38;2 followed by red;green;blue."""
        self.assertEqual(sprite_test.foreground("3"), "\x1b[38;2;41;173;255m")

    def test_background_uses_code_48(self):
        """A background colour starts with 48;2 followed by red;green;blue."""
        self.assertEqual(sprite_test.background("2"), "\x1b[48;2;29;43;83m")


class TestDrawCell(unittest.TestCase):
    """Check the four cases of drawing two stacked pixels."""

    def test_both_transparent_is_a_space(self):
        """Two empty pixels become a plain space."""
        self.assertEqual(sprite_test.draw_cell(".", "."), sprite_test.RESET + " ")

    def test_only_bottom_pixel_uses_lower_half(self):
        """Only a bottom pixel: draw the lower half block in that colour."""
        expected = (
            sprite_test.RESET
            + sprite_test.foreground("1")
            + sprite_test.LOWER_HALF_BLOCK
        )
        self.assertEqual(sprite_test.draw_cell(".", "1"), expected)

    def test_only_top_pixel_uses_upper_half(self):
        """Only a top pixel: draw the upper half block in that colour."""
        expected = (
            sprite_test.RESET
            + sprite_test.foreground("1")
            + sprite_test.UPPER_HALF_BLOCK
        )
        self.assertEqual(sprite_test.draw_cell("1", "."), expected)

    def test_two_pixels_use_foreground_and_background(self):
        """Two pixels: top is the text colour, bottom is the background."""
        expected = (
            sprite_test.foreground("1")
            + sprite_test.background("2")
            + sprite_test.UPPER_HALF_BLOCK
        )
        self.assertEqual(sprite_test.draw_cell("1", "2"), expected)


class TestRenderSprite(unittest.TestCase):
    """Check the shape of the whole rendered sprite."""

    def test_robot_is_eight_by_eight(self):
        """The robot sprite has 8 rows of 8 pixels each."""
        self.assertEqual(len(sprite_test.ROBOT), 8)
        for row in sprite_test.ROBOT:
            self.assertEqual(len(row), 8)

    def test_robot_only_uses_palette_codes(self):
        """Every pixel is either transparent or a colour in the palette."""
        for row in sprite_test.ROBOT:
            for pixel in row:
                self.assertTrue(
                    pixel == sprite_test.TRANSPARENT or pixel in sprite_test.PALETTE
                )

    def test_eight_rows_become_four_lines(self):
        """Two pixel rows share one terminal line."""
        lines = sprite_test.render_sprite(sprite_test.ROBOT)
        self.assertEqual(len(lines), 4)

    def test_every_line_ends_with_reset(self):
        """Each line resets colours so the next line starts clean."""
        for line in sprite_test.render_sprite(sprite_test.ROBOT):
            self.assertTrue(line.endswith(sprite_test.RESET))


if __name__ == "__main__":
    unittest.main()
