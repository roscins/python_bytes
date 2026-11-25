# Python Bytes – Curriculum and progression

Version 2 · Source of truth for what every level teaches. The machine-readable twin of this file is `levels/concepts.toml`; if the two disagree, fix them together in one PR. The tables in sections 4 and 5 repeat the title, concepts, difficulty, outcomes and power-up of `concepts.toml`, and `tests/test_curriculum_data.py` fails when they differ.

## 1. Standard and scope

The curriculum has two tiers.

- **Basic tier (Worlds 1–4)** covers every learning outcome of OsloMet's *Introduction to Python Programming*.
- **Advanced tier (Worlds 5–8)** covers every learning outcome of OsloMet's *Advanced Python Programming for Engineers*.

On top of the OsloMet outcomes, both tiers are raised to the level of first-year engineering and computer-science programming at leading universities. They are benchmarked against the publicly listed topics of:

| Benchmark | Topics we take from it |
| --- | --- |
| Cambridge, Engineering Tripos Part IA, 1P4: Computing | Floating-point round-off; algorithms and complexity; data structures; object-oriented design; testing and error handling; numerical computation; a modular project with unit tests |
| MIT 6.100A, Introduction to CS and Programming using Python | Bindings and aliasing; bisection search; recursion with memoisation; testing and debugging; dunder methods; Big-O and Big-Theta |
| MIT 6.100B | Graph search (BFS/DFS) and path planning |
| Oxford Physics first-year computing | Numerical problems such as differential equations, solved by simulation |

"Benchmarked" means: a student who clears the tier has practised the same core topics at comparable depth. It does not mean the game replaces those courses or carries their credit.

**Known gap, on purpose.** These university courses also use NumPy and Matplotlib for array processing and plotting. Python Bytes uses the standard library only, so arrays are taught with lists, and plotting is done with the game's own text/pixel canvas (Levels 4-3 and 6-5). A later optional bonus world could add NumPy.

## 2. Structure

- 8 worlds × 5 levels = **40 levels**, plus **8 bosses** (one per world, ids `boss-1` to `boss-8`).
- Every non-boss level has 2–4 headline **concepts** (the `concepts` field). The concepts are what the player is told they learn. The **constructs** in `concepts.toml` are the fine-grained syntax items the checker looks for, so one concept such as "string methods" can be many constructs. A level that teaches a method rather than syntax (an algorithm, a design approach) is marked `technique = true` and may add no constructs.
- Difficulty is rated 1–5. Inside a world it never decreases, the boss is at least as hard as the hardest level in its world, and a new world starts at most one step below the previous boss.
- Every 6th item is a boss: no new concepts, mixed tasks, time limit, 3 lives.
- Every level has a power-up: the terminal command the player earns by clearing it. Bosses have none.

This replaces the earlier 29-level layout in `docs/plan.md` (worlds had 2–4 levels). Level ids change accordingly, and the last boss is `boss-8`, not `final-boss`.

## 3. Outcome codes

### OsloMet – Introduction to Python Programming

| Code | Outcome |
| --- | --- |
| B1 | Variables, data types, basic syntax |
| B2 | Manipulate numbers and strings |
| B3 | Conditional statements |
| B4 | Loops (for, while) |
| B5 | Define and call functions, pass arguments |
| B6 | Distinguish and use lists, tuples, sets, dictionaries |
| B7 | Algorithmic thinking for simple problems |
| B8 | Best practice: indentation, naming, documentation |
| B9 | Error handling with try/except, debugging |
| B10 | File input and output |
| B11 | Break real problems into manageable sub-tasks |
| B12 | Code review and constructive feedback |

### OsloMet – Advanced Python Programming for Engineers

