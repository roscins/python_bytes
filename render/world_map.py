"""Draw the world map: level nodes joined by a path, with Snek below them.

The map is a canvas (see render/canvas.py) 80 pixels wide, which is 80
terminal cells. Above the picture is a header and a line with the level
ids, so the player can see which node is which.

This module only knows level ids and numbers, not the engine's Level
objects, so the renderer does not depend on the engine.
"""

from pathlib import Path

from render.canvas import draw_line, new_canvas, paste
from render.palette import load_palette
from render.sprite import load_sprite, render_sprite

ART_FOLDER = Path(__file__).parent.parent / "art"

MAP_WIDTH = 80          # pixels, the same as terminal cells
NODE_SIZE = 8           # a node tile is 8 x 8 pixels
SNEK_SIZE = 16          # Snek is 16 x 16 pixels
NODE_TOP = 0            # nodes sit at the top of the picture
SNEK_TOP = NODE_SIZE    # Snek stands just below the nodes
MAP_HEIGHT = SNEK_TOP + SNEK_SIZE

PATH_CODE = "7"         # teal: the art guide's colour for map paths
PATH_THICKNESS = 2
PATH_TOP = NODE_TOP + (NODE_SIZE - PATH_THICKNESS) // 2

SLITHER_STEP = 4           # Snek moves this many pixels per frame
MAX_STARS = 3              # a level can earn up to 3 stars

# The worlds' names, from docs/plan.md.
WORLD_NAMES = {
    1: "Boot Sector",
    2: "Sensor Fields",
    3: "Data Vaults",
    4: "The Core",
    5: "Robot Foundry",
    6: "Assembly Line",
    7: "Data Streams",
    8: "Factory Mainframe",
}


class MapArt:
    """The palette and sprites the map is drawn with.

    Attributes:
        palette: the game's palette, from art/palette.txt.
        node: the sprite for an open level node.
        snek: the sprite for Snek.
        node_locked: the sprite for a locked level node (the open node's
            sprite if none is given).
    """

    def __init__(self, palette, node, snek, node_locked=None):
        """Remember the palette and the sprites."""
        self.palette = palette
        self.node = node
        self.snek = snek
        if node_locked is None:
            node_locked = node
        self.node_locked = node_locked


class MapStatus:
    """The player's progress, as the map shows it.

    The engine builds this from the game state, so the renderer never needs
    to know about the engine.

    Attributes:
        hud: the text at the right of the header, for example
            "XP 1240   ★ 7/12   COINS 35".
        locked: one True or False per level: is the level locked?
        stars: one number (0 to 3) per level: the stars earned there.
    """

    def __init__(self, hud, locked, stars):
        """Remember the HUD text, the locks and the stars."""
        self.hud = hud
        self.locked = list(locked)
        self.stars = list(stars)


def load_map_art(art_folder=ART_FOLDER):
    """Read the palette, the node tile and Snek from the art folder."""
    palette = load_palette(art_folder / "palette.txt")
    node = load_sprite(art_folder / "node-open.txt", palette)
    snek = load_sprite(art_folder / "snek-offline.txt", palette)
    node_locked = load_sprite(art_folder / "node-locked.txt", palette)
    return MapArt(palette, node, snek, node_locked)


def node_centre(index, node_count):
    """Return the column in the middle of node number `index` (counting from 0).

    The nodes share the width of the map equally, and each node sits in
    the middle of its share.
    """
    share = MAP_WIDTH // node_count
    return share * index + share // 2


def snek_left(index, node_count):
    """Return the column where Snek's left edge is, under node `index`.

    Snek is kept fully on the map, even under the first or last node.
    """
    left = node_centre(index, node_count) - SNEK_SIZE // 2
    if left < 0:
        left = 0
    if left > MAP_WIDTH - SNEK_SIZE:
        left = MAP_WIDTH - SNEK_SIZE
    return left


def header_line(world):
    """Return the map's title, for example "WORLD 1 · BOOT SECTOR"."""
    if world in WORLD_NAMES:
        return f"WORLD {world} · {WORLD_NAMES[world].upper()}"
    return f"WORLD {world}"


