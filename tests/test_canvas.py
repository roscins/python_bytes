"""Tests for render/canvas.py."""

import unittest

from render.canvas import draw_line, new_canvas, paste, set_pixel


class TestCanvas(unittest.TestCase):
    """Check making a canvas and drawing on it."""

    def test_new_canvas_is_transparent(self):
        """A new canvas has the given size and only "." pixels."""
        self.assertEqual(new_canvas(3, 2), ["...", "..."])

    def test_set_pixel_changes_one_pixel(self):
        """Only the chosen pixel changes."""
        canvas = new_canvas(3, 2)
        set_pixel(canvas, 1, 0, "5")
        self.assertEqual(canvas, [".5.", "..."])

    def test_set_pixel_outside_is_ignored(self):
        """Pixels outside the canvas do nothing and do not crash."""
        canvas = new_canvas(2, 2)
        for column, row in [(-1, 0), (2, 0), (0, -1), (0, 2)]:
            set_pixel(canvas, column, row, "5")
        self.assertEqual(canvas, ["..", ".."])

    def test_paste_keeps_transparent_pixels(self):
        """"." in the sprite lets the canvas show through."""
        canvas = ["111", "111"]
        paste(canvas, ["2.", ".2"], 1, 0)
        self.assertEqual(canvas, ["121", "112"])

    def test_paste_cuts_off_at_the_edge(self):
        """A sprite hanging over the edge is cut off."""
        canvas = new_canvas(3, 2)
        paste(canvas, ["22", "22"], 2, 1)
        self.assertEqual(canvas, ["...", "..2"])

    def test_draw_line(self):
        """A line covers the columns from left to right, both included."""
        canvas = new_canvas(5, 3)
        draw_line(canvas, "7", 1, 3, 1, 2)
        self.assertEqual(canvas, [".....", ".777.", ".777."])


if __name__ == "__main__":
    unittest.main()
