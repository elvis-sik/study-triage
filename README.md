# Zero Today's New Cards

An Anki add-on that adds a single Tools-menu action to set `Today only` new cards/day to `0` for every regular deck in the current collection.

## What it does

Use this on tired days when you want to do reviews only.

After installation, open:

- `Tools -> Zero Today's New Cards`

The add-on will ask for confirmation, then apply `Today only` new/day = `0` to every non-filtered deck in the collection.

This change is temporary. It uses Anki's `Today only` limit, so it resets automatically on the next Anki day.

## Install

1. Copy the folder contents into an Anki add-on folder such as `ZeroTodayNew`.
2. Restart Anki.
3. Run `Tools -> Zero Today's New Cards` whenever you want a reviews-only day.

## Notes

- Filtered decks are skipped.
- The add-on uses the same deck-limit update path that the local `anki-fractional-scheduler` add-on uses to modify `Today only` new/day correctly.
- If Anki's newer deck-config API is unavailable, the add-on falls back to older deck update mechanisms.
