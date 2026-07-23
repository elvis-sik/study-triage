from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace


def _load_addon_module() -> ModuleType:
    addon_path = Path(__file__).resolve().parents[1] / "__init__.py"
    spec = importlib.util.spec_from_file_location("study_triage_limits_under_test", addon_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load Study Triage add-on module")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeDeckManager:
    def __init__(self, deck: dict[str, object]) -> None:
        self.deck = deck
        self.update_dict_count = 0
        self.update_count = 0

    def get(self, _deck_id: int) -> dict[str, object]:
        return self.deck

    def update_dict(self, deck: dict[str, object]) -> None:
        self.deck = deck
        self.update_dict_count += 1

    def update(self, deck: dict[str, object]) -> None:
        self.deck = deck
        self.update_count += 1

    def get_deck_configs_for_update(self, _deck_id: int) -> None:
        raise AssertionError("whole deck-options API must not be called")

    def update_deck_configs(self, _request: object) -> None:
        raise AssertionError("whole deck-options API must not be called")


class DeckLimitUpdateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.addon = _load_addon_module()

    def _collection(self, review_today: dict[str, int]) -> SimpleNamespace:
        deck = {
            "id": 123,
            "newLimitToday": {"limit": 17, "today": 98},
            "reviewLimitToday": copy.deepcopy(review_today),
            "extendNew": 4,
            "extendRev": 9,
        }
        return SimpleNamespace(
            decks=_FakeDeckManager(deck),
            sched=SimpleNamespace(today=99),
            usn=lambda: -1,
        )

    def test_stale_review_limit_is_byte_for_byte_unchanged(self) -> None:
        review_before = {"limit": 0, "today": 98}
        collection = self._collection(review_before)

        changed = self.addon._set_today_new_limit(collection, 123, 0)

        self.assertTrue(changed)
        self.assertEqual(collection.decks.update_dict_count, 1)
        self.assertEqual(collection.decks.update_count, 0)
        self.assertEqual(collection.decks.deck["reviewLimitToday"], review_before)
        self.assertEqual(collection.decks.deck["newLimitToday"], {"limit": 0, "today": 99})
        self.assertEqual(collection.decks.deck["extendNew"], 4)
        self.assertEqual(collection.decks.deck["extendRev"], 9)

    def test_active_review_limit_is_byte_for_byte_unchanged(self) -> None:
        review_before = {"limit": 23, "today": 99}
        collection = self._collection(review_before)

        changed = self.addon._set_today_new_limit(collection, 123, 0)

        self.assertTrue(changed)
        self.assertEqual(collection.decks.deck["reviewLimitToday"], review_before)
        self.assertEqual(collection.decks.deck["newLimitToday"], {"limit": 0, "today": 99})


class _UndoAwareDeckManager:
    def __init__(self, collection: "_UndoAwareCollection", deck_count: int) -> None:
        self.collection = collection
        self.decks = {
            deck_id: {
                "id": deck_id,
                "name": f"Deck {deck_id:03d}",
                "dyn": 0,
                "newLimitToday": {"limit": 17, "today": 98},
            }
            for deck_id in range(1, deck_count + 1)
        }

    def get(self, deck_id: int) -> dict[str, object]:
        return self.decks[deck_id]

    def update_dict(self, deck: dict[str, object]) -> None:
        self.decks[int(deck["id"])] = deck
        self.collection.add_undo_step()


class _UndoAwareCollection:
    def __init__(self, deck_count: int) -> None:
        self.sched = SimpleNamespace(today=99)
        self.decks = _UndoAwareDeckManager(self, deck_count)
        self.undo_steps: list[int] = []
        self.next_undo_step = 1
        self.merge_count = 0

    def usn(self) -> int:
        return -1

    def add_undo_step(self) -> int:
        step = self.next_undo_step
        self.next_undo_step += 1
        self.undo_steps.append(step)
        return step

    def add_custom_undo_entry(self, _name: str) -> int:
        return self.add_undo_step()

    def merge_undo_entries(self, target: int) -> None:
        if target not in self.undo_steps:
            raise RuntimeError("target undo op not found")
        target_index = self.undo_steps.index(target)
        self.undo_steps = self.undo_steps[: target_index + 1]
        self.merge_count += 1


class DeckLimitUndoGroupingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.addon = _load_addon_module()

    def test_large_collection_uses_undoable_deck_updates_and_keeps_group_target(self) -> None:
        collection = _UndoAwareCollection(deck_count=61)
        targets = [
            (deck_id, str(deck["name"]))
            for deck_id, deck in collection.decks.decks.items()
        ]

        changed, failed, undo_available, undo_error = (
            self.addon._set_today_new_limit_for_targets(collection, targets, 0)
        )

        self.assertEqual(len(changed), 61)
        self.assertEqual(failed, [])
        self.assertTrue(undo_available)
        self.assertIsNone(undo_error)
        self.assertGreater(collection.merge_count, 1)
        self.assertEqual(len(collection.undo_steps), 1)


if __name__ == "__main__":
    unittest.main()
