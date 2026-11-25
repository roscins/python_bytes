Python Bytes: Development Plan for a Task-Based Python Learning Game
Nov 24, 2026 · @Aleksander
Overview
Python Bytes (working title: small bites of Python, from a python that bites) is an arcade-style, pixel-art terminal game that teaches Python across 8 worlds, 40 levels and 8 boss fights. Each level teaches a few concepts, then the player clears coding waves to earn XP, stars and a new power-up before the next level on the map opens.
• Basic tier (Worlds 1–4) covers the learning outcomes of OsloMet's Introduction to Python Programming: variables, data types, strings and numbers, conditionals, loops, functions, lists, tuples, sets, dictionaries, exception handling and file I/O.
• Advanced tier (Worlds 5–8) covers Advanced Python Programming for Engineers: object-oriented and functional programming, choosing between them, robust design, debugging, reading other people's code and code review.
• Audience: first-year engineering students with no prior programming, who want real understanding, not memorised patterns.
• Format: a terminal game written in Python, drawn with coloured Unicode block characters so it looks like an 8-bit console game. The game's own source code becomes level material in World 7.
• Story frame: the player is a new technician in an abandoned robotics lab. The lab robot Snek, a forest-green robot snake, is offline; each world restores part of her, and from World 5 the player rebuilds the whole automated factory around her.
Progression model: worlds, levels and bosses
The game is a classic arcade map: the player guides Snek along a pixel path from level to level, and each world ends in a boss fight that tests everything in that world. A level opens only when the one before it is cleared.
Tier
World
Theme
Levels
Boss
Basic
1
Boot Sector
1-1 to 1-5
Boss 1: The Corrupted Bootloader
Basic
2
Sensor Fields
2-1 to 2-5
Boss 2: The Night Patrol
Basic
3
Data Vaults
3-1 to 3-5
Boss 3: The Storage Auditor
Basic
4
The Core
4-1 to 4-5
Boss 4: Systems Online (tier final)
Advanced
5
Robot Foundry
5-1 to 5-5
Boss 5: The First Robot
Advanced
6
Assembly Line
6-1 to 6-5
Boss 6: The Production Line
Advanced
7
Data Streams
7-1 to 7-5
Boss 7: The Legacy Machine
Advanced
8
Factory Mainframe
8-1 to 8-5
Boss 8: The Factory Wakes (final)
Inside a level. Every level runs the same short loop, like stages in a shoot-'em-up:
1.  Cutscene – a short story scene with working code in it. The new syntax is seen in action before it is explained.
2.  Tips – a few one-line explanations of the new syntax, saved to the player's Codex.
3.  Wave 1 – Fill-in: complete missing parts of given code.
4.  Wave 2 – Build: write a program or function from a short mission brief.
5.  Wave 3 – Debug: predict the output of code, or find and fix the bug.
6.  Level clear – stars, coins, and a power-up command.
Bosses. A boss has a health bar made of hidden tests: every test the player's code passes knocks off one block of health. Bosses introduce no new concepts; they combine the whole world, add a time limit, and give the player 3 tries (one used up by each failed submission). Using up all tries restarts the fight, not the world.
What I keep from Lingua Latina per se Illustrata. Only the core idea: strict cumulative progression. A level may use only what earlier levels taught plus 2–4 new things, and old concepts keep returning in new combinations. An automatic checker enforces this (see Technical architecture). What each level teaches is decided in docs/curriculum.md and levels/concepts.toml; the tables in this plan are a summary of them.
Example cutscene from Level 1-2, where variables are new and print() is already known:
# >> Snek's memory banks flicker. Two empty cells light up.
name = "Snek"
battery = 12
print(name)      # screen: Snek
print(battery)   # screen: 12
# >> You patch in more power...
battery = 13
print(battery)   # screen: 13
# >> Snek: "MEMORY CELL UPDATED. THANK YOU, TECHNICIAN."
Learning outcomes mapped to levels
Every learning outcome in the two course descriptions is taught in at least one level and tested in at least one wave or boss. The tables are the coverage contract: a level may not be removed without moving its outcome elsewhere.
Basic tier – Introduction to Python Programming
Outcome (from course description)
Taught in
Tested by
Variables, data types, basic syntax
1-1, 1-2
Waves in 1-1 and 1-2, Boss 1
Manipulate numbers and strings
1-3, 1-4, 1-5, 2-1
Wave 2 in 1-3 to 2-1, Boss 1
Conditional statements
2-2
Wave 2 in 2-2, Boss 2
Loops (for, while)
2-3, 2-4
Wave 2 in 2-3 and 2-4, Boss 2
Define and call functions, pass arguments
3-2, 3-3
Wave 2 in 3-2 and 3-3, Boss 3
Lists, tuples, sets, dictionaries
3-1, 3-5, 4-1
Multiple-choice "choose the structure" wave in 4-1, Bosses 3 and 4
Algorithmic thinking
2-2 onwards, 2-5
Plan-first missions, Boss 2, Boss 4
Best practice: indentation, naming, documentation
1-1, 1-2, 3-2 (then continuous)
Code-quality score on every Wave 2
Error handling with try/except
4-2
Wave 2 in 4-2, Boss 4
File input and output
4-3
Wave 2 in 4-3, Boss 4
Break real problems into sub-tasks
3-3, 4-3, Boss 4
Boss 4, phase 2 (project)
Collaborate, review code, give feedback
4-4
Review of a provided solution in 4-4 and Boss 4
Advanced tier – Advanced Python Programming for Engineers
Outcome (from course description)
Taught in
Tested by
Overview of Python for moderate real problems
5-1, Boss 8
Boss 8
OOP: class, object, method, inheritance, polymorphism, encapsulation
5-2 to 6-2
Wave 2 in 5-2 to 6-2, Bosses 5 and 6
Functional vs object-oriented features, when to use each
7-1, 7-2, 7-3
Dual-solution mission in 7-3
Robust, reliable programs with good OO design
5-3, 6-3, 8-1
Design mission in 8-1, Boss 8
Alternative solutions, weigh pros and cons
7-3, 8-1
Written trade-off notes in 7-3 and 8-1
Clear and efficient programs
7-1, 8-2, 8-3
Speed-run missions in 8-2
Find and fix errors in own programs
6-3, 7-4
Bug-hunt waves in 7-4
Understand others' programs to debug and change them
7-5
Legacy-code mission in 7-5, Boss 7
Conduct code review, document errors, suggest improvements
7-5, Boss 8
Review report in 7-5, review in Boss 8
Critically assess programming approaches
6-2, 7-3, 8-1
Trade-off notes, Boss 7
Game design: level loop, rewards and scoring
Every level is a closed loop: watch, practise, score, and only then move on. A player who scores below 70 % spends coins on hints if they want, and replays only the waves they failed.
Replaying only failed waves keeps retries short; the 70 % gate stops players carrying gaps into later levels that build on them.
Arcade rewards
Reward
How it is earned
What it does
Stars (1–3 per level)
1 star ≥ 70 %, 2 stars ≥ 85 %, 3 stars = 100 % with no hints
A boss door opens only when the world's levels hold enough stars (proposal: 2 of 3 on average)
Coins
First-try passes and full code-quality scores
Buy hints in the shop
Power-ups
Clearing a level
A new terminal command built on the concept just learned (calc after 1-3, inventory after 3-1)
Tries
3 per boss fight
Used up by each failed boss submission; with none left the fight restarts
Combo
Clearing waves first try in a row
A streak counter in the HUD that flashes when it goes up
Badges
Special feats, for example "No Hints in World 1" or "Clean Coder" (full quality score on 10 levels)
Shown on the player's profile screen
Power-ups are the main reward: the player can actually use what they just learned as a tool in the game. Commands available from the start (with a colon in front while coding): help, map, play, submit, hint, codex, stats, quit.
Level score
Component
Share of level score
How it is graded
Wave 1 – Fill-in
20 %
Automatic tests on the completed code
Wave 2 – Build
50 %
Hidden test cases plus required-structure checks (for example "uses a while loop")
Wave 3 – Debug
15 %
Exact-match predicted output, multiple choice, or the line holding the bug
Code quality
15 %
Style checks on Wave 2: naming, indentation, comments, docstrings
• Waves can be replayed without limit; the best attempt counts.
• Three hint levels per wave, paid in coins: a nudge (cheap), an approach outline (medium), a partial solution (expensive, and it caps that level at 2 stars).
• Written answers in World 7 and 8 (trade-off notes, review reports) are graded against a published rubric, by self-assessment or a classmate.
• A local high-score table is opt-in, so nobody is ranked against classmates without choosing it.
Tier grade. Levels count 50 %, Bosses 1–3 (or 5–7) 20 % and the tier's final boss 30 %. The game shows the result on an A–F scale as a proposal: A ≥ 90 %, B ≥ 80 %, C ≥ 60 %, D ≥ 50 %, E ≥ 40 %, F below 40 %. These bands are my own choice for motivation and do not represent OsloMet's grading.
Look and feel: pixel art in the terminal
The game runs in an ordinary terminal but looks like an 8-bit console game. The trick is the Unicode half-block character ▀: with a different foreground and background colour, each character cell shows two stacked pixels, so an 80 × 24 terminal becomes an 80 × 48 pixel screen.
• Palette: one fixed 16-colour palette of my own, used for every sprite, so the game looks consistent.
• Sprites: Snek (16 × 16 pixels) in several states (offline, booting, happy, damaged), one sprite per boss, small icons for stars, coins and hearts.
• Screens: title screen, world map, level intro card, code-wave screen, boss fight screen, level-clear screen, Codex, shop, stats.
• Animation: a few frames only (Snek slithering on the map, a boss health bar draining, a level-clear flash), drawn by redrawing the screen.
• Fallbacks: a plain-ASCII mode for terminals without colour, and an accessible mode with no flashing and screen-reader-friendly text.
Rough mock-up of the world map and a boss fight (pixel art shown as text):
 WORLD 1 · BOOT SECTOR                       ★ 7/12   COINS 35

   [1-1]★★★ ══ [1-2]★★☆ ══ [1-3]★☆☆ ══ [1-4] ··· ══ [1-5] ··· ══ [BOSS 1]
                               ▲
                              Snek

 > play 1-3    > codex    > shop    > stats

 BOSS 1 · THE CORRUPTED BOOTLOADER              LIVES ♥ ♥ ♡
 BOSS HP [██████████░░░░░░░░░░]  5 of 10 hidden tests still failing
 TIME 07:42
