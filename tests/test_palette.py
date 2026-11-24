"""Tests for render/palette.py."""

import os
import tempfile
import unittest
from pathlib import Path

from render.palette import background, foreground, load_palette

ART_FOLDER = Path(__file__).parent.parent / "art"


def write_temporary_file(test, text):
    """Write `text` to a temporary file, delete it after `test`, return its path."""
    handle, path = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(handle, "w", encoding="utf-8") as temporary_file:
        temporary_file.write(text)
    test.addCleanup(os.remove, path)
    return path


class TestColourCodes(unittest.TestCase):
    """Check that colours turn into the right ANSI escape codes."""

    def test_foreground_uses_code_38(self):
        """A foreground colour starts with 38;2 followed by red;green;blue."""
        self.assertEqual(foreground((41, 173, 255)), "\x1b[38;2;41;173;255m")

    def test_background_uses_code_48(self):
        """A background colour starts with 48;2 followed by red;green;blue."""
        self.assertEqual(background((29, 43, 83)), "\x1b[48;2;29;43;83m")


class TestLoadPalette(unittest.TestCase):
    """Check reading palette files, good and broken."""

    def test_reads_colours_and_skips_comments(self):
        """Comment and blank lines are skipped; colour lines become entries."""
        path = write_temporary_file(self, "# comment\n\n1 10 20 30 grey\na 0 0 255 blue\n")
        self.assertEqual(load_palette(path), {"1": (10, 20, 30), "a": (0, 0, 255)})

    def test_real_palette_has_the_robot_colours(self):
        """The game's palette file has the three placeholder colours."""
        palette = load_palette(ART_FOLDER / "palette.txt")
        self.assertEqual(palette["1"], (194, 195, 199))
        self.assertEqual(palette["2"], (29, 43, 83))
        self.assertEqual(palette["3"], (41, 173, 255))

    def test_missing_part_is_an_error(self):
        """A line without a name is rejected, with its line number."""
        path = write_temporary_file(self, "1 10 20 30 grey\n2 10 20 30\n")
        with self.assertRaisesRegex(ValueError, "line 2"):
            load_palette(path)

    def test_number_above_255_is_an_error(self):
        """Colour values must be from 0 to 255."""
        path = write_temporary_file(self, "1 10 256 30 grey\n")
        with self.assertRaisesRegex(ValueError, "0 to 255"):
            load_palette(path)

    def test_word_instead_of_number_is_an_error(self):
        """Colour values must be numbers."""
        path = write_temporary_file(self, "1 red 20 30 grey\n")
        with self.assertRaisesRegex(ValueError, "0 to 255"):
            load_palette(path)

    def test_long_code_is_an_error(self):
        """A code must be one character."""
        path = write_temporary_file(self, "12 10 20 30 grey\n")
        with self.assertRaisesRegex(ValueError, "one character"):
            load_palette(path)

    def test_dot_code_is_an_error(self):
        """"." is kept for transparent pixels, so it cannot be a colour."""
        path = write_temporary_file(self, ". 10 20 30 grey\n")
        with self.assertRaisesRegex(ValueError, "one character"):
            load_palette(path)

    def test_code_used_twice_is_an_error(self):
        """Each code can only stand for one colour."""
        path = write_temporary_file(self, "1 10 20 30 grey\n1 0 0 0 black\n")
        with self.assertRaisesRegex(ValueError, "used twice"):
            load_palette(path)


if __name__ == "__main__":
    unittest.main()
