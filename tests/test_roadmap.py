"""Tests for engine/roadmap.py and the map built from concepts.toml.

The curriculum lists every level of a world; only some have a pack yet.
The map shows them all, and a level without a pack is locked.
"""

import unittest

from engine.commands import handle_line
from engine.game_state import GameState
from engine.hud import hud_text, map_status
from engine.rewards import next_level
from engine.roadmap import MissingLevel, build_slots, is_written
from tests.helpers import make_curriculum_of, make_levels

WORLD_ONE = ("1-1", "1-2", "1-3", "boss-1")


def slot_ids(slots):
    """Return the ids of a list of slots."""
    ids = []
    for slot in slots:
        ids.append(slot.id)
    return ids


class TestBuildSlots(unittest.TestCase):
    """One slot for each item of the curriculum."""

    def test_slots_follow_the_curriculum_order(self):
        """The slots are in curriculum order, whatever order the packs came in."""
        curriculum = make_curriculum_of(*WORLD_ONE, "2-1")
        levels = make_levels("1-3", "1-1")
        self.assertEqual(slot_ids(build_slots(levels, curriculum)), ["1-1", "1-2", "1-3", "boss-1", "2-1"])

    def test_a_pack_fills_its_slot_with_the_real_level(self):
        """A slot with a pack holds that very Level."""
        levels = make_levels("1-1")
        slots = build_slots(levels, make_curriculum_of(*WORLD_ONE))
        self.assertIs(slots[0], levels[0])
        self.assertTrue(is_written(slots[0]))

    def test_a_slot_without_a_pack_is_a_missing_level(self):
        """It has the id, title, world and boss flag from the curriculum."""
        slots = build_slots(make_levels("1-1"), make_curriculum_of(*WORLD_ONE))
        missing = slots[1]
        self.assertIsInstance(missing, MissingLevel)
        self.assertFalse(is_written(missing))
        self.assertEqual((missing.id, missing.title, missing.world, missing.boss),
                         ("1-2", "Title 1-2", 1, False))
        self.assertTrue(slots[3].boss)

    def test_without_a_curriculum_the_slots_are_the_levels(self):
        """No curriculum: the map is made of the packs, as before."""
        levels = make_levels("1-1", "1-2")
        self.assertEqual(build_slots(levels, None), levels)

    def test_a_pack_that_is_not_in_the_curriculum_has_no_slot(self):
        """The curriculum decides what is on the map."""
        slots = build_slots(make_levels("1-1", "9-9"), make_curriculum_of(*WORLD_ONE))
        self.assertNotIn("9-9", slot_ids(slots))


class TestGameStateSlots(unittest.TestCase):
    """GameState hands out the slots."""

    def setUp(self):
        """A World 1 with packs for 1-1 and 1-3, and a World 2 with none."""
        self.state = GameState(make_levels("1-1", "1-3"), curriculum=make_curriculum_of(*WORLD_ONE, "2-1"))

    def test_slots_in_world(self):
        """Only that world's slots, in order, written or not."""
        self.assertEqual(slot_ids(self.state.slots_in_world(1)), list(WORLD_ONE))
        self.assertEqual(slot_ids(self.state.slots_in_world(2)), ["2-1"])

    def test_find_slot(self):
        """find_slot finds written and missing levels, and gives None for unknown ids."""
        self.assertIs(self.state.find_slot("1-1"), self.state.levels[0])
        self.assertIsInstance(self.state.find_slot("1-2"), MissingLevel)
        self.assertIsNone(self.state.find_slot("9-9"))

    def test_levels_stay_the_packs(self):
        """state.levels is still only the levels that exist."""
        self.assertEqual(slot_ids(self.state.levels), ["1-1", "1-3"])

    def test_current_world_without_packs_is_the_first_world(self):
        """A game with a curriculum but no packs starts in World 1."""
        state = GameState(curriculum=make_curriculum_of(*WORLD_ONE))
        self.assertEqual(state.current_world(), 1)

    def test_current_world_without_either_is_none(self):
        """No packs and no curriculum: no world."""
        self.assertIsNone(GameState().current_world())


