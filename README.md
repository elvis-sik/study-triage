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

The same deck menu is also available by right-clicking a deck name on the Decks
screen. This is useful with deck-browser layout add-ons that hide Anki's cog
icon.

The deck-menu actions apply to that deck. Anki's deck search includes subdecks,
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
3. Run `Tools -> Study Triage`, use the deck cog menu, or right-click a deck name whenever you need to triage a deck.

## Notes

- Filtered decks are skipped by the new-card limit action.
- The add-on uses the same deck-limit update path that the local `anki-fractional-scheduler` add-on uses to modify `Today only` new/day correctly.
- If Anki's newer deck-config API is unavailable, the add-on falls back to older deck update mechanisms.
- Large Good/Easy and all-deck new-limit batches are merged incrementally to
  stay inside Anki's undo-history window.
- If an action fails, the add-on shows failure details, offers to open failed cards in the Browser, and writes details to `user_files/study-triage.log` inside the add-on folder.

## Development

Run repository checks with:

```sh
make test
```

Run the disposable Anki GUI smoke test with:

```sh
make test-gui-smoke
```

The GUI smoke test uses `anki-workbench` from the sibling
`anki-addon-workbench` project. It launches Anki with a temporary base folder,
installs this add-on plus the project-specific probe add-on, verifies the Tools
and deck-cog menu actions through Qt, checks the deck-name context menu bridge,
writes a JSON result, and quits. See
`tests/gui_smoke/README.md` for the Docker/Xvfb variant that keeps GUI activity
inside a virtual display.

For exploratory agent-driven GUI work, use:

```sh
uv run --extra dev anki-workbench launch --xvfb --keep
uv run --extra dev anki-workbench screenshot --out .tmp-gui-workbench/shot.png
```

The compatibility scripts in `scripts/` delegate to `anki-workbench` and
`gui-workbench` for older commands.
