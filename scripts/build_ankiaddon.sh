#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v zip >/dev/null 2>&1; then
  echo "error: zip not found (install zip first)" >&2
  exit 1
fi

out_dir="${1:-"$repo_root/dist"}"
out_file="${2:-"study-triage.ankiaddon"}"

mkdir -p "$out_dir"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

files=(
  "__init__.py"
  "manifest.json"
  "README.md"
)

for f in "${files[@]}"; do
  cp "$repo_root/$f" "$tmpdir/"
done

out_path="$out_dir/$out_file"
rm -f "$out_path"
(cd "$tmpdir" && zip -qr "$out_path" .)
zip -T "$out_path" >/dev/null
echo "$out_path"