Basic tier: Worlds 1–4
The Basic tier restores Snek one subsystem at a time, from her voice in Level 1-1 to a full log-analysis routine in Boss 4. Each row lists only what is new; everything earlier is assumed and keeps coming back.
Level
Title
New concepts
Example Wave 2 mission
Power-up
World 1
Boot Sector



1-1
Hello, Terminal
print(), string literals, comments
Print a three-line start-up message.
status
1-2
Memory Cells
variables and assignment, the types int, float, str and bool, type(), snake_case names
Store serial number, battery level and online state; rebind one name and print all.
memory
1-3
Power Calculations
arithmetic operators and precedence, //, % and **, converting between int, float and str, round()
Compute remaining run-time in hours and minutes from capacity and power draw.
calc
1-4
Floating Truth
why 0.1 + 0.2 != 0.3, comparison operators, absolute and relative tolerance, math.isclose() and abs()
Compare readings with absolute and relative tolerance; explain why == failed.
approx
1-5
Corrupted Logs
indexing and slicing, len(), string methods, f-strings with format specs
Extract timestamp, code and value from a damaged log line; print an aligned report.
read
Boss 1
The Corrupted Bootloader
Everything in World 1
Repair a scrambled boot report under time pressure.
–
World 2
Sensor Fields



2-1
Listening
input(), converting input to numbers, input, process, output
Ask for two readings and print the calibrated offset to two decimals.
talk
2-2
Decisions
and, or, not, if / elif / else, truthiness and bool(), planning in comments first
Classify a temperature as OK, WARNING or CRITICAL with hysteresis.
alarm
2-3
Charging
while loops, sentinel values, break and continue, augmented assignment
Charge in 5 % steps until full or until the user types stop.
charge
2-4
Grid Scan
for loops and range(), looping over strings, accumulators, nested loops
Scan a 5 x 5 grid string and print the coordinates of every obstacle.
scan
2-5
Finding the Signal
exhaustive enumeration and guess-and-check, bisection search, stopping on a float tolerance, counting iterations
Find a square root by enumeration, then by bisection; compare iteration counts.
seek
Boss 2
The Night Patrol
Everything in Worlds 1–2
Patrol simulation combining input, decisions, loops and a bisection search.
–
World 3
Data Vaults



