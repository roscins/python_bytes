"""Tests for render/world_map.py."""

import re
import unittest

from render.world_map import (
    ARIA_SIZE,
    MAP_HEIGHT,
    MAP_WIDTH,
    WALK_STEP,
    WORLD_NAMES,
    aria_left,
    header_line,
    label_line,
    load_map_art,
    map_frame,
    map_screen,
    node_centre,
    walk_frames,
)

WORLD_1_IDS = ["1-1", "1-2", "1-3", "1-4", "boss-1"]

# Header, blank line, label line, then two pixel rows per terminal line.
FRAME_LINES = 3 + MAP_HEIGHT // 2


def without_colours(text):
    """Return `text` without ANSI escape codes, as the player would read it."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


class TestLayout(unittest.TestCase):
    """Check where nodes, labels and ARIA go."""

    def test_nodes_are_spread_evenly(self):
        """Five nodes share 80 columns, 16 each, centred in their share."""
        centres = []
        for index in range(5):
            centres.append(node_centre(index, 5))
        self.assertEqual(centres, [8, 24, 40, 56, 72])

    def test_one_node_is_in_the_middle(self):
        """A world with one level has its node in the middle."""
        self.assertEqual(node_centre(0, 1), MAP_WIDTH // 2)

    def test_aria_stays_on_the_map(self):
        """ARIA is never drawn past the left or right edge."""
        for count in range(1, 8):
            for index in range(count):
                left = aria_left(index, count)
                self.assertGreaterEqual(left, 0)
                self.assertLessEqual(left + ARIA_SIZE, MAP_WIDTH)

    def test_header_names_the_world(self):
        """The header shows the world's number and name."""
        self.assertEqual(header_line(1), "WORLD 1 · BOOT SECTOR")
        self.assertEqual(len(WORLD_NAMES), 8)
        self.assertEqual(header_line(99), "WORLD 99")

    def test_labels_are_centred_over_the_nodes(self):
        """Each label's middle is at its node's centre."""
        line = label_line(WORLD_1_IDS)
        start = line.index("[1-3]")
        self.assertEqual(start + len("[1-3]") // 2, node_centre(2, 5))
        self.assertLessEqual(len(line), MAP_WIDTH)


class TestFrames(unittest.TestCase):
    """Check whole map pictures with the real art."""

    def setUp(self):
        """Load the real palette and sprites."""
        self.art = load_map_art()

    def test_frame_has_header_labels_and_picture(self):
        """A frame is the header, a blank line, the labels and 12 picture lines."""
        lines = map_frame(1, WORLD_1_IDS, 0, self.art).split("\n")
        self.assertEqual(len(lines), FRAME_LINES)
        self.assertEqual(lines[0], "WORLD 1 · BOOT SECTOR")
        self.assertIn("[boss-1]", lines[2])

    def test_frame_is_never_wider_than_the_map(self):
        """Every line fits in 80 cells once the colour codes are taken out."""
        for line in map_frame(1, WORLD_1_IDS, 0, self.art).split("\n"):
            self.assertLessEqual(len(without_colours(line)), MAP_WIDTH)

    def test_map_without_aria_differs_from_map_with_aria(self):
        """With aria_index None, ARIA is left out."""
        with_aria = map_screen(1, WORLD_1_IDS, 0, self.art)
        without_aria = map_screen(1, WORLD_1_IDS, None, self.art)
        self.assertNotEqual(with_aria, without_aria)

    def test_walk_starts_and_ends_under_the_nodes(self):
        """The first and last frames match ARIA standing at each node."""
        frames = walk_frames(1, WORLD_1_IDS, 1, 3, self.art)
        self.assertEqual(frames[0], map_screen(1, WORLD_1_IDS, 1, self.art))
        self.assertEqual(frames[-1], map_screen(1, WORLD_1_IDS, 3, self.art))

    def test_walk_moves_a_few_pixels_per_frame(self):
        """From node 1 to node 3 is 32 pixels: 8 steps of 4, so 9 frames."""
        distance = aria_left(3, 5) - aria_left(1, 5)
        frames = walk_frames(1, WORLD_1_IDS, 1, 3, self.art)
        self.assertEqual(len(frames), distance // WALK_STEP + 1)

    def test_walk_can_go_left(self):
        """Walking back to an earlier node also works."""
        frames = walk_frames(1, WORLD_1_IDS, 3, 0, self.art)
        self.assertEqual(frames[-1], map_screen(1, WORLD_1_IDS, 0, self.art))

    def test_all_frames_have_the_same_height(self):
        """Frames are drawn over each other, so they must be the same size."""
        for frame in walk_frames(1, WORLD_1_IDS, 0, 4, self.art):
            self.assertEqual(len(frame.split("\n")), FRAME_LINES)


if __name__ == "__main__":
    unittest.main()
