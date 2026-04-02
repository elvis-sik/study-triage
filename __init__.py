from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

try:
    from aqt import gui_hooks, mw
    from aqt.qt import QAction
    from aqt.utils import askUser, showInfo, tooltip
except Exception:  # pragma: no cover
    gui_hooks = None
    mw = None
    QAction = None
    askUser = None
    showInfo = None
    tooltip = None


MENU_LABEL = "Zero Today's New Cards"

_menu_action: Optional[QAction] = None


def _setup_menu() -> None:
    global _menu_action

    if mw is None or QAction is None or _menu_action is not None:
        return

    _menu_action = QAction(MENU_LABEL, mw)
    _menu_action.triggered.connect(_zero_today_new_cards)
    mw.form.menuTools.addAction(_menu_action)


def _zero_today_new_cards() -> None:
    if mw is None or mw.col is None:
        return

    if askUser is not None:
        confirmed = askUser(
            "Set 'Today only' new cards/day to 0 for every regular deck in this collection?\n\n"
            "This only affects today and will reset automatically tomorrow.",
            parent=mw,
        )
        if not confirmed:
            return

    targets = _collect_target_decks(mw.col)
    if not targets:
        if showInfo is not None:
            showInfo("No regular decks were found in this collection.", parent=mw)
        return

    changed: List[str] = []
    failed: List[str] = []
    for deck_id, name in targets:
        if _set_today_new_limit(mw.col, deck_id, 0):
            changed.append(name)
        else:
            failed.append(name)

    try:
        mw.reset()
    except Exception:
        pass

    if failed and showInfo is not None:
        details = "\n".join(failed[:15])
        more = ""
        if len(failed) > 15:
            more = f"\n...and {len(failed) - 15} more."
        showInfo(
            f"Set today's new-card limit to 0 for {len(changed)} deck(s), "
            f"but failed on {len(failed)} deck(s):\n\n{details}{more}",
            parent=mw,
        )
        return

    if tooltip is not None:
        tooltip(
            f"Set Today only new/day = 0 for {len(changed)} deck(s).",
            parent=mw,
            period=4000,
        )


def _collect_target_decks(col) -> List[Tuple[int, str]]:
    decks = getattr(col, "decks", None)
    if decks is None:
        return []

    entries: List[object] = []
    all_names_and_ids = getattr(decks, "all_names_and_ids", None)
    if callable(all_names_and_ids):
        try:
            entries = list(all_names_and_ids())
        except Exception:
            entries = []

    if not entries:
        all_decks = getattr(decks, "all", None)
        if callable(all_decks):
            try:
                entries = list(all_decks())
            except Exception:
                entries = []

    collected: List[Tuple[int, str]] = []
    seen_ids = set()
    for entry in entries:
        name, deck_id = _deck_name_and_id(entry)
        if name is None or deck_id is None or deck_id in seen_ids:
            continue

        deck = _get_deck(col, deck_id)
        if not isinstance(deck, dict) or bool(deck.get("dyn")):
            continue

        seen_ids.add(deck_id)
        collected.append((deck_id, name))

    collected.sort(key=lambda item: item[1].lower())
    return collected


def _deck_name_and_id(entry: object) -> Tuple[Optional[str], Optional[int]]:
    name = None
    deck_id = None

    if isinstance(entry, dict):
        name = entry.get("name")
        deck_id = entry.get("id")
    elif hasattr(entry, "name") and hasattr(entry, "id"):
        name = getattr(entry, "name", None)
        deck_id = getattr(entry, "id", None)
    elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
        first, second = entry[0], entry[1]
        if isinstance(first, str):
            name = first
            deck_id = second
        else:
            deck_id = first
            name = second

    if name is None or deck_id is None:
        return (None, None)

    try:
        return (str(name), int(deck_id))
    except Exception:
        return (None, None)


def _set_today_new_limit(col, deck_id: int, limit: int) -> bool:
    limit = int(limit)

    if _set_today_new_limit_via_deck_configs(col, deck_id, limit):
        return True

    if _set_today_new_limit_on_deck(col, deck_id, limit):
        return True

    for obj in (getattr(col, "decks", None), getattr(col, "sched", None)):
        if obj is None or not hasattr(obj, "set_today_limit"):
            continue
        try:
            obj.set_today_limit(deck_id, "new", limit)
            if _deck_limit_matches(col, deck_id, limit):
                return True
        except TypeError:
            try:
                obj.set_today_limit(deck_id, limit)
                if _deck_limit_matches(col, deck_id, limit):
                    return True
            except Exception:
                pass
        except Exception:
            pass

    if _set_today_new_limit_with_scheduler(col, deck_id, limit):
        return True

    return False


