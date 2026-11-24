Python Bytes: Development Plan for a Task-Based Python Learning Game
Nov 24, 2026 · @Aleksander
Overview
Python Bytes (working title: small bites of Python, from a python that bites) is an arcade-style, pixel-art terminal game that teaches Python across 8 worlds, 29 levels and 8 boss fights. Each level teaches a few concepts, then the player clears coding waves to earn XP, stars and a new power-up before the next level on the map opens.
• Basic tier (Worlds 1–4) covers the learning outcomes of OsloMet's Introduction to Python Programming: variables, data types, strings and numbers, conditionals, loops, functions, lists, tuples, sets, dictionaries, exception handling and file I/O.
• Advanced tier (Worlds 5–8) covers Advanced Python Programming for Engineers: object-oriented and functional programming, choosing between them, robust design, debugging, reading other people's code and code review.
• Audience: first-year engineering students with no prior programming, who want real understanding, not memorised patterns.
• Format: a terminal game written in Python, drawn with coloured Unicode block characters so it looks like an 8-bit console game. The game's own source code becomes level material in World 7.
• Story frame: the player is a new technician in an abandoned robotics lab. The lab robot ARIA is offline; each world restores part of her, and from World 5 the player rebuilds the whole automated factory around her.
Progression model: worlds, levels and bosses
The game is a classic arcade map: the player walks ARIA along a pixel path from level to level, and each world ends in a boss fight that tests everything in that world. A level opens only when the one before it is cleared.
Tier
World
Theme
Levels
Boss
Basic
1
Boot Sector
1-1 to 1-4
Boss 1: The Corrupted Bootloader
Basic
2
Sensor Fields
2-1 to 2-4
Boss 2: The Night Patrol
Basic
3
Data Vaults
3-1 to 3-4
Boss 3: The Storage Auditor
Basic
4
The Core
4-1 to 4-3
Boss 4: ARIA Online (tier final)
Advanced
5
Robot Foundry
5-1 to 5-4
Boss 5: The First Robot
Advanced
6
Assembly Line
6-1 to 6-4
Boss 6: The Production Line
Advanced
7
Data Streams
7-1 to 7-4
Boss 7: The Legacy Machine
Advanced
8
Factory Mainframe
8-1 to 8-2
Final Boss: The Factory Wakes
Inside a level. Every level runs the same short loop, like stages in a shoot-'em-up:
1.  Cutscene – a short story scene with working code in it. The new syntax is seen in action before it is explained.
2.  Tips – a few one-line explanations of the new syntax, saved to the player's Codex.
3.  Wave 1 – Fill-in: complete missing parts of given code.
4.  Wave 2 – Build: write a program or function from a short mission brief.
5.  Wave 3 – Debug: predict the output of code, or find and fix the bug.
6.  Level clear – stars, XP, and a power-up command.
Bosses. A boss has a health bar made of hidden tests: every test the player's code passes knocks off one block of health. Bosses introduce no new concepts; they combine the whole world, add a time limit, and give the player 3 lives (one lost per failed submission). Losing all lives restarts the fight, not the world.
What we keep from Lingua Latina per se Illustrata. Only the core idea: strict cumulative progression. A level may use only what earlier levels taught plus 2–4 new things, and old concepts keep returning in new combinations. An automatic checker enforces this (see Technical architecture).
Example cutscene from Level 1-2, where variables are new and print() is already known:
# >> ARIA's memory banks flicker. Two empty cells light up.
name = "ARIA"
battery = 12
print(name)      # screen: ARIA
print(battery)   # screen: 12
# >> You patch in more power...
battery = 13
print(battery)   # screen: 13
# >> ARIA: "MEMORY CELL UPDATED. THANK YOU, TECHNICIAN."
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
1-3, 1-4, 2-1
Wave 2 in 1-3 to 2-1
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
3-1, 3-4, 4-1
"Choose the structure" wave in 4-1, Boss 4
Algorithmic thinking
2-2 onwards
Plan-first missions, Boss 4
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
3-3, Boss 4
Boss 4, phase 2 (project)
Collaborate, review code, give feedback
Boss 4
Peer-review round in Boss 4
Advanced tier – Advanced Python Programming for Engineers
Outcome (from course description)
Taught in
Tested by
Overview of Python for moderate real problems
5-1, Final Boss
Final Boss
OOP: class, object, method, inheritance, polymorphism, encapsulation
5-2 to 6-2
Wave 2 in 5-2 to 6-2, Bosses 5 and 6
Functional vs object-oriented features, when to use each
6-4, 7-1, 7-2
Dual-solution mission in 7-2
Robust, reliable programs with good OO design
6-3, 8-1
Design mission in 8-1, Final Boss
Alternative solutions, weigh pros and cons
7-2, 8-1
Written trade-off notes in 7-2 and 8-1
Clear and efficient programs
6-4, 8-2
Speed-run missions in 8-2
Find and fix errors in own programs
6-3, 7-3
Bug-hunt waves in 7-3
Understand others' programs to debug and change them
7-4
Legacy-code mission in 7-4, Boss 7
Conduct code review, document errors, suggest improvements
7-4, Final Boss
Review report in 7-4, peer review in Final Boss
Critically assess programming approaches
7-2, 8-1
Trade-off notes, Boss 7
Game design: level loop, rewards and scoring
Every level is a closed loop: watch, practise, score, and only then move on. A player who scores below 70 % spends coins on hints if they want, and replays only the waves they failed.
Replaying only failed waves keeps retries short; the 70 % gate stops players carrying gaps into later levels that build on them.
Arcade rewards
Reward
How it is earned
What it does
XP
Points from every wave
Fills the XP bar; level-ups change ARIA's sprite and colours
Stars (1–3 per level)
1 star ≥ 70 %, 2 stars ≥ 85 %, 3 stars = 100 % with no hints
A boss door opens only when the world's levels hold enough stars (proposal: 2 of 3 on average)
Coins
First-try passes and full code-quality scores
Buy hints in the shop
Power-ups
Clearing a level
A new terminal command built on the concept just learned (calc after 1-3, inventory after 3-1)
Lives
3 per boss fight
Lost on each failed boss submission; at 0 the fight restarts
Combo
Clearing waves first try in a row
XP multiplier: ×1.5 after 3, ×2 after 5
Badges
Special feats, for example "No Hints in World 1" or "Clean Coder" (full quality score on 10 levels)
Shown on the player's profile screen
Power-ups are the main reward: the player can actually use what they just learned as a tool in the game. Commands available from the start: help, map, play, submit, hint, codex, stats, quit.
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
Tier grade. Levels count 50 %, Bosses 1–3 (or 5–7) 20 % and the tier's final boss 30 %. The game shows the result on an A–F scale as a proposal: A ≥ 90 %, B ≥ 80 %, C ≥ 60 %, D ≥ 50 %, E ≥ 40 %, F below 40 %. These bands are our own choice for motivation and do not represent OsloMet's grading.
Look and feel: pixel art in the terminal
The game runs in an ordinary terminal but looks like an 8-bit console game. The trick is the Unicode half-block character ▀: with a different foreground and background colour, each character cell shows two stacked pixels, so an 80 × 24 terminal becomes an 80 × 48 pixel screen.
• Palette: one fixed 16-colour palette of our own, used for every sprite, so the game looks consistent.
• Sprites: ARIA (16 × 16 pixels) in several states (offline, booting, happy, damaged), one sprite per boss, small icons for stars, coins and hearts.
• Screens: title screen, world map, level intro card, code-wave screen, boss fight screen, level-clear screen, Codex, shop, stats.
• Animation: a few frames only (ARIA walking on the map, a boss health bar draining, a level-clear flash), drawn by redrawing the screen.
• Fallbacks: a plain-ASCII mode for terminals without colour, and an accessible mode with no flashing and screen-reader-friendly text.
Rough mock-up of the world map and a boss fight (pixel art shown as text):
 WORLD 1 · BOOT SECTOR            XP 1240   ★ 7/12   COINS 35

   [1-1]★★★ ══ [1-2]★★☆ ══ [1-3]★☆☆ ══ [1-4] ··· ══ [BOSS 1]
                               ▲
                              ARIA

 > play 1-3    > codex    > shop    > stats

 BOSS 1 · THE CORRUPTED BOOTLOADER              LIVES ♥ ♥ ♡
 BOSS HP [██████████░░░░░░░░░░]  5 of 10 hidden tests still failing
 TIME 07:42