| Code | Outcome |
| --- | --- |
| A1 | Use Python to solve real problems of moderate size |
| A2 | OOP: class, object, method, inheritance, polymorphism, encapsulation |
| A3 | Functional vs object-oriented features, and when to use each |
| A4 | Robust programs with good OO design; alternative solutions and trade-offs |
| A5 | Clear and efficient programs |
| A6 | Find and fix errors in own programs |
| A7 | Understand others' programs to debug and change them |
| A8 | Conduct code review, document errors, suggest improvements |
| A9 | Critically assess programming approaches |

### Rigor extensions (benchmark topics)

| Code | Topic | Benchmark |
| --- | --- | --- |
| R1 | Floating-point representation and round-off error | Cambridge 1P4 |
| R2 | Algorithms and complexity (counting operations, Big-O, Big-Theta) | Cambridge 1P4, MIT 6.100A |
| R3 | Recursion, induction, memoisation | MIT 6.100A |
| R4 | Bindings, mutability, aliasing, cloning | MIT 6.100A |
| R5 | Specification, testing and debugging | MIT 6.100A, Cambridge 1P4 |
| R6 | Object-oriented data structures | Cambridge 1P4 |
| R7 | Numerical methods and simulation | Cambridge 1P4, Oxford Physics |
| R8 | Graph search and path planning | MIT 6.100B |
| R9 | Modular project with unit tests | Cambridge 1P4 (Lent project) |
| R10 | Automation patterns: state machines and feedback control | Programme-specific (automation and robotics) |

## 4. Basic tier

### World 1 – Boot Sector: values and expressions

| Level | Title | Concepts | Difficulty | Outcomes | Power-up |
| --- | --- | --- | --- | --- | --- |
| 1-1 | Hello, Terminal | print(); string literals; comments | 1 | B1, B8 | `status` |
| 1-2 | Memory Cells | variables and assignment; the types int, float, str and bool; type(); snake_case names | 1 | B1, B8, R4 | `memory` |
| 1-3 | Power Calculations | arithmetic operators and precedence; //, % and **; converting between int, float and str; round() | 2 | B2 | `calc` |
| 1-4 | Floating Truth | why 0.1 + 0.2 != 0.3; comparison operators; absolute and relative tolerance; math.isclose() and abs() | 2 | B2, R1 | `approx` |
| 1-5 | Corrupted Logs | indexing and slicing; len(); string methods; f-strings with format specs | 2 | B2 | `read` |
| Boss 1 | The Corrupted Bootloader | No new concepts. Repair a scrambled boot report under time pressure. | 3 | B1, B2, R1 | – |

### World 2 – Sensor Fields: control flow and first algorithms

| Level | Title | Concepts | Difficulty | Outcomes | Power-up |
| --- | --- | --- | --- | --- | --- |
| 2-1 | Listening | input(); converting input to numbers; input, process, output | 1 | B1, B2 | `talk` |
| 2-2 | Decisions | and, or, not; if / elif / else; truthiness and bool(); planning in comments first | 2 | B3, B7 | `alarm` |
| 2-3 | Charging | while loops; sentinel values; break and continue; augmented assignment | 2 | B4 | `charge` |
| 2-4 | Grid Scan | for loops and range(); looping over strings; accumulators; nested loops | 3 | B4, B7 | `scan` |
| 2-5 | Finding the Signal | exhaustive enumeration and guess-and-check; bisection search; stopping on a float tolerance; counting iterations | 3 | B7, R1, R2, R7 | `seek` |
| Boss 2 | The Night Patrol | No new concepts. Patrol simulation combining input, decisions, loops and a bisection search. | 3 | B3, B4, B7 | – |

### World 3 – Data Vaults: functions, lists, tuples and sets

