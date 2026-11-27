#!/usr/bin/env bash
# Build dist/personal-plugin-<version>.zip (single top-level folder personal-plugin/).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN="$ROOT/plugins/personal-plugin"
OUT_DIR="$ROOT/dist"

VERSION="$(python3 - "$PLUGIN" <<'PY'
import json, sys
p = sys.argv[1]
def load(f): return json.load(open(f"{p}/{f}"))
root, claude, codex = load("plugin.json"), load(".claude-plugin/plugin.json"), load(".codex-plugin/plugin.json")
vs = {"plugin.json": root.get("version"), ".claude-plugin/plugin.json": claude.get("version"), ".codex-plugin/plugin.json": codex.get("version")}
if len(set(vs.values())) != 1 or None in vs.values():
    sys.exit(f"ERROR: manifest versions differ or missing: {vs}")
for label, s in (("codex interface.shortDescription", codex["interface"]["shortDescription"]),
                 ("plugin.json extensions.com.openai.interface.shortDescription", root["extensions"]["com.openai"]["interface"]["shortDescription"])):
    if len(s) > 30:
        sys.exit(f"ERROR: {label} is {len(s)} chars (max 30): {s!r}")
print(root["version"])
PY
)"

mkdir -p "$OUT_DIR"
ZIP="$OUT_DIR/personal-plugin-$VERSION.zip"
rm -f "$ZIP"

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir "$STAGE/personal-plugin"
cp -a "$PLUGIN/." "$STAGE/personal-plugin/"
find "$STAGE" -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
find "$STAGE" -type f \( -name '*.pyc' -o -name .DS_Store \) -delete

if command -v zip >/dev/null 2>&1; then
  (cd "$STAGE" && zip -qr -X "$ZIP" personal-plugin)
else
  python3 - "$STAGE" "$ZIP" <<'PY'
import os, sys, zipfile
stage, out = sys.argv[1:3]
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for d, _, fs in os.walk(stage):
        for f in sorted(fs):
            full = os.path.join(d, f)
            z.write(full, os.path.relpath(full, stage))
PY
fi
echo "$ZIP"