class TestLocks(unittest.TestCase):
    """A level opens when the slot before it is cleared; a missing level never opens."""

    def locked_for(self, pack_ids, cleared):
        """Return the lock flags of the four World 1 slots."""
        state = GameState(make_levels(*pack_ids), curriculum=make_curriculum_of(*WORLD_ONE))
        state.cleared = list(cleared)
        return map_status(state, state.slots_in_world(1)).locked

    def test_only_the_first_level_is_open_at_the_start(self):
        """Nothing cleared: 1-1 is open, the rest locked."""
        self.assertEqual(self.locked_for(["1-1", "1-2"], []), [False, True, True, True])

    def test_a_missing_level_stays_locked_even_when_the_one_before_is_cleared(self):
        """1-1 is cleared but 1-2 has no pack."""
        self.assertEqual(self.locked_for(["1-1"], ["1-1"]), [False, True, True, True])

    def test_a_written_level_opens_when_the_one_before_is_cleared(self):
        """1-2 has a pack, so clearing 1-1 opens it."""
        self.assertEqual(self.locked_for(["1-1", "1-2"], ["1-1"]), [False, False, True, True])

    def test_a_pack_after_a_gap_stays_locked(self):
        """1-3 has a pack, but 1-2 does not, so 1-3 cannot be reached."""
        self.assertEqual(self.locked_for(["1-1", "1-3"], ["1-1"]), [False, True, True, True])

    def test_hud_counts_stars_over_every_slot(self):
        """Four slots make 12 possible stars."""
        state = GameState(make_levels("1-1"), curriculum=make_curriculum_of(*WORLD_ONE))
        self.assertIn("★ 0/12", hud_text(state, state.slots_in_world(1)))


class TestNextLevel(unittest.TestCase):
    """Clearing a level only opens a level that exists."""

    def test_next_written_level(self):
        """With a pack for 1-2, it opens after 1-1."""
        state = GameState(make_levels("1-1", "1-2"), curriculum=make_curriculum_of(*WORLD_ONE))
        self.assertEqual(next_level(state, state.levels[0]).id, "1-2")

    def test_next_level_that_is_missing_is_none(self):
        """1-2 has no pack, so nothing opens."""
        state = GameState(make_levels("1-1"), curriculum=make_curriculum_of(*WORLD_ONE))
        self.assertIsNone(next_level(state, state.levels[0]))

    def test_without_a_curriculum_it_is_the_next_pack(self):
        """As before: the next level in the list."""
        state = GameState(make_levels("1-1", "1-2"))
        self.assertEqual(next_level(state, state.levels[0]).id, "1-2")
        self.assertIsNone(next_level(state, state.levels[1]))


class TestCommands(unittest.TestCase):
    """What the player sees."""

    def setUp(self):
        """A game with a pack for 1-1 only, in a four-slot World 1."""
        self.state = GameState(make_levels("1-1"), curriculum=make_curriculum_of(*WORLD_ONE))

    def test_map_shows_every_node_of_the_world(self):
        """All four labels are on the map."""
        text = handle_line(self.state, "map")
        for label in ("[1-1]", "[1-2]", "[1-3]", "[boss-1]"):
            self.assertIn(label, text)

    def test_map_without_any_pack_still_draws_the_world(self):
        """A game with a curriculum and no packs shows a locked world, not 'No levels found'."""
        state = GameState(curriculum=make_curriculum_of(*WORLD_ONE))
        text = handle_line(state, "map")
        self.assertNotIn("No levels found", text)
        self.assertIn("[1-1]", text)

    def test_map_without_packs_or_curriculum_says_so(self):
        """As before."""
        self.assertIn("No levels found", handle_line(GameState(), "map"))

    def test_play_a_level_that_is_not_written_yet(self):
        """The message says so, and names the level."""
        text = handle_line(self.state, "play 1-2")
        self.assertIn("1-2", text)
        self.assertIn("not written yet", text)
        self.assertIsNone(self.state.current_level)

    def test_play_an_unknown_level(self):
        """An id that is not in the curriculum is still 'no level'."""
        self.assertIn("There is no level 9-9", handle_line(self.state, "play 9-9"))

    def test_play_the_first_level_still_works(self):
        """1-1 has a pack and is open."""
        handle_line(self.state, "play 1-1")
        self.assertEqual(self.state.current_level, "1-1")

    def test_play_a_level_after_a_gap_says_which_level_to_clear(self):
        """1-3 has a pack but 1-2 has none: it is locked, and the message names 1-2."""
        state = GameState(make_levels("1-1", "1-3"), curriculum=make_curriculum_of(*WORLD_ONE))
        text = handle_line(state, "play 1-3")
        self.assertIn("locked", text)
        self.assertIn("1-2", text)


if __name__ == "__main__":
    unittest.main()
