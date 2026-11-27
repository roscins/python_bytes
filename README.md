# python_bytes
A python learning game with basic and advanced levels

## Play

You need Python 3.12 or newer and a terminal. From this folder:

    python play.py

That is all: the game opens full screen with a title (press Enter), then CONTINUE,
NEW GAME or QUIT. Menus and the map are worked with the arrow keys and Enter. It saves after every line you type, so closing the window never
loses your work, and your terminal comes back as it was when you leave.

Needs a window of at least 80 x 24. `python play.py --plain` is the plain look (no
colour, no animation, no full screen, ASCII boxes): use it with a screen reader, in a
log, or when something looks wrong. It is also used when the output is not a
terminal, and when the `NO_COLOR` variable is set.
Optional: `pip install -e .` adds a `python-bytes` command that does the same.
Your save is `~/.python-bytes/save.json` (`--save PATH` changes it).

Inside a level you write code in an editor: arrows move, Ctrl-S submits, Ctrl-R
runs, and Down from the last line reaches the buttons. Ctrl-G lists every key, and
Ctrl-E takes a typed word (a power-up, `stats`, a line of Python). On the map, press
`:` to type a command. A level is cleared when every wave is passed.

In `--plain` you type code line by line, and commands start with a colon (`:submit`,
`:run`, `:undo`, `:edit`, `:help` ...).