def _set_today_new_limit_via_deck_configs(col, deck_id: int, limit: int) -> bool:
    decks = getattr(col, "decks", None)
    if decks is None:
        return False
    if not hasattr(decks, "get_deck_configs_for_update") or not hasattr(decks, "update_deck_configs"):
        return False

    try:
        from anki.decks import UpdateDeckConfigs
    except Exception:
        return False

    try:
        state = decks.get_deck_configs_for_update(deck_id)
    except Exception:
        return False

    current_deck = getattr(state, "current_deck", None)
    if current_deck is None:
        return False

    selected_config = None
    current_config_id = getattr(current_deck, "config_id", None)
    for entry in getattr(state, "all_config", []):
        config = getattr(entry, "config", None)
        if config is not None and getattr(config, "id", None) == current_config_id:
            selected_config = config
            break
    if selected_config is None:
        return False

    try:
        req = UpdateDeckConfigs()
        req.target_deck_id = int(deck_id)
        req.mode = 0
        req.card_state_customizer = getattr(state, "card_state_customizer", "")
        req.new_cards_ignore_review_limit = bool(
            getattr(state, "new_cards_ignore_review_limit", False)
        )
        req.apply_all_parent_limits = bool(getattr(state, "apply_all_parent_limits", False))
        req.fsrs = bool(getattr(state, "fsrs", False))
        req.fsrs_health_check = bool(getattr(state, "fsrs_health_check", False))
        req.configs.add().CopyFrom(selected_config)
        req.limits.CopyFrom(current_deck.limits)
        req.limits.new_today = int(limit)
        decks.update_deck_configs(req)
    except Exception:
        return False

    return _deck_limit_matches(col, deck_id, limit)


def _set_today_new_limit_with_scheduler(col, deck_id: int, limit: int) -> bool:
    sched = getattr(col, "sched", None)
    if sched is None or not hasattr(sched, "update_stats"):
        return False

    base_new_limit = _base_new_limit(col, deck_id)
    if base_new_limit is None:
        return False

    new_today = _new_count_today(col, deck_id)
    desired_remaining = max(0, int(limit) - new_today)
    delta = int(base_new_limit) - new_today - desired_remaining

    try:
        sched.update_stats(deck_id, new_delta=int(delta))
        return _deck_limit_matches(col, deck_id, limit)
    except TypeError:
        try:
            sched.update_stats(deck_id, int(delta))
            return _deck_limit_matches(col, deck_id, limit)
        except Exception:
            return False
    except Exception:
        return False


def _set_today_new_limit_on_deck(col, deck_id: int, limit: int) -> bool:
    deck = _get_deck(col, deck_id)
    if not isinstance(deck, dict):
        return False

    base_new_limit = _base_new_limit(col, deck_id)
    updated = False
    if "newLimitToday" in deck:
        deck["newLimitToday"] = limit
        updated = True
    if "extendNew" in deck:
        if base_new_limit is None:
            deck["extendNew"] = limit
        else:
            deck["extendNew"] = limit - int(base_new_limit)
        updated = True
    if not updated and "newLimit" in deck:
        deck["newLimit"] = limit
        updated = True

    if not updated:
        return False

    deck["mod"] = int(time.time())
    try:
        deck["usn"] = col.usn()
    except Exception:
        pass

    if _persist_deck(col, deck):
        return _deck_limit_matches(col, deck_id, limit)
    return False


def _persist_deck(col, deck: Dict[str, Any]) -> bool:
    decks = getattr(col, "decks", None)
    if decks is None:
        return False

    persisted = False
    if hasattr(decks, "save"):
        try:
            decks.save(deck)
            persisted = True
        except Exception:
            pass
    if hasattr(decks, "update"):
        try:
            decks.update(deck)
            persisted = True
        except Exception:
            pass
    return persisted


def _get_deck(col, deck_id: int) -> Optional[Dict[str, Any]]:
    try:
        deck = col.decks.get(deck_id)
    except Exception:
        deck = None
    return deck if isinstance(deck, dict) else None


def _deck_limit_matches(col, deck_id: int, limit: int) -> bool:
    limits = _get_backend_deck_limits(col, deck_id)
    if limits is not None:
        try:
            if bool(getattr(limits, "new_today_active", False)) and int(
                getattr(limits, "new_today")
            ) == limit:
                return True
        except Exception:
            pass

    deck = _get_deck(col, deck_id)
    if not deck:
        return False
    if deck.get("newLimitToday") == limit:
        return True

    base_new_limit = _base_new_limit(col, deck_id)
    extend_new = deck.get("extendNew")
    if base_new_limit is not None and isinstance(extend_new, int):
        return int(base_new_limit) + int(extend_new) == limit

    if deck.get("newLimit") == limit:
        return True
    return False


def _get_backend_deck_limits(col, deck_id: int) -> Any:
    decks = getattr(col, "decks", None)
    if decks is None or not hasattr(decks, "get_deck_configs_for_update"):
        return None
    try:
        state = decks.get_deck_configs_for_update(deck_id)
        current_deck = getattr(state, "current_deck", None)
        if current_deck is None:
            return None
        return getattr(current_deck, "limits", None)
    except Exception:
        return None


def _base_new_limit(col, deck_id: int) -> Optional[int]:
    conf: Optional[Dict[str, Any]]
    try:
        conf = col.decks.confForDid(deck_id)
    except Exception:
        conf = None
    if not isinstance(conf, dict):
        return None
    new_conf = conf.get("new")
    if not isinstance(new_conf, dict):
        return None
    try:
        return int(new_conf.get("perDay", 0))
    except Exception:
        return None


def _new_count_today(col, deck_id: int) -> int:
    sched = getattr(col, "sched", None)
    if sched is not None and hasattr(sched, "counts_for_deck_today"):
        try:
            counts = sched.counts_for_deck_today(deck_id)
            if hasattr(counts, "new"):
                return int(getattr(counts, "new") or 0)
        except Exception:
            pass

    deck = _get_deck(col, deck_id)
    if isinstance(deck, dict):
        new_today = deck.get("newToday")
        if isinstance(new_today, (list, tuple)) and len(new_today) >= 2:
            try:
                return int(new_today[1] or 0)
            except Exception:
                pass
    return 0


if gui_hooks is not None:
    gui_hooks.main_window_did_init.append(_setup_menu)