3-1
Inventory
lists: literals, indexing and slicing, adding, removing and sorting items, searching with in, lists of lists
Add, remove, search and sort parts; keep a list of [name, count] pairs.
inventory
3-2
Subroutines I
def, parameters and return, None, docstrings, local scope
Write celsius_to_kelvin() and distance() with docstrings; reuse them in a loop.
define
3-3
Subroutines II
default and keyword arguments, returning several values, min, max, sum and sorted, decomposition, specifications and Newton-Raphson
Split it into specified functions; make bisection from 2-5 a reusable function and add Newton-Raphson.
refactor
3-4
Echoes and Aliases
mutability and aliasing, is versus ==, cloning with slices and copy, the mutable default argument trap
Find and fix three aliasing bugs, including a mutable default argument.
clone
3-5
Fixed Records
tuples in depth: immutability and unpacking, sets and set algebra, zip(), enumerate()
Find sensors present in both runs, in only one, and in either; pair readings with their timestamps.
compare
Boss 3
The Storage Auditor
Everything in Worlds 1–3
Audit the inventory with functions, lists, tuples and sets; fix an aliasing fault.
–
World 4
The Core



4-1
The Catalogue
dictionaries: keys, values and get(), looping over dictionaries and nesting, the counting pattern, choosing a data structure, with timing and Big-O vocabulary
Build a parts catalogue; choose list, tuple, set or dict for four scenarios (multiple choice); time `in` on a list, a set and a dict.
lookup
4-2
Fault Tolerance
exceptions and reading tracebacks, try / except / else / finally, raise and exception constructors, assert and defensive programming
Make the calibration program survive any input; raise a clear error for impossible values.
debug
4-3
The Archive
reading and writing files with open() and with, the csv module, pathlib.Path, validating input data
Read sensor CSVs, skip invalid rows with a report, write a summary file and a text bar chart.
save
4-4
The Test Bench
black-box and glass-box test design, boundary cases, assert-based test functions, systematic debugging and reviewing a provided solution
Design boundary tests for given functions, find two hidden bugs by experiment, then review a provided solution by choosing the right feedback for each fault.
test
4-5
Echo Chamber
recursion: base case and recursive case, inductive reasoning, recursion on lists and strings, memoisation with a dictionary
Recursive sum, reverse and palindrome; Fibonacci with and without a memo dict, with call counts.
echo
Boss 4
Systems Online (tier final)
Phase 1: timed mixed waves. Phase 2: a small single-file project plus a review
Phase 1: timed mixed waves. Phase 2: a single-file sensor-warning project with tests; review a provided solution.
–
Advanced tier
Two threads run through every level rather than belonging to one:
• Code quality is scored from Level 1-2 onwards: naming, indentation and comments, then docstrings from Level 3-2.
• Algorithmic thinking starts in Level 2-2: from there on, harder missions ask for a short plan in comments before the code is accepted.
Advanced tier: Worlds 5–8
In the Advanced tier Snek asks the player to bring the whole lab back online: a simulated factory with robots, conveyors, sensors and a scheduler. Missions grow from single files into small multi-file projects with test suites, and from writing code to reading, reviewing and redesigning it.
Level
Title
New concepts
Example Wave 2 mission
Power-up
World 5
Robot Foundry



