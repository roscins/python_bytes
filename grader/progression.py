"""The progression checker: what may each level use, and does the curriculum keep its rules?

levels/concepts.toml lists the constructs every level adds. docs/curriculum.md
(section 6) holds the six rules this module enforces:

1. A level's code uses only constructs listed for that level or an earlier one.
2. Bosses add no constructs.
3. Every level adds a construct, unless it is marked `technique = true`.
4. Every outcome code appears in at least one level that is not a boss.
5. Inside a world difficulty never decreases, the boss is at least the
   world's maximum, and a new world starts at most one below the previous boss.
6. `recycles` names only items that come earlier.

Rules 2-6 look at the data (check_curriculum, check_item). Rule 1 looks at
the code of a level (check_code, check_level_code). Every check returns a
list of problems, one line of text each, and an empty list means all is well.
"""

import tomllib
from pathlib import Path

from grader.constructs import find_needs

PROJECT_FOLDER = Path(__file__).parent.parent
CONCEPTS_FILE = PROJECT_FOLDER / "levels" / "concepts.toml"

MIN_CONCEPTS = 2
MAX_CONCEPTS = 4


class ConceptLevel:
    """One item of concepts.toml: a level or a boss.

    Attributes:
        id: "1-1", or "boss-1" for a boss.
        world: the world number.
        title: the name of the level.
        boss: True for a boss.
        technique: True if the level teaches a method rather than new syntax.
        concepts: the headline concepts (bosses have none).
        constructs: the constructs this item adds to the allowed set.
        recycles: ids of earlier items whose material comes back.
        difficulty: 1 to 5.
        outcomes: outcome codes such as "B1".
        power_up: the command the player earns ("" for bosses).
        story: the story line of the level.
        mission: what the player does.
    """

    def __init__(self, table):
        """Read one [[level]] table from concepts.toml."""
        self.id = table["id"]
        self.world = table["world"]
        self.title = table["title"]
        self.boss = table.get("boss", False)
        self.technique = table.get("technique", False)
        self.concepts = list(table.get("concepts", []))
        self.constructs = list(table["constructs"])
        self.recycles = list(table["recycles"])
        self.difficulty = table["difficulty"]
        self.outcomes = list(table["outcomes"])
        self.power_up = table.get("power_up", "")
        self.story = table.get("story", "")
        self.mission = table.get("mission", "")


class Curriculum:
    """All the items of concepts.toml, in file order.

    "Earlier" always means earlier in this list.

    Attributes:
        items: a list of ConceptLevel.
        outcome_codes: every outcome code that exists, like "B1" or "R10".
    """

    def __init__(self, items, outcome_codes):
        """Remember the items and the outcome codes."""
        self.items = list(items)
        self.outcome_codes = list(outcome_codes)

    def ids(self):
        """Return the ids of all items, in file order."""
        ids = []
        for item in self.items:
            ids.append(item.id)
        return ids

    def index_of(self, item_id):
        """Return the position of an item, or -1 if there is no such item."""
        for index in range(len(self.items)):
            if self.items[index].id == item_id:
                return index
        return -1

    def find(self, item_id):
        """Return the item with this id, or None."""
        index = self.index_of(item_id)
        if index == -1:
            return None
        return self.items[index]

    def allowed_constructs(self, item_id):
        """Return what an item may use, as (construct, id of the item that adds it) pairs.

        This is everything added up to and including the item, in file order.
        Raises KeyError if there is no such item.
        """
        index = self.index_of(item_id)
        if index == -1:
            raise KeyError(item_id)
        pairs = []
        for item in self.items[:index + 1]:
            for construct in item.constructs:
                pairs.append((construct, item.id))
        return pairs

    def allowed_set(self, item_id):
        """Return what an item may use, as a set of construct names."""
        names = set()
        for construct, _ in self.allowed_constructs(item_id):
            names.add(construct)
        return names

    def new_constructs(self, item_id):
        """Return the constructs this item adds. Raises KeyError for an unknown id."""
        item = self.find(item_id)
        if item is None:
            raise KeyError(item_id)
        return list(item.constructs)

    def first_taught(self, option_names):
        """Return the id of the first item that adds any of `option_names`, or None."""
        for item in self.items:
            for name in option_names:
                if name in item.constructs:
                    return item.id
        return None