def centred_line(texts):
    """Return a line with each text centred over its node.

    `texts` has one text per node; an empty text leaves that place blank.
    """
    line = " " * MAP_WIDTH
    for index in range(len(texts)):
        text = texts[index]
        start = node_centre(index, len(texts)) - len(text) // 2
        if start < 0:
            start = 0
        line = line[:start] + text + line[start + len(text):]
    # A text may have made the line longer than the map; cut it back.
    return line[:MAP_WIDTH].rstrip()


def label_line(level_ids):
    """Return a line with each level id in brackets, centred over its node."""
    labels = []
    for level_id in level_ids:
        labels.append(f"[{level_id}]")
    return centred_line(labels)


def star_line(status):
    """Return a line with each open level's stars, like ★★☆, under its label."""
    texts = []
    for index in range(len(status.stars)):
        if status.locked[index]:
            texts.append("")
        else:
            stars = status.stars[index]
            texts.append("★" * stars + "☆" * (MAX_STARS - stars))
    return centred_line(texts)


def header_with_hud(world, hud):
    """Return the header with the HUD text pushed to the right edge of the map."""
    header = header_line(world)
    gap = MAP_WIDTH - len(header) - len(hud)
    if gap < 2:
        gap = 2
    return header + " " * gap + hud


def text_map(world, level_ids, snek_index, status=None):
    """Return the map as words only, for the plain mode: no pictures and no colour codes.

    The line under the ids shows each open level's stars, or "locked". Snek's
    node is marked on the line below. `snek_index` None means no Snek.
    """
    if status is None:
        lines = [header_line(world), "", label_line(level_ids)]
    else:
        lines = [header_with_hud(world, status.hud), "", label_line(level_ids)]
        texts = []
        for index in range(len(level_ids)):
            if status.locked[index]:
                texts.append("locked")
            else:
                stars = status.stars[index]
                texts.append("★" * stars + "☆" * (MAX_STARS - stars))
        lines.append(centred_line(texts))
    if snek_index is not None:
        markers = [""] * len(level_ids)
        markers[snek_index] = "^Snek"
        lines.append(centred_line(markers))
    return "\n".join(lines)


def map_frame(world, level_ids, snek_column, art, status=None):
    """Return one picture of the map as text, with Snek's left edge at `snek_column`.

    If `snek_column` is None, Snek is not drawn. With a MapStatus, the
    header shows the HUD, locked levels get the locked tile, and each open
    level's stars are shown under its label.
    """
    canvas = new_canvas(MAP_WIDTH, MAP_HEIGHT)
    node_count = len(level_ids)
    if node_count > 1:
        first = node_centre(0, node_count)
        last = node_centre(node_count - 1, node_count)
        draw_line(canvas, PATH_CODE, first, last, PATH_TOP, PATH_THICKNESS)
    for index in range(node_count):
        left = node_centre(index, node_count) - NODE_SIZE // 2
        node = art.node
        if status is not None and status.locked[index]:
            node = art.node_locked
        paste(canvas, node, left, NODE_TOP)
    if snek_column is not None:
        paste(canvas, art.snek, snek_column, SNEK_TOP)

    if status is None:
        lines = [header_line(world), "", label_line(level_ids)]
    else:
        lines = [header_with_hud(world, status.hud), "", label_line(level_ids), star_line(status)]
    lines.extend(render_sprite(canvas, art.palette))
    return "\n".join(lines)


def map_screen(world, level_ids, snek_index, art, status=None):
    """Return the map with Snek under level number `snek_index`, or None for no Snek."""
    if snek_index is None:
        return map_frame(world, level_ids, None, art, status)
    return map_frame(world, level_ids, snek_left(snek_index, len(level_ids)), art, status)


def slither_frames(world, level_ids, from_index, to_index, art, status=None):
    """Return the frames of Snek slithering from one node to another.

    The first frame has Snek under node `from_index` and the last under
    node `to_index`. In between, she moves SLITHER_STEP pixels per frame.
    """
    start = snek_left(from_index, len(level_ids))
    end = snek_left(to_index, len(level_ids))
    if end >= start:
        step = SLITHER_STEP
    else:
        step = -SLITHER_STEP
    columns = list(range(start, end, step))
    columns.append(end)
    frames = []
    for column in columns:
        frames.append(map_frame(world, level_ids, column, art, status))
    return frames
