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
    draw_row_pair,
    load_sprite,
    render_sprite,
)
from render.palette import TRANSPARENT, background, foreground, load_palette
from tests.helpers import write_temporary_file

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


class TestDrawRowPair(unittest.TestCase):
    """Check that two pixel rows become one terminal line."""

    def test_row_pair_is_cells_then_reset(self):
        """Each column becomes one cell, and the line ends with a reset."""
        expected = draw_cell("1", ".", PALETTE) + draw_cell("2", "1", PALETTE) + RESET
        self.assertEqual(draw_row_pair("12", ".1", PALETTE), expected)


class TestRenderSprite(unittest.TestCase):
    """Check render_sprite on sprites made in code."""

    def test_odd_number_of_rows_is_an_error(self):
        """A sprite that did not come from load_sprite may have odd rows."""
        with self.assertRaisesRegex(SpriteError, "even number"):
            render_sprite(["12", "21", "11"], PALETTE)


class TestLoadSprite(unittest.TestCase):
    """Check reading sprite files, good and broken."""

    def test_reads_rows(self):
        """Each line of the file is one row of pixels."""
        path = write_temporary_file(self, "12\n21\n")
        self.assertEqual(load_sprite(path, PALETTE), ["12", "21"])

    def test_comment_is_an_error(self):
        """The art style guide does not allow comments in sprite files."""
        path = write_temporary_file(self, "# a comment\n12\n21\n")
        with self.assertRaisesRegex(SpriteError, "line 1: comments are not allowed"):
            load_sprite(path, PALETTE)

    def test_blank_line_is_an_error(self):
        """The art style guide does not allow blank lines in sprite files."""
        path = write_temporary_file(self, "12\n\n21\n")
        with self.assertRaisesRegex(SpriteError, "line 2: blank lines are not allowed"):
            load_sprite(path, PALETTE)

    def test_space_gets_a_clear_message(self):
        """A trailing space says to use "." instead."""
        path = write_temporary_file(self, "12 \n21.\n")
        with self.assertRaisesRegex(SpriteError, "spaces are not allowed, use '.'"):
            load_sprite(path, PALETTE)

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
        """An empty file has nothing to draw."""
        path = write_temporary_file(self, "")
        with self.assertRaisesRegex(SpriteError, "no rows"):
            load_sprite(path, PALETTE)

    def test_sprite_error_is_a_value_error(self):
        """Code that catches ValueError also catches SpriteError."""
        self.assertTrue(issubclass(SpriteError, ValueError))


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

    def test_every_line_ends_with_reset(self):
        """Each line resets colours so the next line starts clean."""
        for line in render_sprite(self.aria, self.palette):
            self.assertTrue(line.endswith(RESET))


class TestEverySpriteFollowsTheArtGuide(unittest.TestCase):
    """Check every sprite file in art/ against the art style guide."""

    def setUp(self):
        """Load the palette and find every sprite file (all but palette.txt)."""
        self.palette = load_palette(ART_FOLDER / "palette.txt")
        self.sprite_paths = []
        for path in sorted(ART_FOLDER.glob("*.txt")):
            if path.name != "palette.txt":
                self.sprite_paths.append(path)

    def test_there_are_sprites_to_check(self):
        """The art folder has at least the ARIA reference sprite."""
        self.assertIn(ART_FOLDER / "aria-offline.txt", self.sprite_paths)

    def test_names_are_subject_dash_state(self):
        """Files are named <subject>-<state>.txt, for example aria-offline.txt."""
        for path in self.sprite_paths:
            with self.subTest(sprite=path.name):
                self.assertIn("-", path.stem)
                self.assertEqual(path.stem, path.stem.lower())

    def test_sprites_load_and_have_an_even_row_count(self):
        """Every sprite loads (so it has no comments or blank lines) and has even rows.

        load_sprite would pad an odd sprite, so the file itself is counted.
        """
        for path in self.sprite_paths:
            with self.subTest(sprite=path.name):
                load_sprite(path, self.palette)
                with open(path, encoding="utf-8") as sprite_file:
                    row_count = len(sprite_file.read().splitlines())
                self.assertEqual(row_count % 2, 0)

    def test_at_most_four_colours_plus_outline(self):
        """Style rule 3: a sprite uses at most 4 colours plus the Slate outline (2)."""
        for path in self.sprite_paths:
            with self.subTest(sprite=path.name):
                colours = set()
                for row in load_sprite(path, self.palette):
                    for pixel in row:
                        if pixel != TRANSPARENT and pixel != "2":
                            colours.add(pixel)
                self.assertLessEqual(len(colours), 4)


class TestCommandLine(unittest.TestCase):
    """Check python -m render by calling its main function."""

    def run_main(self, arguments):
        """Run main with `arguments`; return the exit code and what it printed."""
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = render_main.main(arguments)
        return exit_code, output.getvalue()

    def test_draws_aria(self):
        """Drawing ARIA prints eight lines and succeeds."""
        exit_code, text = self.run_main([str(ART_FOLDER / "aria-offline.txt")])
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(text.splitlines()), 8)

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

    def test_broken_file_is_reported(self):
        """A sprite file with a mistake gives a message, not a crash."""
        path = write_temporary_file(self, "12\n1\n")
        exit_code, text = self.run_main([path])
        self.assertEqual(exit_code, 1)
        self.assertIn("Cannot draw the sprite", text)


if __name__ == "__main__":
    unittest.main()