def parse_curriculum(data):
    """Turn the contents of concepts.toml (a dict) into a Curriculum."""
    items = []
    for table in data["level"]:
        items.append(ConceptLevel(table))
    return Curriculum(items, data["meta"]["outcome_codes"])


def load_curriculum(path=CONCEPTS_FILE):
    """Read levels/concepts.toml (or another file) and return a Curriculum."""
    with open(path, "rb") as concepts_file:
        return parse_curriculum(tomllib.load(concepts_file))


# ---- rules 2-6: the data

def check_item(curriculum, item_id):
    """Return the problems of one item under rules 2, 3, 4, 5 and 6, plus the concept limit."""
    item = curriculum.find(item_id)
    if item is None:
        return [f"{item_id} is not in concepts.toml"]
    problems = []
    problems.extend(check_constructs_rule(item))
    problems.extend(check_outcomes_known(curriculum, item))
    problems.extend(check_difficulty_rule(curriculum, item))
    problems.extend(check_recycles_rule(curriculum, item))
    if not item.boss:
        count = len(item.concepts)
        if count < MIN_CONCEPTS or count > MAX_CONCEPTS:
            problems.append(f"{item.id} has {count} concepts ({MIN_CONCEPTS} to {MAX_CONCEPTS} needed)")
    return problems


def check_constructs_rule(item):
    """Rule 2 (a boss adds nothing) and rule 3 (a level adds something)."""
    if item.boss and item.constructs:
        return [f"rule 2: {item.id} is a boss but adds constructs"]
    if not item.boss and not item.technique and not item.constructs:
        return [f"rule 3: {item.id} adds no construct and is not a technique level"]
    return []


def check_outcomes_known(curriculum, item):
    """Every outcome code of the item exists, and there is at least one."""
    problems = []
    if not item.outcomes:
        problems.append(f"{item.id} has no outcomes")
    for code in item.outcomes:
        if code not in curriculum.outcome_codes:
            problems.append(f"{item.id} names the unknown outcome {code}")
    return problems


def items_of_world(curriculum, world):
    """Return the items of one world, in file order."""
    items = []
    for item in curriculum.items:
        if item.world == world:
            items.append(item)
    return items


def check_difficulty_rule(curriculum, item):
    """Rule 5 for one item.

    It is no easier than the item before it in its world. A boss is at
    least as hard as the hardest level of its world. The first item of a
    world is at most the previous world's boss, minus 1.
    """
    items = items_of_world(curriculum, item.world)
    position = items.index(item)
    if position > 0:
        before = items[position - 1]
        if item.difficulty < before.difficulty:
            return [f"rule 5: {item.id} (difficulty {item.difficulty}) is easier than "
                    f"{before.id} ({before.difficulty}) before it"]
    problems = []
    if item.boss:
        hardest = 0
        for other in items:
            if other.difficulty > hardest:
                hardest = other.difficulty
        if item.difficulty < hardest:
            problems.append(f"rule 5: {item.id} (difficulty {item.difficulty}) is easier "
                            f"than the hardest level of its world ({hardest})")
    if position == 0:
        previous = previous_boss(curriculum, item.world)
        if previous is not None and item.difficulty > previous.difficulty - 1:
            problems.append(f"rule 5: {item.id} (difficulty {item.difficulty}) starts too high "
                            f"after {previous.id} ({previous.difficulty}); at most "
                            f"{previous.difficulty - 1}")
    return problems


def previous_boss(curriculum, world):
    """Return the boss of the closest world before `world`, or None."""
    best = None
    for item in curriculum.items:
        if item.boss and item.world < world:
            if best is None or item.world > best.world:
                best = item
    return best


def check_recycles_rule(curriculum, item):
    """Rule 6: every recycled id exists and comes earlier in the file."""
    problems = []
    own_index = curriculum.index_of(item.id)
    for other_id in item.recycles:
        other_index = curriculum.index_of(other_id)
        if other_index == -1:
            problems.append(f"rule 6: {item.id} recycles {other_id}, which does not exist")
        elif other_index >= own_index:
            problems.append(f"rule 6: {item.id} recycles {other_id}, which does not come earlier")
    return problems


