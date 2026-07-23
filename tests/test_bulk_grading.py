from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace


def _load_addon_module() -> ModuleType:
    addon_path = Path(__file__).resolve().parents[1] / "__init__.py"
    spec = importlib.util.spec_from_file_location("study_triage_grading_under_test", addon_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load Study Triage add-on module")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeBackend:
    def __init__(self) -> None:
        self.calls: list[tuple[list[int], int]] = []

    def grade_now(self, *, card_ids: list[int], rating: int) -> SimpleNamespace:
        self.calls.append((card_ids, rating))
        return SimpleNamespace(card=True)


class _RejectingScheduler:
    def answerCard(self, _card: object, _ease: int) -> None:
        raise AssertionError("per-card reviewer API must not be called")


class _FallbackScheduler:
    def __init__(self) -> None:
        self.answered: list[tuple[int, int]] = []

    def answerCard(self, card: SimpleNamespace, ease: int) -> None:
        self.answered.append((card.id, ease))


class NativeBulkGradingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.addon = _load_addon_module()

    def test_good_uses_native_bulk_grader_for_arbitrary_card_ids(self) -> None:
        backend = _FakeBackend()
        collection = SimpleNamespace(
            _backend=backend,
            sched=_RejectingScheduler(),
            undo_status=lambda: SimpleNamespace(last_step=42),
        )
        card_ids = [109, 103, 107]

        answered, failed, cancelled, changes, undo_target = (
            self.addon._answer_card_ids_with_progress(
                collection,
                card_ids,
                self.addon.EASE_GOOD,
                "grading",
                background=True,
            )
        )

        self.assertEqual(backend.calls, [(card_ids, 2)])
        self.assertEqual(answered, len(card_ids))
        self.assertEqual(failed, [])
        self.assertFalse(cancelled)
        self.assertTrue(changes.card)
        self.assertEqual(undo_target, 42)

    def test_easy_maps_to_native_easy_rating(self) -> None:
        backend = _FakeBackend()
        collection = SimpleNamespace(
            _backend=backend,
            sched=_RejectingScheduler(),
            undo_status=lambda: SimpleNamespace(last_step=43),
        )

        result = self.addon._answer_card_ids_with_progress(
            collection,
            [201, 202],
            self.addon.EASE_EASY,
            "grading",
            background=True,
        )

        self.assertEqual(backend.calls, [([201, 202], 3)])
        self.assertEqual(result[0], 2)
        self.assertEqual(result[1], [])

    def test_older_anki_without_native_bulk_grader_keeps_per_card_fallback(self) -> None:
        scheduler = _FallbackScheduler()
        cards = {
            card_id: SimpleNamespace(id=card_id, start_timer=lambda: None)
            for card_id in (301, 302)
        }
        collection = SimpleNamespace(
            _backend=SimpleNamespace(),
            sched=scheduler,
            get_card=lambda card_id: cards[card_id],
            undo_status=lambda: SimpleNamespace(last_step=44),
        )

        result = self.addon._answer_card_ids_with_progress(
            collection,
            [301, 302],
            self.addon.EASE_GOOD,
            "grading",
            background=True,
        )

        self.assertEqual(scheduler.answered, [(301, 3), (302, 3)])
        self.assertEqual(result[0], 2)
        self.assertEqual(result[1], [])


if __name__ == "__main__":
    unittest.main()
