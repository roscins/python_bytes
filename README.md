# python_bytes
A python learning game with basic and advanced levels

## Play

You need Python 3.12 or newer and a terminal. From this folder:

    python play.py

That is all: the title screen asks CONTINUE, NEW GAME or QUIT. The game saves
after every line you type, so closing the window never loses your work.

Optional: `pip install -e .` adds a `python-bytes` command that does the same.
`python play.py --plain` uses plain text without box characters.
Your save is `~/.python-bytes/save.json` (`--save PATH` changes it).

Inside a level you type your code line by line; commands start with a colon
(`:submit`, `:run`, `:show`, `:undo`, `:edit`, `:help` ...). Outside a level, any
line of Python you type just runs (`print("hi")`, `x = 5`, a `for` loop), like in
the Python console. A level is cleared when every wave is passed.
