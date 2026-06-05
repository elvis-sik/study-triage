from __future__ import annotations

import importlib
import json
import os
import traceback
from pathlib import Path
from typing import Any

from aqt import gui_hooks, mw
from aqt.qt import QApplication, QMenu, QPoint, QTimer, Qt

try:
    from aqt.qt import QTest
except ImportError:
    try:
        from PyQt6.QtTest import QTest
    except ImportError:
        from PyQt5.QtTest import QTest


MENU_LABEL = "Study Triage"
EXPECTED_ACTIONS = [
    "Set Today's New Cards to 0",
    "Answer Due Cards as Good",
    "Answer Due Cards as Easy",
]


def _normal_text(text: str) -> str:
    return text.replace("&", "").strip()


def _action_snapshot(menu: QMenu) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for action in menu.actions():
        submenu = action.menu()
        item: dict[str, Any] = {
            "text": _normal_text(action.text()),
            "enabled": bool(action.isEnabled()),
            "separator": bool(action.isSeparator()),
        }
        if submenu is not None:
            item["submenu"] = _action_snapshot(submenu)
        items.append(item)
    return items


def _find_menu(items: list[dict[str, Any]], label: str) -> dict[str, Any] | None:
    for item in items:
        if item.get("text") == label and "submenu" in item:
            return item
    return None


def _find_qmenu(menu: QMenu, label: str) -> QMenu:
    for action in menu.actions():
        submenu = action.menu()
        if _normal_text(action.text()) == label and submenu is not None:
            return submenu
    raise AssertionError(f"missing submenu: {label}")


def _find_qaction(menu: QMenu, label: str):
    for action in menu.actions():
        if not action.isSeparator() and _normal_text(action.text()) == label:
            return action
    raise AssertionError(f"missing action: {label}")


def _action_texts(items: list[dict[str, Any]]) -> list[str]:
    return [
        str(item.get("text", ""))
        for item in items
        if not item.get("separator") and item.get("text")
    ]


def _assert_expected_actions(items: list[dict[str, Any]]) -> None:
    texts = _action_texts(items)
    missing = [label for label in EXPECTED_ACTIONS if label not in texts]
    if missing:
        raise AssertionError(f"missing action(s): {', '.join(missing)}")


def _ensure_smoke_deck_id() -> int:
    assert mw is not None
    assert mw.col is not None
    deck_id = int(mw.col.decks.id("Study Triage GUI Smoke"))
    mw.col.decks.set_current(deck_id)
    return deck_id


def _qt_left_button():
    return getattr(getattr(Qt, "MouseButton", Qt), "LeftButton")


def _qt_no_modifier():
    return getattr(getattr(Qt, "KeyboardModifier", Qt), "NoModifier")


def _process_events(milliseconds: int = 50) -> None:
    app = QApplication.instance()
    if app is not None:
        app.processEvents()
    QTest.qWait(milliseconds)
    if app is not None:
        app.processEvents()


def _click_menu_action(menu: QMenu, action_label: str) -> None:
    action = _find_qaction(menu, action_label)
    menu.adjustSize()
    menu.popup(mw.mapToGlobal(QPoint(80, 80)))
    _process_events(100)

    rect = menu.actionGeometry(action)
    if not rect.isValid():
        raise AssertionError(f"action has no clickable geometry: {action_label}")

    click_point = rect.center()
    menu.setActiveAction(action)
    QTest.mouseMove(menu, click_point)
    _process_events(50)
    QTest.mouseClick(menu, _qt_left_button(), _qt_no_modifier(), click_point)
    _process_events(150)

    if menu.isVisible():
        menu.hide()
        _process_events(50)


