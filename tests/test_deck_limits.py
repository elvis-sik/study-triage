from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


def _load_addon_module() -> ModuleType:
    addon_path = Path(__file__).resolve().parents[1] / "__init__.py"
    spec = importlib.util.spec_from_file_location("study_triage_limits_under_test", addon_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load Study Triage add-on module")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeLimits:
    def __init__(
        self,
        *,
        review_today: int | None,
        review_today_active: bool,
        new_today: int | None = None,
        new_today_active: bool = False,
    ) -> None:
        self.review_today = review_today
        self.review_today_active = review_today_active
        self.new_today = new_today
        self.new_today_active = new_today_active

    def CopyFrom(self, other: "_FakeLimits") -> None:
        self.review_today = other.review_today
        self.review_today_active = other.review_today_active
        self.new_today = other.new_today
        self.new_today_active = other.new_today_active

    def ClearField(self, field: str) -> None:
        setattr(self, field, None)


class _FakeConfigs:
    def __init__(self) -> None:
        self.values: list[object] = []

    def add(self) -> SimpleNamespace:
        entry = SimpleNamespace(CopyFrom=lambda value: self.values.append(value))
        return entry


class _FakeUpdateDeckConfigs:
    def __init__(self) -> None:
        self.configs = _FakeConfigs()
        self.limits = _FakeLimits(review_today=None, review_today_active=False)


class _FakeDeckManager:
    def __init__(self, limits: _FakeLimits) -> None:
        self.state = SimpleNamespace(
            current_deck=SimpleNamespace(config_id=7, limits=limits),
            all_config=[SimpleNamespace(config=SimpleNamespace(id=7))],
        )
        self.last_request: _FakeUpdateDeckConfigs | None = None

    def get_deck_configs_for_update(self, _deck_id: int) -> SimpleNamespace:
        return self.state

    def update_deck_configs(self, request: _FakeUpdateDeckConfigs) -> None:
        self.last_request = request
        request.limits.new_today_active = True
        self.state.current_deck.limits = request.limits


class DeckLimitUpdateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.addon = _load_addon_module()
        anki_module = ModuleType("anki")
        decks_module = ModuleType("anki.decks")
        decks_module.UpdateDeckConfigs = _FakeUpdateDeckConfigs
        anki_module.decks = decks_module
        self.anki_modules = {"anki": anki_module, "anki.decks": decks_module}

    def test_inactive_stale_review_limit_is_not_reactivated(self) -> None:
        decks = _FakeDeckManager(
            _FakeLimits(review_today=0, review_today_active=False, new_today=11)
        )
        collection = SimpleNamespace(decks=decks)

        with patch.dict(sys.modules, self.anki_modules):
            changed = self.addon._set_today_new_limit_via_deck_configs(collection, 123, 0)

        self.assertTrue(changed)
        self.assertIsNotNone(decks.last_request)
        self.assertIsNone(decks.last_request.limits.review_today)
        self.assertEqual(decks.last_request.limits.new_today, 0)

    def test_active_review_limit_is_preserved(self) -> None:
        decks = _FakeDeckManager(
            _FakeLimits(review_today=23, review_today_active=True, new_today=11)
        )
        collection = SimpleNamespace(decks=decks)

        with patch.dict(sys.modules, self.anki_modules):
            changed = self.addon._set_today_new_limit_via_deck_configs(collection, 123, 0)

        self.assertTrue(changed)
        self.assertIsNotNone(decks.last_request)
        self.assertEqual(decks.last_request.limits.review_today, 23)
        self.assertEqual(decks.last_request.limits.new_today, 0)


if __name__ == "__main__":
    unittest.main()
