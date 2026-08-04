#!/usr/bin/env bash
set -euo pipefail
for file in prompts/[0-9][0-9]_*.md; do
  base="$(basename "$file" .md)"
  title="$(grep -m1 '^# ' "$file" | sed 's/^# //')"
  printf "%s  %s\n" "${base%%_*}" "$title"
done