| Level | Title | Concepts | Difficulty | Outcomes | Power-up |
| --- | --- | --- | --- | --- | --- |
| 3-1 | Inventory | lists: literals, indexing and slicing; adding, removing and sorting items; searching with in; lists of lists | 2 | B6 | `inventory` |
| 3-2 | Subroutines I | def, parameters and return; None; docstrings; local scope | 2 | B5, B8 | `define` |
| 3-3 | Subroutines II | default and keyword arguments; returning several values; min, max, sum and sorted; decomposition, specifications and Newton-Raphson | 3 | B5, B11, R5, R7 | `refactor` |
| 3-4 | Echoes and Aliases | mutability and aliasing; is versus ==; cloning with slices and copy; the mutable default argument trap | 3 | B6, R4 | `clone` |
| 3-5 | Fixed Records | tuples in depth: immutability and unpacking; sets and set algebra; zip(); enumerate() | 3 | B6 | `compare` |
| Boss 3 | The Storage Auditor | No new concepts. Audit the inventory with functions, lists, tuples and sets; fix an aliasing fault. | 4 | B5, B6, R4 | – |

### World 4 – The Core: dictionaries, robustness, files and recursion

| Level | Title | Concepts | Difficulty | Outcomes | Power-up |
| --- | --- | --- | --- | --- | --- |
| 4-1 | The Catalogue | dictionaries: keys, values and get(); looping over dictionaries and nesting; the counting pattern; choosing a data structure, with timing and Big-O vocabulary | 3 | B6, B7, R2 | `lookup` |
| 4-2 | Fault Tolerance | exceptions and reading tracebacks; try / except / else / finally; raise and exception constructors; assert and defensive programming | 3 | B9, R5 | `debug` |
| 4-3 | The Archive | reading and writing files with open() and with; the csv module; pathlib.Path; validating input data | 3 | B10, B11 | `save` |
| 4-4 | The Test Bench | black-box and glass-box test design; boundary cases; assert-based test functions; systematic debugging and reviewing a provided solution | 3 | B8, B9, B12, R5 | `test` |
| 4-5 | Echo Chamber | recursion: base case and recursive case; inductive reasoning; recursion on lists and strings; memoisation with a dictionary | 4 | B5, B7, R3 | `echo` |
| Boss 4 | Systems Online | No new concepts. Phase 1: timed mixed waves. Phase 2: a single-file sensor-warning project with tests; review a provided solution. | 5 | B11, B12, R5 | – |

Notes on the Basic tier:

- **1-5** uses `split()` before lists exist. The result is only indexed (`parts[0]`) or passed to `join()`; list literals come in 3-1.
- **3-3** holds the first tuples (returning and unpacking several values). 3-5 then teaches tuples properly, together with sets, `zip()` and `enumerate()`.
- **4-1** is where timing (`time`) and the first Big-O words come in, because "choose the right structure" needs a measurement to argue with. The "justify" waves are multiple choice; written answers belong to Worlds 7–8.
- **4-4** teaches B12 without written answers: the player reviews a provided solution by choosing the right feedback for each fault and marking the line that holds it.
- **4-5** (recursion) is the last level of the world on purpose. Call counts are kept through return values or a mutable counter, because `global` is never taught (see the level style guide). There is no nested-list flattening: it needs `isinstance`, which comes in 6-1.
- **Boss 4** is one file. The player cannot import their own modules before 5-1.

## 5. Advanced tier

### World 5 – Robot Foundry: objects and data structures

| Level | Title | Concepts | Difficulty | Outcomes | Power-up |
| --- | --- | --- | --- | --- | --- |
| 5-1 | The Lab Network | modules and import; packages and namespaces; the main guard; project layout with tests beside the code | 2 | A1, B11, R9 | `project` |
| 5-2 | Blueprints | classes and objects; __init__ and attributes; methods and self; class versus instance attributes | 2 | A2 | `build` |
| 5-3 | Safety Interlocks | encapsulation and the _private convention; @property; setters with validation; invariants | 3 | A2, A4 | `lock` |
| 5-4 | Coordinates | printing: __repr__ and __str__; equality and hashing: exact __eq__ with __hash__; ordering and arithmetic: __lt__, __add__, __radd__; value objects with a separate is_close() | 3 | A2 | `plot` |
| 5-5 | Data Structures by Hand | abstract data type versus implementation; stack, queue and linked list as classes; the container protocol: __len__ and __iter__; cost of each operation and collections.deque | 4 | A2, A5, R2, R6 | `stack` |
| Boss 5 | The First Robot | No new concepts. Build a tested robot package from a specification. | 4 | A2, R6 | – |

