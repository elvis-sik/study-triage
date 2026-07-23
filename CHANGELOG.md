# Changelog

## 0.3.12 - 2026-07-23

- Fix collection-wide new-card limit changes losing their custom undo target.
- Persist deck limit changes through Anki's undo-aware deck update API so the
  batch remains a single Study Triage undo action.
- Add regression coverage for incremental undo merging across large collections.

## 0.3.11 - 2026-07-16

- Fix Today-only new-card updates on current Anki releases.
- Preserve both active and expired Today-only review limits while triaging new cards.
- Add regression coverage for the deck-limit update and a disposable Anki GUI interaction.
