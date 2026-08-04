#!/usr/bin/env bash
set -euo pipefail

echo "Aira LM environment check"
echo "=========================="

missing=0
for cmd in git python3 uv claude; do
  if command -v "$cmd" >/dev/null 2>&1; then
    printf "%-10s %s\n" "$cmd" "$(command -v "$cmd")"
  else
    printf "%-10s MISSING\n" "$cmd"
    missing=1
  fi
done

echo
python3 --version 2>/dev/null || true
uv --version 2>/dev/null || true
claude --version 2>/dev/null || true
git --version 2>/dev/null || true

if [[ "$(uname -s)" == "Darwin" ]]; then
  echo
  echo "Apple hardware:"
  system_profiler SPHardwareDataType 2>/dev/null | grep -E "Chip|Memory" || true
fi

echo
if [[ $missing -ne 0 ]]; then
  echo "One or more required commands are missing."
  exit 1
fi

echo "Environment looks ready for Step 00."
