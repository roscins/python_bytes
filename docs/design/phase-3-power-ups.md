# Phase 3 design: World 1 power-ups

**Status: proposed. No code until this is approved.**

A power-up is a small tool that shows the idea a level has just taught. It is
earned by clearing the level and stays for the rest of the game.

## Rules for every power-up

- **Where:** at the map as `calc 2 + 3 * 4`; inside a wave with a colon,
  `:calc 2 + 3 * 4`. Before its level is cleared it answers
  `Clear 1-3 to earn calc.`
- **Free.** No coins, and no effect on score, stars or combo.
- **Predict waves and boss fights:** refused in a predict wave, like `:run`.
  Allowed in a boss fight, because it shows nothing about the hidden tests.
- **Your own names still work.** Today a command name wins over Python, so
  `read = 5` would run the command. A line where the name is followed by `=`
  (or `+=` and so on) is Python.
- **Plain mode:** every drawing is ordinary characters, with no colour codes.
- **80 x 24:** each drawing fits the screen; longer ones are paged.
- **Safe:** nothing is passed to `eval` in the game process. Code runs in the
  separate runner, as player code does now.

## 1-1 `status`: what does this line do?

Concepts: `print()`, string literals, comments.

    > status print("# 1 ready")  # start-up
    print("# 1 ready")  # start-up
    ^^^^^                             call: show something
          ^^^^^^^^^^^                 string: this # is only text
                        ^^^^^^^^^^    comment: Python skips it
    SCREEN: # 1 ready

## 1-2 `memory`: names and the values they point to

At the map it draws the quick console's variables; in a wave it runs the code
you have typed and draws what is left at the end.

    > memory
    NAMES              VALUES
    power     -------> [ 9 ]  int
    backup    -------> [ 5 ]  int
    unit_name --+----> [ "Snek" ]  str
    twin      --+

Two names share one box when they are the very same object (`is`). The same
drawing will show aliasing in 3-4, so it is built to draw several names per
box from the start.

## 1-3 `calc`: the order of evaluation

One step per line, the part about to be worked out underlined:

    > calc (74 - 2) * 3 + 10 // 4
    (74 - 2) * 3 + 10 // 4
     ~~~~~~
    72 * 3 + 10 // 4
    ~~~~~~
    216 + 10 // 4
          ~~~~~~~
    216 + 2
    ~~~~~~~
    218

It knows numbers, text, `+ - * / // % **`, brackets, `int float str round`
and the variables of the quick console or wave. It walks the syntax tree
itself, so it shows Python's real order. Huge powers are refused.

## 1-4 `approx`: the number a float really stores

    > approx 0.1 + 0.2
    you see      0.30000000000000004
    stored       0.3000000000000000444089209850062616169452667236328125

    > approx 0.1 + 0.2, 0.3
    left stored  0.3000000000000000444089209850062616169452667236328125
    right stored 0.299999999999999988897769753748434595763683319091796875
                 same up to here: 0.3000000000000000
    ==           False
    math.isclose True

The exact digits come from `decimal.Decimal(x)`.

## 1-5 `read`: the index under every character

    > read "09:42|E07" [0:5]
    char    0  9  :  4  2  |  E  0  7
    index   0  1  2  3  4  5  6  7  8
    back   -9 -8 -7 -6 -5 -4 -3 -2 -1
    [0:5]   ^  ^  ^  ^  ^
    gives   '09:42'      len = 9

The slice is optional. A variable name works in place of the text. Spaces are
shown as `·` (`_` in plain mode). Long text wraps in blocks of 20.

## Build plan

Small PRs, each with tests:

1. The shared part (unlocking, routing, help, refusals) with `read`.
2. `memory`.
3. `calc`.
4. `approx` and `status`.

`engine/powerups/` holds one module per tool; `render/` holds the drawings.
The level-clear screen already announces the new command. `help` lists the
ones you have earned.

## Please decide

1. **`status`.** Your list did not cover 1-1. Is the line explainer above
   right, or should `status` be a progress report instead?
2. **Shared boxes in `memory`.** Proposed: share when the objects are the same
   (`is`). It is the truth, and shows that `backup = power` copies no value.
   The catch: Python reuses small numbers and short texts, so `a = 5` and
   `b = 5`, typed separately, also share a box. The tool would then add:
   `Python reuses small values; this is safe because they cannot change.`
   The other choice is to share only lists and other changeable values, which
   hides binding until 3-4.
3. **Power-ups in boss fights:** allowed, as proposed?
4. **A way round predict waves.** You can type `map` and then run the code in
   the quick console, which is already possible today. Leave it?
