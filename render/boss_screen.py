"""Draw the boss fight screen: the boss, the lives, the health bar and the timer.

It follows the mock-up in docs/plan.md:

    BOSS 1 · THE CORRUPTED BOOTLOADER              LIVES ♥ ♥ ♡
    (pixel picture: a heart per life on the left, the boss in the middle)
    BOSS HP [██████████░░░░░░░░░░]  5 of 10 hidden tests still failing
    TIME 07:42

The boss's health is made of its hidden tests: each test the player's code
passes knocks off a piece of the bar.
"""

from pathlib import Path

from render.canvas import new_canvas, paste
from render.palette import load_palette
from render.sprite import load_sprite, render_sprite

ART_FOLDER = Path(__file__).parent.parent / "art"

SCREEN_WIDTH = 80
BOSS_SIZE = 16
ICON_SIZE = 8
PICTURE_HEIGHT = BOSS_SIZE
HEART_GAP = 2           # pixels between two hearts
BAR_BLOCKS = 20         # the health bar is 20 characters wide
FULL_BLOCK = "█"
EMPTY_BLOCK = "░"
FULL_HEART = "♥"
EMPTY_HEART = "♡"
LIVES_TOTAL = 3


class BossArt:
    """The palette and sprites the boss screen is drawn with.

    Attributes:
        palette: the game's palette.
        boss: the boss's sprite.
        heart: the sprite for a life the player still has.
        heart_empty: the sprite for a lost life.
    """

    def __init__(self, palette, boss, heart, heart_empty):
        """Remember the palette and the sprites."""
        self.palette = palette
        self.boss = boss
        self.heart = heart
        self.heart_empty = heart_empty


def load_boss_art(sprite_name, art_folder=ART_FOLDER):
    """Read the palette, the hearts and the boss sprite `sprite_name` from the art folder."""
    palette = load_palette(art_folder / "palette.txt")
    boss = load_sprite(art_folder / f"{sprite_name}.txt", palette)
    heart = load_sprite(art_folder / "heart-full.txt", palette)
    heart_empty = load_sprite(art_folder / "heart-empty.txt", palette)
    return BossArt(palette, boss, heart, heart_empty)


def boss_name(level_id):
    """Return a boss level's id as a name, for example "boss-1" gives "BOSS 1"."""
    return level_id.upper().replace("-", " ")


def lives_text(lives_left):
    """Return the lives as text hearts, for example "♥ ♥ ♡" for 2 of 3."""
    hearts = []
    for index in range(LIVES_TOTAL):
        if index < lives_left:
            hearts.append(FULL_HEART)
        else:
            hearts.append(EMPTY_HEART)
    return " ".join(hearts)


def header(level_id, title, lives_left):
    """Return the header: the boss's name on the left, the lives on the right."""
    left = f"{boss_name(level_id)} · {title.upper()}"
    right = f"LIVES {lives_text(lives_left)}"
    gap = SCREEN_WIDTH - len(left) - len(right)
    if gap < 2:
        gap = 2
    return left + " " * gap + right


def health_bar(hp_left, hp_total):
    """Return the health bar line, for example "BOSS HP [████░░░░]  2 of 4 hidden tests ..."."""
    filled = 0
    if hp_total > 0:
        filled = round(BAR_BLOCKS * hp_left / hp_total)
    bar = FULL_BLOCK * filled + EMPTY_BLOCK * (BAR_BLOCKS - filled)
    tests_word = "tests"
    if hp_total == 1:
        tests_word = "test"
    return f"BOSS HP [{bar}]  {hp_left} of {hp_total} hidden {tests_word} still failing"


def timer_text(seconds_left):
    """Return the time left as "TIME 07:42"; never less than 00:00."""
    seconds = int(seconds_left)
    if seconds < 0:
        seconds = 0
    minutes = seconds // 60
    seconds = seconds % 60
    return f"TIME {minutes:02d}:{seconds:02d}"


def boss_picture(lives_left, art):
    """Return the pixel picture as terminal lines: hearts on the left, the boss in the middle."""
    canvas = new_canvas(SCREEN_WIDTH, PICTURE_HEIGHT)
    for index in range(LIVES_TOTAL):
        heart = art.heart_empty
        if index < lives_left:
            heart = art.heart
        paste(canvas, heart, index * (ICON_SIZE + HEART_GAP), (PICTURE_HEIGHT - ICON_SIZE) // 2)
    paste(canvas, art.boss, (SCREEN_WIDTH - BOSS_SIZE) // 2, 0)
    return render_sprite(canvas, art.palette)


def boss_screen(level_id, title, hp_left, hp_total, lives_left, seconds_left, art):
    """Return the whole boss screen as text."""
    lines = [header(level_id, title, lives_left)]
    lines.extend(boss_picture(lives_left, art))
    lines.append(health_bar(hp_left, hp_total))
    lines.append(timer_text(seconds_left))
    return "\n".join(lines)


def hp_drain_frames(level_id, title, hp_from, hp_to, hp_total, lives_left, seconds_left, art):
    """Return frames of the health bar going from `hp_from` down to `hp_to`, one test at a time.

    If the health did not go down, there is just one frame.
    """
    frames = []
    hp = hp_from
    while hp > hp_to:
        frames.append(boss_screen(level_id, title, hp, hp_total, lives_left, seconds_left, art))
        hp = hp - 1
    frames.append(boss_screen(level_id, title, hp_to, hp_total, lives_left, seconds_left, art))
    return frames
