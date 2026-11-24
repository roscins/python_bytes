# Art style guide

All pixel art in Python Bytes uses one 16-colour palette and one sprite format, so the game looks consistent and the renderer can draw every sprite.

## Palette

Each colour has a one-character code (`0`–`9`, `a`–`f`). `.` always means transparent and is never a colour.

| Code | Name | Hex | Use |
| --- | --- | --- | --- |
| 0 | Void | `#0d0d1a` | Background, deepest shadow |
| 1 | Navy | `#1b2a4a` | Dark details, mouths, gaps |
| 2 | Slate | `#3e4c66` | Outlines |
| 3 | Steel | `#8a93a6` | Metal, ARIA's body |
| 4 | Silver | `#d7dce6` | Highlights, ARIA's face |
| 5 | White | `#ffffff` | Sparkles, text highlights |
| 6 | Cyan | `#29c5f6` | ARIA active (eyes, lights), player |
| 7 | Teal | `#1a8a8a` | Map paths, water, screens |
| 8 | Green | `#4cd964` | Success, level clear, full health |
| 9 | Moss | `#2a7a3a` | Green shadows, plants |
| a | Gold | `#ffd23f` | Stars, coins, XP |
| b | Orange | `#ff8c1a` | Warnings, sparks |
| c | Red | `#e63946` | Danger, bosses, lives |
| d | Maroon | `#8a1c2b` | Red shadows, status lights off |
| e | Violet | `#9b5de5` | Codex, power-ups |
| f | Pink | `#f78fb3` | Rare accents |

Colour meanings are fixed: gold is always a reward, red is always danger, cyan is always ARIA or the player. Don't use them for anything else.

`art/palette.txt` must match this table.

## Sprite format

- One text file per sprite in `art/`, named `<subject>-<state>.txt`, for example `art/aria-offline.txt`.
- One character per pixel, using the palette codes above. `.` is transparent.
- Every row has the same length.
- The row count should be even (two pixels per terminal cell). The renderer pads an odd sprite with one transparent row, but don't rely on it.
- No other characters, no comments inside sprite files.

## Sizes

| What | Size (pixels) | Terminal cells |
| --- | --- | --- |
| ARIA, bosses | 16 × 16 | 16 × 8 |
| Icons (star, coin, heart) | 8 × 8 | 8 × 4 |
| Map tiles | 8 × 8 | 8 × 4 |
| Full screen | 80 × 48 | 80 × 24 |

## Style rules

1. Outline characters and objects in Slate (`2`), not black.
2. Light comes from the top left: highlights top left, shadows bottom right.
3. At most 4 colours plus outline in one 16 × 16 sprite. Fewer colours read better at this size.
4. Every sprite must be recognisable in plain-ASCII mode by its shape alone. Test it.

## Reference sprite: ARIA, offline (16 × 16)

Eyes and status light are dark (`2` and `d`); in the "online" state they turn cyan (`6`) and green (`8`).

```
.......33.......
.......22.......
...2222222222...
..233333333332..
..234444444432..
..234224422432..
..234224422432..
..234444444432..
..234411114432..
..233333333332..
...2222222222...
.....222222.....
...2333333332...
..23311dd11332..
..233333333332..
...22......22...
```

Save it as `art/aria-offline.txt` and check it with `python -m render art/aria-offline.txt`.