5-1
The Lab Network
modules and import, packages and namespaces, the main guard, project layout with tests beside the code
Split the Boss 4 project into a package of three modules with a main guard; run its tests.
project
5-2
Blueprints
classes and objects, __init__ and attributes, methods and self, class versus instance attributes
Write a Robot class with position, battery, move() and report(); a class-level counter of robots.
build
5-3
Safety Interlocks
encapsulation and the _private convention, @property, setters with validation, invariants
Battery level and speed with validated setters; invariants checked in tests.
lock
5-4
Coordinates
printing: __repr__ and __str__, equality and hashing: exact __eq__ with __hash__, ordering and arithmetic: __lt__, __add__, __radd__, value objects with a separate is_close()
A Vector2D value class usable in sets, sorting and sum(), with exact equality and a separate is_close().
plot
5-5
Data Structures by Hand
abstract data type versus implementation, stack, queue and linked list as classes, the container protocol: __len__ and __iter__, cost of each operation and collections.deque
Implement Stack, Queue and LinkedList classes; compare operation costs with deque.
stack
Boss 5
The First Robot
Everything in World 5
Build a tested robot package from a specification.
–
World 6
Assembly Line



6-1
Specialists
inheritance and super(), overriding, isinstance(), is-a versus has-a: composition
WeldingRobot and DeliveryRobot from Robot; a Gripper by composition; justify each choice.
spawn
6-2
One Interface
polymorphism and duck typing, abstract base classes, type hints, typing.Protocol
A Sensor ABC and a Protocol; the controller reads any mix of sensors through one interface.
sensors
6-3
Fail-safe Systems
custom exception hierarchies, class-based context managers, logging, EAFP versus LBYL
A ConveyorFault hierarchy and a class-based context manager that always stops the belt; log every fault.
log
6-4
Operating Modes
finite state machines, enum.Enum, transition table versus the State pattern, match statements
One state machine two ways: a transition dict and the State pattern; compare in a short note.
mode
6-5
The Control Loop
discrete-time simulation, Euler integration of a motor model, a PID controller class, step response and tuning
Simulate a motor with Euler steps, write a PID class, tune it, plot the step response as text.
pid
Boss 6
The Production Line
Everything in Worlds 5–6
Run a mixed robot line with state machines, a PID-controlled belt and fault handling.
–
World 7
Data Streams



