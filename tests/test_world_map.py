"""Tests for render/world_map.py."""

import re
import unittest

from render.world_map import (
    MapStatus,
    SNEK_SIZE,
    MAP_HEIGHT,
    MAP_WIDTH,
    SLITHER_STEP,
    WORLD_NAMES,
    snek_left,
    header_line,
    label_line,
    load_map_art,
    map_frame,
    map_screen,
    node_centre,
    slither_frames,
)

WORLD_1_IDS = ["1-1", "1-2", "1-3", "1-4", "1-5", "boss-1"]
NODE_COUNT = len(WORLD_1_IDS)

# Header, blank line, label line, then two pixel rows per terminal line.
FRAME_LINES = 3 + MAP_HEIGHT // 2


def without_colours(text):
    """Return `text` without ANSI escape codes, as the player would read it."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


class TestLayout(unittest.TestCase):
    """Check where nodes, labels and Snek go."""

    def test_nodes_are_spread_evenly(self):
        """Five nodes share 80 columns, 16 each, centred in their share."""
        centres = []
        for index in range(5):
            centres.append(node_centre(index, 5))
        self.assertEqual(centres, [8, 24, 40, 56, 72])

    def test_world_one_has_six_nodes_that_all_fit(self):
        """Five levels and a boss: 13 columns each, and every label fits in its share."""
        centres = []
        for index in range(6):
            centres.append(node_centre(index, 6))
        self.assertEqual(centres, [6, 19, 32, 45, 58, 71])
        labels = label_line(WORLD_1_IDS)
        for level_id in WORLD_1_IDS:
            self.assertIn(f"[{level_id}]", labels)

    def test_one_node_is_in_the_middle(self):
        """A world with one level has its node in the middle."""
        self.assertEqual(node_centre(0, 1), MAP_WIDTH // 2)

    def test_snek_stays_on_the_map(self):
        """Snek is never drawn past the left or right edge."""
        for count in range(1, 8):
            for index in range(count):
                left = snek_left(index, count)
                self.assertGreaterEqual(left, 0)
                self.assertLessEqual(left + SNEK_SIZE, MAP_WIDTH)

    def test_header_names_the_world(self):
        """The header shows the world's number and name."""
        self.assertEqual(header_line(1), "WORLD 1 · BOOT SECTOR")
        self.assertEqual(len(WORLD_NAMES), 8)
        self.assertEqual(header_line(99), "WORLD 99")

    def test_labels_are_centred_over_the_nodes(self):
        """Each label's middle is at its node's centre."""
        line = label_line(WORLD_1_IDS)
        start = line.index("[1-3]")
        self.assertEqual(start + len("[1-3]") // 2, node_centre(2, NODE_COUNT))
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

    def test_map_without_snek_differs_from_map_with_snek(self):
        """With snek_index None, Snek is left out."""
        with_snek = map_screen(1, WORLD_1_IDS, 0, self.art)
        without_snek = map_screen(1, WORLD_1_IDS, None, self.art)
        self.assertNotEqual(with_snek, without_snek)

    def test_slither_starts_and_ends_under_the_nodes(self):
        """The first and last frames match Snek standing at each node."""
        frames = slither_frames(1, WORLD_1_IDS, 1, 3, self.art)
        self.assertEqual(frames[0], map_screen(1, WORLD_1_IDS, 1, self.art))
        self.assertEqual(frames[-1], map_screen(1, WORLD_1_IDS, 3, self.art))

    def test_slither_moves_a_few_pixels_per_frame(self):
        """Snek moves 4 pixels per frame; a shorter last step still gets a frame."""
        distance = snek_left(3, NODE_COUNT) - snek_left(1, NODE_COUNT)
        steps = (distance + SLITHER_STEP - 1) // SLITHER_STEP
        frames = slither_frames(1, WORLD_1_IDS, 1, 3, self.art)
        self.assertEqual(len(frames), steps + 1)

    def test_slither_can_go_left(self):
        """Slithering back to an earlier node also works."""
        frames = slither_frames(1, WORLD_1_IDS, 3, 0, self.art)
        self.assertEqual(frames[-1], map_screen(1, WORLD_1_IDS, 0, self.art))

    def test_all_frames_have_the_same_height(self):
        """Frames are drawn over each other, so they must be the same size."""
        for frame in slither_frames(1, WORLD_1_IDS, 0, 4, self.art):
            self.assertEqual(len(frame.split("\n")), FRAME_LINES)


class TestMapStatus(unittest.TestCase):
    """Check the HUD, stars and locked nodes drawn from a MapStatus."""

    def setUp(self):
        """Load the real art and make a status: 1-1 has 2 stars, 1-3 on are locked."""
        self.art = load_map_art()
        self.status = MapStatus("XP 1240   ★ 7/12   COINS 35",
                                [False, False, True, True, True, True], [2, 0, 0, 0, 0, 0])

    def test_header_has_the_hud_at_the_right(self):
        """The HUD ends at the right edge of the 80-column map."""
        header = map_frame(1, WORLD_1_IDS, None, self.art, self.status).split("\n")[0]
        self.assertTrue(header.startswith("WORLD 1 · BOOT SECTOR"))
        self.assertTrue(header.endswith("XP 1240   ★ 7/12   COINS 35"))
        self.assertEqual(len(header), MAP_WIDTH)

    def test_stars_under_open_levels_only(self):
        """Open levels show their stars under their label; locked ones show none."""
        star_row = map_frame(1, WORLD_1_IDS, None, self.art, self.status).split("\n")[3]
        self.assertEqual(star_row.count("★"), 2)
        self.assertEqual(star_row.count("☆"), 1 + 3)
        start = star_row.index("★★☆")
        self.assertEqual(start + 1, node_centre(0, NODE_COUNT))

    def test_locked_nodes_use_the_locked_tile(self):
        """With locks, the picture differs from the same map without them."""
        open_status = MapStatus("", [False] * NODE_COUNT, [0] * NODE_COUNT)
        locked = map_frame(1, WORLD_1_IDS, None, self.art, self.status).split("\n")[4:]
        unlocked = map_frame(1, WORLD_1_IDS, None, self.art, open_status).split("\n")[4:]
        self.assertNotEqual(locked, unlocked)

    def test_frames_with_status_have_one_more_line(self):
        """The star row adds one line, the same in every slither frame."""
        for frame in slither_frames(1, WORLD_1_IDS, 0, 1, self.art, self.status):
            self.assertEqual(len(frame.split("\n")), FRAME_LINES + 1)


if __name__ == "__main__":
    unittest.main()
