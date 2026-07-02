Study Triage adds quick triage actions for days when you need to reduce today's Anki workload.

Use it when you want to keep reviews moving but avoid adding more new cards, or when you need to quickly answer a batch of due cards.

Actions:

- Set Today's New Cards to 0
- Answer Due Cards as Good
- Answer Due Cards as Easy

You can run actions collection-wide from Tools -> Study Triage. You can also run deck-specific actions from a deck's cog menu or by right-clicking a deck name on the Decks screen.

Notes:

- The new-card limit uses Anki's Today only limit, so it resets automatically on the next Anki day.
- Deck actions apply to the selected deck and its subdecks, matching Anki's deck search behavior.
- Filtered decks can use the Good/Easy actions; the new-card limit action is only available for regular decks.
- Actions show a count before running and try to group the change into a single Anki undo step.

Requires Anki 2.1.55 or newer.

Source, screenshot, and issue tracker: github.com/elvis-sik/study-triage
