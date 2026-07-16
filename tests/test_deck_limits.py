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
        self.update_count = 0

    def get(self, _deck_id: int) -> dict[str, object]:
        return self.deck

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
        self.assertEqual(collection.decks.update_count, 1)
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


if __name__ == "__main__":
    unittest.main()