### World 6 – Assembly Line: inheritance, robustness, automation

| Level | Title | Concepts | Difficulty | Outcomes | Power-up |
| --- | --- | --- | --- | --- | --- |
| 6-1 | Specialists | inheritance and super(); overriding; isinstance(); is-a versus has-a: composition | 3 | A2, A4 | `spawn` |
| 6-2 | One Interface | polymorphism and duck typing; abstract base classes; type hints; typing.Protocol | 3 | A2, A9 | `sensors` |
| 6-3 | Fail-safe Systems | custom exception hierarchies; class-based context managers; logging; EAFP versus LBYL | 4 | A4, A6 | `log` |
| 6-4 | Operating Modes | finite state machines; enum.Enum; transition table versus the State pattern; match statements | 4 | A4, A9, R10 | `mode` |
| 6-5 | The Control Loop | discrete-time simulation; Euler integration of a motor model; a PID controller class; step response and tuning | 5 | A1, R7, R10 | `pid` |
| Boss 6 | The Production Line | No new concepts. Run a mixed robot line with state machines, a PID-controlled belt and fault handling. | 5 | A1, A4, R10 | – |

### World 7 – Data Streams: functional style, testing, others' code

| Level | Title | Concepts | Difficulty | Outcomes | Power-up |
| --- | --- | --- | --- | --- | --- |
| 7-1 | Pipelines I | first-class functions and lambda; map and filter; list, dict and set comprehensions; conditional expressions, any() and all() | 3 | A3, A5 | `pipe` |
| 7-2 | Pipelines II | closures and nonlocal; decorators, wraps and lru_cache; generators and yield; the iterator protocol | 4 | A3, R3 | `stream` |
| 7-3 | Two Roads | functional versus object-oriented design of one system; dataclasses and NamedTuple; immutability; contextlib and itertools | 4 | A3, A9 | `twins` |
| 7-4 | The Test Bench II | unittest and fixtures; test-first fixing; dependency injection and mocks; debugging with breakpoint() and pdb | 4 | A6, R5 | `mock` |
| 7-5 | The Legacy Controller | reading unfamiliar code; documenting a module; code smells and refactoring under tests; writing a code-review report | 4 | A7, A8 | `review` |
| Boss 7 | The Legacy Machine | No new concepts. Review, test and improve a provided mini-project, including parts of Python Bytes' own code (provided files are exempt from the construct rule). | 5 | A7, A8, A9 | – |

### World 8 – Factory Mainframe: algorithms and design

| Level | Title | Concepts | Difficulty | Outcomes | Power-up |
| --- | --- | --- | --- | --- | --- |
| 8-1 | The Architect | coupling and cohesion; SOLID in plain terms; strategy, factory and observer patterns; comparing two designs | 4 | A4, A9 | `design` |
| 8-2 | Speed Run | Big-O and Big-Theta; analysing loops and recursion; timeit and cProfile; heapq and bisect | 4 | A5, R2 | `profile` |
| 8-3 | Sorting Line | insertion sort; merge sort and divide and conquer; binary search; stability | 4 | A5, R2, R3 | `sort` |
| 8-4 | Path Planning | graphs as adjacency dicts; BFS and DFS; Dijkstra with heapq; paths on a grid | 5 | A1, A5, R8 | `route` |
| 8-5 | The Scheduler | greedy versus optimal; dynamic programming: memoised and tabulated; 0/1 knapsack as job scheduling; proving a greedy solution can fail | 5 | A5, A9, R2, R3 | `schedule` |
| Boss 8 | The Factory Wakes | No new concepts. Full factory simulation: state machines, control loop, path planning, scheduling; design note, tests, review. | 5 | A1, A4, A8, R9, R10 | – |

