# Study Triage

An Anki add-on that adds quick triage actions for days when you need to reduce today's study load.

## What it does

Use this on tired days when you want to do reviews only.

After installation, open:

- `Tools -> Study Triage`

Available collection-wide actions:

- `Set Today's New Cards to 0`
- `Answer Due Cards as Good`
- `Answer Due Cards as Easy`

Or click a deck's cog menu on the Decks screen and open:

- `Study Triage`

The cog-menu actions apply to that deck. Anki's deck search includes subdecks,
so answering due cards from a parent deck includes due cards in its children.
Filtered decks can use the Good/Easy actions; the new-card limit action is only
available for regular decks.

The new-card limit change is temporary. It uses Anki's `Today only` limit, so it
resets automatically on the next Anki day. Deck-cog Good/Easy actions answer the
queued due review and learning cards Anki's scheduler would currently show for
that deck, including review limits and sibling-burying behavior. Cards that
belong to the deck but are currently parked in another deck, such as a filtered
deck, are left alone. The actions show a count before running, process the batch
with progress, and try to group the change into a single Anki undo step.

## Install

Requires Anki 2.1.55 or newer.

1. Copy the folder contents into an Anki add-on folder such as `StudyTriage`.
2. Restart Anki.
3. Run `Tools -> Study Triage` or use the deck cog menu whenever you need to triage a deck.

## Notes

- Filtered decks are skipped by the new-card limit action.
- The add-on uses the same deck-limit update path that the local `anki-fractional-scheduler` add-on uses to modify `Today only` new/day correctly.
- If Anki's newer deck-config API is unavailable, the add-on falls back to older deck update mechanisms.
- Large Good/Easy and all-deck new-limit batches are merged incrementally to
  stay inside Anki's undo-history window.
- If an action fails, the add-on shows failure details, offers to open failed cards in the Browser, and writes details to `user_files/study-triage.log` inside the add-on folder.
