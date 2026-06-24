# Anki GUI Smoke Harness

This directory validates the add-on in a disposable Anki GUI process without
touching the user's real Anki base folder or collection.

The reusable launch, disposable profile, add-on copy, Docker/Xvfb, screenshot,
and input tooling lives in the PyPI `anki-addon-workbench[gui]` package. This
directory keeps only the Study Triage-specific probe add-on and the checked-in
Dockerfile used for local smoke runs.

The probe add-on waits for Anki's main window initialization hook, inspects the
real Qt `Tools` menu, synthesizes Anki's deck-cog options menu hook, then opens
the Study Triage deck submenu and clicks the deck-specific zero-new action with
`QTest.mouseClick`. It also exercises the right-click deck-name JavaScript
bridge and context menu builder. The JSON result includes the clicked action,
signal count, bridge assertion, and before/after deck limit assertion before
Anki quits.

## Host Run

```sh
uv run --extra dev anki-workbench smoke
```

Useful overrides:

```sh
ANKI_BIN=anki uv run --extra dev anki-workbench smoke
uv run --extra dev anki-workbench smoke --qt-platform offscreen
uv run --extra dev anki-workbench smoke --keep
uv run --extra dev anki-workbench smoke --screenshot /tmp/study-triage-gui.png
```

## Docker/Xvfb Run

Start Docker Desktop, then run from the `anki-studying` workspace root:

```sh
docker build -f anki-zero-today-new/tests/gui_smoke/Dockerfile -t study-triage-anki-gui anki-zero-today-new
docker run --rm -v "$PWD":/workspace -w /workspace/anki-zero-today-new study-triage-anki-gui
```

The Docker image uses Anki's Linux launcher at build time, installs
`anki-addon-workbench[gui]` from PyPI, then runs the installed Anki entrypoint
under Xvfb. GUI activity stays inside a virtual display and does not use the
host mouse or keyboard. The workspace mount makes local edits in
`anki-zero-today-new` visible inside the container.

To keep logs and a screenshot from a Docker run:

```sh
mkdir -p anki-zero-today-new/.tmp-gui-smoke
docker run --rm -v "$PWD":/workspace -w /workspace/anki-zero-today-new study-triage-anki-gui sh -lc 'Xvfb :99 -screen 0 1280x1024x24 -nolisten tcp & xvfb_pid=$!; export DISPLAY=:99; python3 -m anki_addon_workbench smoke --anki-bin /root/.local/share/AnkiProgramFiles/.venv/bin/anki --base /workspace/anki-zero-today-new/.tmp-gui-smoke/base --keep --screenshot /workspace/anki-zero-today-new/.tmp-gui-smoke/gui-smoke.png; status=$?; kill "$xvfb_pid" 2>/dev/null || true; exit "$status"'
```

## Agent GUI Workbench

The smoke test above is deterministic and self-contained. For exploratory
agent-driven GUI testing, use `anki-workbench launch` instead. It launches
disposable Anki without the probe add-on, then `anki-workbench screenshot`,
`move`, `click`, `key`, and `type` can inspect and interact with the virtual
display.

One-shot launch plus cursor-marked screenshot:

```sh
docker run --rm -v "$PWD":/workspace -w /workspace/anki-zero-today-new study-triage-anki-gui \
  python3 -m anki_addon_workbench launch \
    --xvfb \
    --base /workspace/anki-zero-today-new/.tmp-gui-workbench/base \
    --artifact-dir /workspace/anki-zero-today-new/.tmp-gui-workbench \
    --pointer 558,166 \
    --keep
```

Detached agent workbench:

```sh
docker rm -f study-triage-workbench 2>/dev/null || true
docker run -d --name study-triage-workbench -v "$PWD":/workspace -w /workspace/anki-zero-today-new study-triage-anki-gui \
  python3 -m anki_addon_workbench launch \
    --xvfb \
    --hold \
    --base /workspace/anki-zero-today-new/.tmp-gui-workbench/base \
    --artifact-dir /workspace/anki-zero-today-new/.tmp-gui-workbench
```

With that container running, use the system Python to drive the display:

```sh
docker exec study-triage-workbench \
  python3 \
  -m anki_addon_workbench screenshot \
    --out /workspace/anki-zero-today-new/.tmp-gui-workbench/shot-001.png \
    --meta /workspace/anki-zero-today-new/.tmp-gui-workbench/shot-001.json

docker exec study-triage-workbench \
  python3 \
  -m anki_addon_workbench move 558 166

docker exec study-triage-workbench \
  python3 \
  -m anki_addon_workbench click
```

Stop the detached workbench with:

```sh
docker rm -f study-triage-workbench
```

The screenshot command writes both a PNG and JSON metadata. The marker is drawn
onto the PNG at the current pointer location by default, so an agent can inspect
where the next click will land and adjust before clicking.