Basic tier: Worlds 1–4
The Basic tier restores ARIA one subsystem at a time, from her voice in Level 1-1 to a full log-analysis routine in Boss 4. Each row lists only what is new; everything earlier is assumed and keeps coming back.
Level
Title (story beat)
New concepts
Example Wave 2 mission
Power-up
World 1
Boot Sector



1-1
Hello, Terminal (ARIA's voice)
print(), string literals, comments, running a script
Make ARIA print a three-line start-up message
status
1-2
Memory Cells (short-term memory)
Variables, assignment, int, float, str, bool, type(), snake_case naming
Store and print ARIA's serial number, battery level and online state
memory
1-3
Power Calculations (the battery)
Arithmetic operators, //, %, **, precedence, round(), int/float conversion
Compute remaining run-time from battery capacity and power draw
calc
1-4
Corrupted Logs (the log reader)
String indexing, slicing, len(), f-strings, methods upper, strip, replace, split
Extract the timestamp and error code from a damaged log line
read <file>
Boss 1
The Corrupted Bootloader
Everything in World 1
Repair a scrambled boot report under time pressure
–
World 2
Sensor Fields



2-1
Listening (the microphone)
input(), converting input with int() and float(), input → process → output
Ask for two sensor readings and print the offset
talk
2-2
Decisions (the alarm system)
bool expressions, comparisons, and/or/not, if/elif/else, nesting; plan first
Classify a temperature as OK, WARNING or CRITICAL
alarm
2-3
Charging (the charge controller)
while, counters, sentinel values, break, continue, avoiding infinite loops
Charge in 5 % steps until full or the user types stop
charge
2-4
The Grid Scan (the camera)
for, range(), looping over strings, accumulators, nested loops
Scan a 5 × 5 grid and print the coordinates of every obstacle
scan
Boss 2
The Night Patrol
Everything in Worlds 1–2
Patrol simulation combining input, decisions and loops
–
World 3
Data Vaults



3-1
Inventory (parts storage)
Lists: indexing, slicing, append, insert, remove, pop, sort, in, lists of lists
Add, remove, search and sort items in a parts list
inventory
3-2
Subroutines I (motor functions)
def, parameters, return, calling, docstrings, local vs global scope
Write celsius_to_kelvin() and distance() with docstrings
define
3-3
Subroutines II (refactoring ARIA)
Default and keyword arguments, returning several values, decomposition, min, max, sum, sorted, enumerate, zip
Split an earlier 40-line script into four well-named functions
refactor
3-4
Fixed Records (sensor history)
Tuples, immutability, unpacking, sets, union/intersection/difference
Find which sensors reported in both of two test runs
compare
Boss 3
The Storage Auditor
Everything in Worlds 1–3
Audit the inventory with functions, lists, tuples and sets
–
World 4
The Core



4-1
The Catalogue (knowledge base)
Dictionaries: get, items, looping, nested dictionaries, counting pattern; choosing the right data structure
Build a parts catalogue; pick list, tuple, set or dict for four scenarios
lookup
4-2
Fault Tolerance (error recovery)
Exceptions, reading tracebacks, try/except/else/finally, raise, debugging strategy
Make the calibration program survive any bad input
debug
4-3
The Archive (long-term memory)
open(), with, reading lines, writing and appending, parsing comma-separated data
Read a sensor log file and write a summary report file
save
Boss 4
ARIA Online (tier final)
Phase 1: timed mixed waves. Phase 2: a small project plus peer review
Analyse a week of warehouse-robot logs from files, then review a classmate's code
Advanced tier
Two threads run through every level rather than belonging to one:
• Code quality is scored from Level 1-2 onwards: naming, indentation and comments, then docstrings from Level 3-2.
• Algorithmic thinking starts in Level 2-2: from there on, harder missions ask for a short plan in comments before the code is accepted.
Advanced tier: Worlds 5–8
In the Advanced tier ARIA asks the player to bring the whole lab back online: a simulated factory with robots, conveyors, sensors and a scheduler. Missions grow from single files into small multi-file projects with test suites, and from writing code to reading, reviewing and redesigning it.
Level
Title (story beat)
New concepts
Example Wave 2 mission
Power-up
World 5
Robot Foundry



5-1
The Lab Network (bridge level)
Modules, import, packages, if __name__ == "__main__":, project layout
Split the Boss 4 project into three modules
project
5-2
Blueprints (robot classes)
class, objects, __init__, attributes, methods, self
Write a Robot class with move() and report()
build
5-3
Safety Interlocks (protecting state)
Encapsulation, _private convention, @property, setters with validation, invariants
A battery level that can never go below 0 % or above 100 %
lock
5-4
Coordinates (robot positions)
__str__, __repr__, __eq__, __lt__, __add__, operator overloading
A Vector2D class that supports +, == and printing
plot
Boss 5
The First Robot
Everything in World 5
Build a tested robot package from a specification
–
World 6
Assembly Line



6-1
Specialists (robot types)
Inheritance, super(), overriding, is-a vs has-a, composition
WeldingRobot and DeliveryRobot from Robot; a gripper by composition
spawn
6-2
Many Sensors, One Interface
Polymorphism, duck typing, abc.ABC, @abstractmethod
A Sensor base class; the controller reads any list of sensors via read()
sensors
6-3
Fail-safe Systems
Custom exception hierarchies, context managers (__enter__/__exit__), logging
A ConveyorFault hierarchy and a context manager that always stops the belt
log
6-4
Data Pipelines I
First-class functions, lambda, map, filter, comprehensions, generator expressions, sorted(key=...)
Clean and filter 10 000 sensor readings in a pipeline
pipe
Boss 6
The Production Line
Everything in Worlds 5–6
Run a mixed robot line and log its faults
–
World 7
Data Streams



7-1
Data Pipelines II
Closures, decorators, generators and yield, the iterator protocol, itertools, functools, pure functions
A @timed decorator and a generator streaming a large log file
stream
7-2
Two Roads (paradigm choice)
Functional vs object-oriented design, dataclasses, immutability; when each fits
Solve one scheduling problem both ways and write a half-page trade-off note
compare-designs
7-3
The Test Bench
assert, unittest, test-first fixing, pdb, systematic debugging
Make a failing test suite pass without changing the tests
test
7-4
The Legacy Controller (others' code)
Reading unfamiliar code, documenting it, refactoring safely, writing a code-review report
Find and document five planted bugs in an old module, then fix them
review
Boss 7
The Legacy Machine
Everything in Worlds 5–7
Review, test and improve a provided mini-project, including parts of Python Bytes's own code
–
World 8
Factory Mainframe



8-1
The Architect
Coupling and cohesion, SOLID in plain terms, type hints, three patterns (strategy, factory, observer)
Propose two designs for the task scheduler and argue for one
design
8-2
Speed Run (efficiency)
Big-O intuition, choosing data structures for speed, timeit, profiling
Speed up a slow part-matching routine and measure the gain
profile
Final Boss
The Factory Wakes
A full project with design note, tests and peer review
Build the factory simulation; review another team's code with the review template
Ending + credits
From Level 7-3 onward, Wave 2 is graded by hidden unittest suites, and some missions are partly graded by a written note checked against a rubric (see Game design).
Technical architecture
Python Bytes is a single Python program built on the standard library only, so it installs with nothing but Python 3.12. The game engine is the hub: it reads level packs, draws through the renderer, sends player code to the runner and turns the grader's results into XP, stars and unlocks.
The player writes code in their own editor, in a workspace/ folder the game watches; the game then runs and grades it.
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
Progress, XP, stars, coins, badges
json, pathlib
Progression checker (developer tool)
Fails the build if a level uses a construct not taught yet
ast
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
Limits we accept. The runner protects against infinite loops and crashes, but it is not a security sandbox; it is meant for players running their own code on their own machine. ANSI colours work in Windows Terminal, macOS Terminal and Linux terminals; the plain-ASCII mode covers the rest.
Development roadmap, step by step
The build runs in ten phases (0–9), each ending in a gate that must be met before the next starts. World 1 is playable, with real pixel art, at the end of Phase 3, so every later phase can be playtested.
Phase 0 – Foundations
[ ] Create the shared Git repository and folder layout (engine/, render/, levels/, runner/, grader/, art/, tests/)
[ ] Agree on Python 3.12 and the standard library only
[ ] Write the level style guide: level template, at most 4 new concepts per level, English, tone of the story
[ ] Write the art style guide: the 16-colour palette, sprite sizes, a sample ARIA sprite
[ ] Assign roles (see Collaboration)
Gate: repository exists; both style guides approved by the group.
Phase 1 – Engine and renderer prototype
[ ] Command loop with help, map, play, submit, quit
[ ] Half-block pixel renderer that draws a sprite from a text file
[ ] World map screen with placeholder sprites and ARIA walking between level nodes
[ ] Level-pack loader (TOML) and save/load of progress (JSON)
[ ] Write Level 1-1 as the test level
Gate: a player can open the map, play Level 1-1, quit and resume.
Phase 2 – Runner, grader and scoring
[ ] Run player code in a separate process with a time limit and fake input
[ ] Output tests, function tests, AST rules ("must use a for loop") and style rules
[ ] XP, stars, coins, hints and the 70 % unlock rule
[ ] Level-clear screen and boss fight screen with health bar and lives
Gate: Level 1-1 is fully graded; each wave's reference solution passes and a known-wrong solution fails.
Phase 3 – Worlds 1–2 (content and art)
[ ] Write Levels 1-1 to 2-4 in order: cutscene, tips, three waves, tests, power-up
[ ] Build Boss 1 and Boss 2
[ ] Draw ARIA's states and the first two boss sprites
[ ] Build the progression checker; peer-review every level before merging
Gate: Worlds 1–2 playable end to end.
Phase 4 – Playtest round 1
[ ] At least 5 testers who have not seen the content play Worlds 1–2
[ ] Record time per level, hints bought, stars earned and where players got stuck
[ ] Ask whether the rewards feel motivating, not just whether the tasks are clear
[ ] Rewrite the levels where most testers stalled
Gate: the median tester clears Worlds 1–2 without outside help.
Phase 5 – Worlds 3–4
[ ] Write Levels 3-1 to 4-3 and Bosses 3 and 4 (both phases)
[ ] Add the shop, badges, the Codex screen and the peer-review mode
[ ] Add tier grades and a printable progress report
Gate: Basic tier complete; every Basic outcome in the mapping table is tested.
Phase 6 – Engine features for the Advanced tier
[ ] Multi-file projects: a mission can provide a folder of starter files
[ ] Grading with hidden unittest suites
[ ] Rubric-graded written answers (trade-off notes, review reports)
[ ] Legacy-code missions that ship deliberately buggy modules
Gate: Level 5-2 runs on the new features.
Phase 7 – Worlds 5–8 (content and art)
[ ] Write the Advanced levels in order, using Python Bytes's own source code as material in World 7
[ ] Build Bosses 5–7 and the Final Boss, with its specification and test suite
[ ] Draw the factory tileset and the remaining boss sprites
Gate: Advanced tier playable end to end.
Phase 8 – Playtest round 2 and balancing
[ ] Full playthrough by testers from both tiers
[ ] Tune XP, coin prices, star thresholds, boss timers and pass marks from the data
[ ] Fix all bugs in the issue tracker
Gate: no open critical bugs; pass rates per level reviewed.
Phase 9 – Release 1.0
[ ] Installation guide and player handbook
[ ] Contributor guide: how to make a new level and its sprites
[ ] Tag version 1.0 and share it with the class
Collaboration, quality assurance and open questions
The team builds Python Bytes the way the courses ask students to work: in small reviewed changes. Writing and reviewing the game is itself practice for the "code review" outcomes of both courses.
Roles (one person can hold several)
Role
Responsible for
Engine developer
Command loop, level loader, save system, pixel renderer
Grader developer
Runner, test types, style and structure checks
Content author
Writing levels: cutscenes, tips, waves and power-ups
Test writer
Reference solutions, wrong solutions and test cases for each task
Reviewer
Reviewing every pull request against the style guide
Playtest lead
Recruiting testers, collecting and summarising feedback
Pixel artist
Palette, ARIA and boss sprites, map tiles, level-clear animations
Working rules
• Every change goes through a pull request and needs one approving review from someone other than the author.
• A level is "done" only when its reference solutions pass, its wrong solutions fail, and the progression checker accepts it.
• Bugs and ideas go in the issue tracker, never only in chat.
Quality checks
• Automated tests for the engine and grader, run before each merge.
• For every task: one reference solution that must pass and at least one typical wrong solution that must fail, so grading is neither too strict nor too lenient.
• Progression checker run on all content, so no level uses a construct before it is taught.
• Playtest data (time, hints, failure points) reviewed after each round.
Open questions for the group
• How should players write code: in the terminal itself, or in their own editor with the game watching a workspace/ folder? (Proposal: own editor, because that is how real work is done.)
• Should the style checker use our own ast-based rules only, or the third-party pycodestyle package as an optional extra?
• How should the game treat AI-generated or copied answers, given that it is self-study?
• Is the grade scale in Game design acceptable, or should it be removed so the game is not confused with official OsloMet grading?
• Which licence should the code and content use if the game is shared beyond the class?
• Do we keep the ARIA robotics-lab story, or vote on alternatives before drawing the sprites?
• Do we stay with pixel art in the terminal (standard library only), or move to a real graphics window with the third-party pygame package for true pixels and sound? (Proposal: terminal first; it keeps the game text-based and easy to install.)
• Should a class-wide leaderboard exist at all, or only personal bests?