7-1
Pipelines I
first-class functions and lambda, map and filter, list, dict and set comprehensions, conditional expressions, any() and all()
Clean, filter and summarise 10 000 readings as a pipeline of small functions.
pipe
7-2
Pipelines II
closures and nonlocal, decorators, wraps and lru_cache, generators and yield, the iterator protocol
A @timed decorator, a generator streaming a huge log, lru_cache on recursive Fibonacci.
stream
7-3
Two Roads
functional versus object-oriented design of one system, dataclasses and NamedTuple, immutability, contextlib and itertools
Solve one scheduling problem functionally and with objects; write a half-page trade-off note.
twins
7-4
The Test Bench II
unittest and fixtures, test-first fixing, dependency injection and mocks, debugging with breakpoint() and pdb
Make a failing suite pass without changing tests; inject a fake sensor; explain a pdb session.
mock
7-5
The Legacy Controller
reading unfamiliar code, documenting a module, code smells and refactoring under tests, writing a code-review report
Document an unfamiliar module, find five planted bugs, refactor under tests, write a review report.
review
Boss 7
The Legacy Machine
Everything in Worlds 5–7
Review, test and improve a provided mini-project, including parts of Python Bytes' own code (provided files are exempt from the construct rule).
–
World 8
Factory Mainframe