def _run_deck_menu_interaction(deck_id: int) -> dict[str, Any]:
    assert mw is not None
    assert mw.col is not None

    study_triage = importlib.import_module("study_triage")
    setup_limit = 7
    if not study_triage._set_today_new_limit(mw.col, deck_id, setup_limit):
        raise AssertionError("could not set up a nonzero today-only new-card limit")
    if not study_triage._deck_limit_matches(mw.col, deck_id, setup_limit):
        raise AssertionError("smoke deck did not report the setup new-card limit")

    deck_menu = QMenu(mw)
    gui_hooks.deck_browser_will_show_options_menu(deck_menu, deck_id)
    triage_menu = _find_qmenu(deck_menu, MENU_LABEL)

    triggered = {"count": 0}
    zero_action = _find_qaction(triage_menu, "Set Today's New Cards to 0")
    zero_action.triggered.connect(
        lambda _checked=False: triggered.__setitem__("count", triggered["count"] + 1)
    )

    _click_menu_action(triage_menu, "Set Today's New Cards to 0")

    if triggered["count"] != 1:
        raise AssertionError(
            f"expected one Qt-triggered menu activation, got {triggered['count']}"
        )
    if not study_triage._deck_limit_matches(mw.col, deck_id, 0):
        raise AssertionError("clicked menu action did not set the deck limit to 0")

    return {
        "action": "Set Today's New Cards to 0",
        "before_new_today": setup_limit,
        "after_new_today": 0,
        "triggered_count": triggered["count"],
        "via": "QTest.mouseClick on deck submenu QMenu action",
    }


def _run_smoke() -> dict[str, Any]:
    assert mw is not None
    assert mw.col is not None

    tools_menu = mw.form.menuTools
    tools_items = _action_snapshot(tools_menu)
    tools_submenu = _find_menu(tools_items, MENU_LABEL)
    if tools_submenu is None:
        raise AssertionError("Tools menu is missing Study Triage submenu")
    _assert_expected_actions(list(tools_submenu["submenu"]))

    deck_id = _ensure_smoke_deck_id()
    deck_menu = QMenu(mw)
    gui_hooks.deck_browser_will_show_options_menu(deck_menu, deck_id)
    deck_items = _action_snapshot(deck_menu)
    deck_submenu = _find_menu(deck_items, MENU_LABEL)
    if deck_submenu is None:
        raise AssertionError("deck options menu is missing Study Triage submenu")
    _assert_expected_actions(list(deck_submenu["submenu"]))

    zero_action = next(
        (
            item
            for item in deck_submenu["submenu"]
            if item.get("text") == "Set Today's New Cards to 0"
        ),
        None,
    )
    if not zero_action or not zero_action.get("enabled"):
        raise AssertionError("deck-specific zero-new action should be enabled")

    interaction = _run_deck_menu_interaction(deck_id)

    return {
        "ok": True,
        "tools_menu": tools_items,
        "deck_menu": deck_items,
        "deck_id": deck_id,
        "interaction": interaction,
        "anki_version": getattr(mw, "appVersion", None),
    }


def _write_result(payload: dict[str, Any]) -> None:
    path = os.environ.get("ANKI_ADDON_WORKBENCH_RESULT") or os.environ.get(
        "STUDY_TRIAGE_GUI_SMOKE_RESULT"
    )
    if not path:
        return

    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _save_screenshot() -> str | None:
    path = os.environ.get("ANKI_ADDON_WORKBENCH_SCREENSHOT") or os.environ.get(
        "STUDY_TRIAGE_GUI_SMOKE_SCREENSHOT"
    )
    if not path or mw is None:
        return None

    screenshot_path = Path(path)
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    pixmap = mw.grab()
    if not pixmap.save(str(screenshot_path), "PNG"):
        raise RuntimeError(f"failed to save screenshot to {screenshot_path}")
    return str(screenshot_path)


def _finish() -> None:
    if mw is None:
        return
    mw.unloadProfileAndExit()


def _run_and_quit() -> None:
    try:
        result = _run_smoke()
    except Exception as exc:
        result = {
            "ok": False,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }

    try:
        screenshot = _save_screenshot()
        if screenshot:
            result["screenshot"] = screenshot
    except Exception as exc:
        result["screenshot_error"] = str(exc)

    _write_result(result)
    QTimer.singleShot(100, _finish)


def _schedule_smoke() -> None:
    QTimer.singleShot(500, _run_and_quit)


gui_hooks.main_window_did_init.append(_schedule_smoke)
