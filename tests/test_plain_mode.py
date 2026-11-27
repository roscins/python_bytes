"""The plain mode (--plain, NO_COLOR) never writes escape codes or pixel art."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from engine.__main__ import run_game
from tests.helpers import make_boss_level, make_full_level

# Characters that only pictures use.
PICTURE_CHARACTERS = "\u2580\u2584\u2588\u2591"


def play(levels, lines):
    """Run the real game in plain mode with these levels and typed lines; return all it wrote."""
    typed = iter(lines)
    output = []
    with tempfile.TemporaryDirectory() as folder:
        with mock.patch("engine.__main__.load_levels", return_value=levels):
            run_game(save_path=Path(folder) / "save.json", workspace_root=Path(folder) / "work",
                     concepts_file=None, read_line=lambda prompt: next(typed),
                     write=output.append, plain=True, install_signals=False,
                     pause=lambda seconds: None)
    return "\n".join(output)


class TestPlainModeIsPlain(unittest.TestCase):
    """A whole session: map, level, level clear, boss fight."""

    def setUp(self):
        """Play a level and a boss from start to finish."""
        level = make_full_level()
        boss = make_boss_level()
        lines = ["1", "map", "play " + level.id]
        for wave in level.waves:
            text = wave.reference
            if wave.mode == "predict":
                text = wave.answer
            lines.append(":clear")
            lines.extend(text.strip().splitlines())
            lines.append(":submit")
        lines.extend(["map", "play " + boss.id, ":clear", 'print("x")', ":submit", ":clear"])
        lines.extend(boss.waves[0].reference.strip().splitlines())
        lines.extend([":submit", "map", ":quit"])
        self.output = play([level, boss], lines)

    def test_the_session_reaches_every_screen(self):
        """The level was cleared and the boss beaten, so those screens were shown."""
        self.assertIn("CLEARED", self.output)
        self.assertIn("BOSS HP [", self.output)
        self.assertIn("BOSS DEFEATED", self.output)
        self.assertIn("^Snek", self.output)

    def test_no_escape_codes(self):
        """Not one escape character is written."""
        self.assertNotIn("\x1b", self.output)

    def test_no_pixel_art_or_box_blocks(self):
        """No half blocks and no bar blocks are written."""
        for character in PICTURE_CHARACTERS:
            with self.subTest(character=character):
                self.assertNotIn(character, self.output)


if __name__ == "__main__":
    unittest.main()
