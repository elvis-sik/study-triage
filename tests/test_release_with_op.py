from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def _load_release_script() -> object:
    path = ROOT / "scripts" / "release_with_op.py"
    spec = importlib.util.spec_from_file_location("release_with_op", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReleaseWithOpTests(unittest.TestCase):
    def test_load_env_file_preserves_op_references_with_spaces(self) -> None:
        module = _load_release_script()
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        'ANKIWEB_EMAIL_OP="op://Vault/Item With Spaces/username"',
                        "ANKIWEB_PASSWORD_OP=op://Vault/Item With Spaces/password",
                    ]
                ),
                encoding="utf-8",
            )

            values = module.load_env_file(env_path)

        self.assertEqual(values["ANKIWEB_EMAIL_OP"], "op://Vault/Item With Spaces/username")
        self.assertEqual(values["ANKIWEB_PASSWORD_OP"], "op://Vault/Item With Spaces/password")

    def test_strip_remainder_separator(self) -> None:
        module = _load_release_script()

        self.assertEqual(["--submit"], module._strip_remainder_separator(["--", "--submit"]))
        self.assertEqual(["--mode", "create"], module._strip_remainder_separator(["--mode", "create"]))


if __name__ == "__main__":
    unittest.main()