def check_curriculum(curriculum):
    """Return every problem of the whole curriculum: rules 2-6 and the extra checks."""
    problems = []
    seen = []
    for item in curriculum.items:
        if item.id in seen:
            problems.append(f"the id {item.id} is used twice")
        seen.append(item.id)
    for item in curriculum.items:
        problems.extend(check_item(curriculum, item.id))
    problems.extend(check_outcome_coverage(curriculum))
    return problems


def check_outcome_coverage(curriculum):
    """Rule 4: every outcome code appears in at least one item that is not a boss."""
    covered = set()
    for item in curriculum.items:
        if not item.boss:
            covered.update(item.outcomes)
    problems = []
    for code in curriculum.outcome_codes:
        if code not in covered:
            problems.append(f"rule 4: the outcome {code} is not taught by any level (bosses do not count)")
    return problems


# ---- rule 1: the code

def check_code(curriculum, item_id, code, place):
    """Return the rule 1 problems of one piece of code in level `item_id`.

    `place` says where the code is, for example "cutscene". Code that does
    not parse gives no problem here: the style limits report it.
    """
    if curriculum.find(item_id) is None:
        return [f"{place}: {item_id} is not in concepts.toml"]
    try:
        needs = find_needs(code)
    except SyntaxError:
        return []
    allowed = curriculum.allowed_set(item_id)
    problems = []
    for need in needs:
        if not any_allowed(need.options, allowed):
            problems.append(f"{place}: rule 1: line {need.line} uses {need.label} "
                            f"({where_taught(curriculum, need.options)})")
    return problems


def any_allowed(options, allowed):
    """Return True if any of `options` is in the allowed set."""
    for option in options:
        if option in allowed:
            return True
    return False


def where_taught(curriculum, options):
    """Say where a construct is taught: "taught in 1-3" or "not listed in concepts.toml"."""
    first = curriculum.first_taught(options)
    if first is None:
        return "not listed in concepts.toml"
    return f"taught in {first}"


def code_fields(level):
    """Return the pieces of code of a level that rule 1 looks at.

    Each is a pair (place, code). The cutscene, references and debug code
    must follow the rule. A starter and a wrong solution are listed too,
    but code that does not parse gives no problem (see check_code). The
    output a player types in a predict wave (answer and wrong) is text, not
    code, and is not listed.
    """
    fields = [("cutscene", level.cutscene)]
    number = 0
    for wave in level.waves:
        number = number + 1
        place = f"wave {number} ({wave.kind})"
        if wave.mode == "predict":
            fields.append((place + " code", wave.code))
            continue
        if wave.is_quiz():
            for question in wave.questions:
                if "code" in question:
                    fields.append((place + " question code", question["code"]))
            continue
        if wave.starter is not None:
            fields.append((place + " starter", wave.starter))
        if wave.reference is not None:
            fields.append((place + " reference", wave.reference))
        if wave.wrong is not None:
            fields.append((place + " wrong", wave.wrong))
    return fields


def check_level_code(curriculum, level):
    """Return the rule 1 problems of all the code in `level` (an engine Level)."""
    if curriculum.find(level.id) is None:
        return [f"{level.id} is not in concepts.toml"]
    problems = []
    for place, code in code_fields(level):
        problems.extend(check_code(curriculum, level.id, code, place))
    return problems


def check_level_matches(curriculum, level):
    """Return where a level file differs from its entry in concepts.toml."""
    item = curriculum.find(level.id)
    if item is None:
        return [f"{level.id} is not in concepts.toml"]
    problems = []
    if level.title != item.title:
        problems.append(f"title is {level.title!r}, concepts.toml says {item.title!r}")
    if level.world != item.world:
        problems.append(f"world is {level.world}, concepts.toml says {item.world}")
    if level.boss != item.boss:
        problems.append(f"boss is {level.boss}, concepts.toml says {item.boss}")
    if not item.boss and level.new_concepts != item.concepts:
        problems.append("new_concepts differ from concepts in concepts.toml")
    if not item.boss and level.power_up != item.power_up:
        problems.append(f"power_up is {level.power_up!r}, concepts.toml says {item.power_up!r}")
    return problems