Notes on the Advanced tier:

- **5-1** is the first multi-file level. It splits the single-file Boss 4 project into modules and runs its tests (B11, R9).
- **5-4** teaches value objects with exact `__eq__` and a matching `__hash__`. Closeness is a separate `is_close()` method, because a tolerance-based `__eq__` cannot have a consistent hash. `__len__` and `__iter__` wait for 5-5, where the Stack and Queue classes need them. `iter()` first appears there; `next()` first appears in 4-3, and 7-2 teaches the iterator protocol with both.
- **6-3** uses class-based context managers only. `@contextmanager` needs `yield` (7-2) and is taught in 7-3.
- **7-2** needs `*args` and `**kwargs` before a decorator can be written, and `functools.wraps` and `lru_cache`. `functools` is therefore listed in 7-2; `partial` and `reduce` are used from 7-3.
- **7-4** teaches `pdb` as a predict/explain wave. The runner has no terminal for a debugger, so the wave shows a session and asks questions about it.
- **8-4** draws paths on the game's pixel map, which is a renderer feature on the roadmap (Phase 7).

## 6. The progression checker

The checker reads `levels/concepts.toml` and the code of every level in `levels/`.

### What counts as a construct

| Form | Allows |
| --- | --- |
| `"Node"` (for example `While`) | that `ast` node type and all its sub-forms. `Compare` allows every comparison; `Match` allows every pattern. |
| `"Node:detail"` (`BinOp:FloorDiv`, `Compare:Is`) | only that sub-form. A level that wants to hold sub-forms back lists the ones it allows. `Compare:In` also allows `not in`; `Compare:Is` also allows `is not`. |
| `"call:name"` | calling that built-in, for example `call:print` |
| `"method:name"` | calling that method on a **built-in** str, list, dict, set or file. Methods of user-defined classes and of library classes are free once the class or module is allowed. |
| `"import:module"` | `import module`, `from module import ...` and everything `module.*` (calls and attributes). `import:local` does the same for the project's own modules. |
| `"decorator:name"` | using that decorator |
| `"dunder:name"` | defining that special method in a class |
| `"pattern:name"` | a rule beyond plain syntax: `docstring`, `default_args`, `recursion`, `main_guard`, `class_bases`, `annotations`, `varargs`, `custom_decorator` |

**Always allowed, never listed:** `Module`, `Load`, `Store`, `Expr`, and the name of a function that is being called. (The call itself is still gated: `print("x")` needs `call:print`.)

**Which code is checked.** Rule 1 applies to the cutscene code, fill-in starters, reference solutions and debug code. A wrong solution must follow the rule only if it parses (some wrong solutions are deliberately not valid Python). Output text is never checked: expected output, and the `answer` and `wrong` of a predict wave. A file provided with a level can set `exempt = true`; Boss 7 needs this to review the game's own code.

**"Earlier"** means earlier in the file `concepts.toml`. A level allows the union of its own constructs and those of every earlier item.

**Never taught.** `global` is never taught and never allowed. The player passes values in and returns them out, so a function can be read and tested on its own. The reason is in the level style guide.

### The six rules

1. A level's code may use only constructs listed in `concepts.toml` for that level or any earlier item.
2. Bosses add no constructs.
3. Every non-boss level adds at least one construct, unless it is marked `technique = true`.
4. Every outcome code (B1–B12, A1–A9, R1–R10) appears in at least one **non-boss** level. A boss can test an outcome, but only a level teaches it.
5. Inside a world, difficulty never decreases. The boss is at least as hard as the hardest level of its world. A new world starts at or below the previous boss's difficulty minus 1.
6. `recycles` may only name items that come earlier in the file.

The loader keeps its own limit on `new_concepts` in a level pack (2–4). The `concepts` of a level in `concepts.toml` have the same limit.
