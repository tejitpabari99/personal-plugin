#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

bash scripts/zip-plugin.sh >/dev/null
VERSION="$(python3 -c "import json;print(json.load(open('plugins/personal-plugin/plugin.json'))['version'])")"
ZIP="dist/personal-plugin-$VERSION.zip"

fail() { echo "FAIL: $*" >&2; exit 1; }
[ -f "$ZIP" ] || fail "missing $ZIP"

LIST="$(python3 -c "
import sys,zipfile
print('\n'.join(zipfile.ZipFile(sys.argv[1]).namelist()))" "$ZIP")"

while IFS= read -r e; do
  case "$e" in personal-plugin/*) ;; *) fail "entry outside personal-plugin/: $e";; esac
done <<<"$LIST"

for f in plugin.json .claude-plugin/plugin.json .codex-plugin/plugin.json LICENSE skills/tick/SKILL.md; do
  grep -qxF "personal-plugin/$f" <<<"$LIST" || fail "missing personal-plugin/$f"
done
! grep -q 'marketplace.json' <<<"$LIST" || fail "marketplace.json present"
! grep -q '__pycache__' <<<"$LIST" || fail "__pycache__ present"
! grep -qE '\.pyc$|\.DS_Store$' <<<"$LIST" || fail "pyc/.DS_Store present"
echo "PASS: $ZIP"