8-1
The Architect
coupling and cohesion, SOLID in plain terms, strategy, factory and observer patterns, comparing two designs
Two designs for the task scheduler using strategy, factory or observer; argue for one in writing.
design
8-2
Speed Run
Big-O and Big-Theta, analysing loops and recursion, timeit and cProfile, heapq and bisect
Derive Big-O of given functions, profile a slow routine, speed it up and measure the gain.
profile
8-3
Sorting Line
insertion sort, merge sort and divide and conquer, binary search, stability
Implement insertion sort, merge sort and binary search; test stability; compare with sorted().
sort
8-4
Path Planning
graphs as adjacency dicts, BFS and DFS, Dijkstra with heapq, paths on a grid
Model the floor as a graph; BFS, DFS and Dijkstra; show each robot's path on the pixel map.
route
8-5
The Scheduler
greedy versus optimal, dynamic programming: memoised and tabulated, 0/1 knapsack as job scheduling, proving a greedy solution can fail
Greedy versus dynamic-programming job scheduling (0/1 knapsack); show the greedy one can fail.
schedule
Boss 8
The Factory Wakes
A full project with design note, tests and review
Full factory simulation: state machines, control loop, path planning, scheduling; design note, tests, review.
Ending + credits
From Level 7-4 onward, Wave 2 is graded by hidden unittest suites, and some missions are partly graded by a written note checked against a rubric (see Game design).
Technical architecture
Python Bytes is a single Python program built on the standard library only, so it installs with nothing but Python 3.12. The game engine is the hub: it reads level packs, draws through the renderer, sends player code to the runner and turns the grader's results into XP, stars and unlocks.
The player types code inside the game, line by line, in code mode (decided in docs/design/breakthrough.md); the game saves it after every line, then runs and grades it. :where copies a wave's code to a file for players who want an editor.
Components and the standard-library modules they use
Component
Job
Main modules
Screen renderer
Draws pixel sprites with half-block characters and ANSI colours; map, HUD, boss bars
shutil, sys, time
Game engine
Command loop, level state machine, scoring, stars, coins, unlocks
cmd or own parser, dataclasses
Level packs
One folder per level: story text, tips, waves, test cases, sprites
tomllib (reads TOML)
Code runner
Runs player code in a separate process with a time limit and fake input; captures output
subprocess, tempfile
Grader
Output tests, function tests, unittest suites (World 7+), AST rules, style rules
ast, unittest, importlib
Save file
Progress, stars, coins, badges
json, pathlib
Progression checker (developer tool)
Fails the build if a level uses a construct not taught yet. Reads levels/concepts.toml; the rules are in docs/curriculum.md
ast, tomllib
What a level pack looks like (simplified):
[level]
id = "2-3"
title = "Charging"
new_concepts = ["while", "break", "continue"]
power_up = "charge"

[[wave]]
kind = "build"            # fill-in | build | debug
brief = "Charge in 5 % steps until 100 or until the user types stop."
require = ["While"]        # AST node types the solution must use
forbid = ["For"]

