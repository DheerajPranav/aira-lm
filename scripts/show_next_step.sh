#!/usr/bin/env bash
set -euo pipefail
grep -A20 '^## Stage checklist' docs/BUILD_STATUS.md || true
echo
echo "Read BUILD_STATUS.md and run only the first Pending step whose prerequisites are complete."
