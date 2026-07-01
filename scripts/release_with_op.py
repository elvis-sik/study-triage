#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = ROOT.parent
RELEASE_PROJECT = WORKSPACE_ROOT / "anki-addon-release"
ENV_FILE = ROOT / ".env"
DIAGNOSTICS_DIR = ROOT / ".anki-addon-release" / "diagnostics"

EMAIL_ENV = "ANKIWEB_EMAIL"
PASSWORD_ENV = "ANKIWEB_PASSWORD"
EMAIL_REF_KEYS = ("ANKIWEB_EMAIL_OP", "ANKIWEB_USERNAME_OP")
PASSWORD_REF_KEYS = ("ANKIWEB_PASSWORD_OP",)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resolve AnkiWeb 1Password references and run anki-addon-release.",
    )
    parser.add_argument(
        "action",
        nargs="?",
        choices=("release", "login", "publish"),
        default="release",
        help="release logs in and prepares the publish form; default: release",
    )
    parser.add_argument(
        "framework_args",
        nargs=argparse.REMAINDER,
        help="additional arguments passed to the final anki-addon-release command",
    )
    args = parser.parse_args(argv)

    framework_args = _strip_remainder_separator(args.framework_args)
    child_env = _environment_with_credentials()

    if args.action == "login":
        return _run_release_cli(["login", "--submit-login", *framework_args], child_env)
    if args.action == "publish":
        return _run_release_cli(["publish", *framework_args], child_env)

    login_code = _run_release_cli(["login", "--submit-login"], child_env)
    if login_code != 0:
        return login_code
    return _run_release_cli(["publish", *framework_args], child_env)


def load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        raise SystemExit(f"error: missing {path.name}; copy .env.example to .env and fill op refs")

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            raise SystemExit(f"error: invalid {path.name} line {line_number}: expected KEY=value")
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            raise SystemExit(f"error: invalid {path.name} line {line_number}: missing key")
        values[key] = _unquote(value.strip())
    return values


def _environment_with_credentials() -> dict[str, str]:
    refs = load_env_file(ENV_FILE)
    email_ref = _required_value(refs, EMAIL_REF_KEYS)
    password_ref = _required_value(refs, PASSWORD_REF_KEYS)

    print("Resolving AnkiWeb credentials from 1Password references in .env...")
    env = os.environ.copy()
    env[EMAIL_ENV] = _op_read(email_ref, label="AnkiWeb username")
    env[PASSWORD_ENV] = _op_read(password_ref, label="AnkiWeb password")
    return env


def _required_value(values: dict[str, str], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = values.get(key)
        if value:
            return value
    joined = " or ".join(keys)
    raise SystemExit(f"error: missing {joined} in {ENV_FILE.name}")


def _op_read(reference: str, *, label: str) -> str:
    if shutil.which("op") is None:
        raise SystemExit("error: 1Password CLI not found: install and sign in to `op` first")

    result = subprocess.run(
        ["op", "read", reference],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        suffix = f": {details}" if details else ""
        raise SystemExit(f"error: could not resolve {label} with `op read`{suffix}")

    value = result.stdout.rstrip("\n")
    if not value:
        raise SystemExit(f"error: resolved {label} is empty")
    return value


def _run_release_cli(args: list[str], env: dict[str, str]) -> int:
    if not RELEASE_PROJECT.exists():
        print(f"error: release framework checkout not found: {RELEASE_PROJECT}", file=sys.stderr)
        return 1

    uv = os.environ.get("UV", "uv")
    command = [
        uv,
        "run",
        "--project",
        str(RELEASE_PROJECT),
        "--extra",
        "browser",
        "anki-addon-release",
        "--project",
        str(ROOT),
        *args,
    ]
    if args and args[0] in {"login", "publish"} and "--diagnostics-dir" not in args:
        command.extend(["--diagnostics-dir", str(DIAGNOSTICS_DIR)])

    print(f"+ {shlex.join(command)}")
    return subprocess.run(command, cwd=ROOT, env=env, check=False).returncode


def _strip_remainder_separator(args: list[str]) -> list[str]:
    if args[:1] == ["--"]:
        return args[1:]
    return args


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