[[wave.test]]
stdin = "\n\nstop\n"
expected_stdout_contains = ["Battery: 10 %"]
Limits I accept. The runner protects against infinite loops and crashes, but it is not a security sandbox; it is meant for players running their own code on their own machine. ANSI colours work in Windows Terminal, macOS Terminal and Linux terminals; the plain-ASCII mode covers the rest.
Development roadmap, step by step
The build runs in ten phases (0–9), each ending in a gate that must be met before the next starts. World 1 is playable, with real pixel art, at the end of Phase 3, so students can playtest every later phase.
Phase 0 – Foundations
[x] Create the Git repository and folder layout (engine/, render/, levels/, runner/, grader/, art/, tests/)
[x] Choose Python 3.12 and the standard library only
[x] Write the level style guide: level template, at most 4 new concepts per level, English, tone of the story
[x] Write the art style guide: the 16-colour palette, sprite sizes, a sample Snek sprite
Gate: repository exists; both style guides approved by me.
Phase 1 – Engine and renderer prototype
[x] Command loop with help, map, play, submit, quit
[x] Half-block pixel renderer that draws a sprite from a text file
[x] World map screen with placeholder sprites and Snek slithering between level nodes
[x] Level-pack loader (TOML) and save/load of progress (JSON)
[x] Write Level 1-1 as the test level
Gate: a player can open the map, play Level 1-1, quit and resume.
Phase 2 – Runner, grader and scoring
[x] Run player code in a separate process with a time limit and fake input
[x] Output tests, function tests, AST rules ("must use a for loop") and style rules
[x] XP, stars, coins, hints and the 70 % unlock rule
[x] Level-clear screen and boss fight screen with health bar and tries
Gate: Level 1-1 is fully graded; each wave's reference solution passes and a known-wrong solution fails.
Phase 2.5 – Breakthrough: it must feel like a real game (design: docs/design/breakthrough.md)
[ ] A: one command (python play.py), title screen, autosave after every line, signals, code buffers saved
[ ] B: code inside the game (quick console, :run, highlighting, friendly errors, a level clears only when every wave is passed); no external folders
[ ] C: full-screen look: alternate screen, HUD, framed panels, typed story, Snek reactions, level-clear animation, title with logo (--plain keeps the old look)
Gate: a new player starts with one command, types a level's code in the game, and closing the window never loses work.
Phase 3 – Worlds 1–2 (content and art)
[ ] Write Levels 1-1 to 2-5 in order: cutscene, tips, three waves, tests, power-up
[ ] Build Boss 1 and Boss 2
[ ] Draw Snek's states and the first two boss sprites
[ ] Build the progression checker (reads levels/concepts.toml, enforces the six rules in docs/curriculum.md); review every level against the level style guide before merging
Gate: Worlds 1–2 playable end to end.
Phase 4 – Playtest round 1
[ ] At least 5 students who have not seen the content playtest Worlds 1–2
[ ] Record time per level, hints bought, stars earned and where students got stuck
[ ] Ask whether the rewards feel motivating, not just whether the tasks are clear
[ ] Rewrite the levels where most students stalled
Gate: the median student clears Worlds 1–2 without outside help.
Phase 5 – Worlds 3–4
[ ] Write Levels 3-1 to 4-5 and Bosses 3 and 4 (both phases)
[ ] Data files for waves (the sensor CSVs of Level 4-3 and Boss 4)
[ ] Add the shop, badges, the Codex screen and the peer-review mode
[ ] Add tier grades and a printable progress report
Gate: Basic tier complete; every Basic outcome in the mapping table is tested.
Phase 6 – Engine features for the Advanced tier
[ ] Multi-file projects: a mission can provide a folder of starter files
[ ] Grading with hidden unittest suites
[ ] Rubric-graded written answers (trade-off notes, review reports)
[ ] Legacy-code missions that ship deliberately buggy modules
Gate: Level 5-1 runs on the new features.
Phase 7 – Worlds 5–8 (content and art)
[ ] Write the Advanced levels in order, using Python Bytes's own source code as material in World 7
[ ] Build Bosses 5–7 and Boss 8 (the final boss), with its specification and test suite
[ ] Draw paths on the pixel map (Level 8-4)
[ ] Optional time limit per wave (Level 8-2 timing missions); pdb in Level 7-4 is graded as a predict/explain wave, not run
[ ] Draw the factory tileset and the remaining boss sprites
Gate: Advanced tier playable end to end.
Phase 8 – Playtest round 2 and balancing
[ ] Full playthrough by student playtesters from both tiers
[ ] Tune coin prices, star thresholds, boss timers and pass marks from the data
[ ] Fix all bugs in the issue tracker
Gate: no open critical bugs; pass rates per level reviewed.
Phase 9 – Release 1.0
[ ] Installation guide and player handbook
[ ] Contributor guide: how to make a new level and its sprites
[ ] Tag version 1.0 and share it with the class
How I work, quality assurance and open questions
Python Bytes is a solo project: I build it on my own, for students. I work the way the courses ask students to work: in small reviewed changes. Students take part as playtesters in Phases 4 and 8.
Working rules
• Every change goes through a pull request and is reviewed by me before it is merged.
• A level is "done" only when its reference solutions pass, its wrong solutions fail, and the progression checker accepts it.
• Bugs and ideas go in the issue tracker.
Quality checks
• Automated tests for the engine and grader, run before each merge.
• For every task: one reference solution that must pass and at least one typical wrong solution that must fail, so grading is neither too strict nor too lenient.
• Progression checker run on all content, so no level uses a construct before it is taught.
• Playtest data from the student playtesters (time, hints, failure points) reviewed after each round.
Open questions
• Decided: players write code inside the game (code mode), not in an external editor. Code is saved after every typed line.
• Should the style checker use my own ast-based rules only, or the third-party pycodestyle package as an optional extra?
• How should the game treat AI-generated or copied answers, given that it is self-study?
• Is the grade scale in Game design acceptable, or should it be removed so the game is not confused with official OsloMet grading?
• Which licence should the code and content use if the game is shared beyond the class?
• Do I stay with pixel art in the terminal (standard library only), or move to a real graphics window with the third-party pygame package for true pixels and sound? (Proposal: terminal first; it keeps the game text-based and easy to install.)
• Should a class-wide leaderboard exist at all, or only personal bests?
