"""Draw a sprite file in the terminal.

Run it with:  python -m render art/aria-offline.txt
"""

import os
import sys
from pathlib import Path

from render.palette import load_palette
from render.sprite import load_sprite, render_sprite

# The palette file, found from this file's folder so it works from anywhere.
PALETTE_PATH = Path(__file__).parent.parent / "art" / "palette.txt"


def main(arguments):
    """Draw the sprite file named in `arguments` and return an exit code."""
    if len(arguments) != 1:
        print("Usage: python -m render <sprite file>, for example art/aria-offline.txt")
        return 2
    if os.name == "nt":
        os.system("")  # switches on ANSI colours in older Windows consoles
    # OSError means a file is missing. ValueError means a file is broken
    # (SpriteError is a kind of ValueError, so it is caught here too).
    try:
        palette = load_palette(PALETTE_PATH)
        sprite = load_sprite(arguments[0], palette)
    except (OSError, ValueError) as error:
        print(f"Cannot draw the sprite: {error}")
        return 1
    for line in render_sprite(sprite, palette):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
