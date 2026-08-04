#!/usr/bin/env bash
# Control-tower verification for Step 00.
# Passes only when the written plan is complete, all governing documents and
# referenced paths exist, every hard invariant is mapped to a test, every stage
# has a completion gate, and no Python runtime/package code has been introduced.
set -euo pipefail

cd "$(dirname "$0")/.."

fail=0
note() { printf "  %-6s %s\n" "$1" "$2"; }
check_file() {
  if [[ -e "$1" ]]; then note "OK" "$1"; else note "MISS" "$1"; fail=1; fi
}

echo "Step 00 — Control Tower verification"
echo "===================================="

echo
echo "1) Required governing documents exist"
for f in \
  CLAUDE.md \
  docs/MISSION.md docs/REQUIREMENTS.md docs/INVARIANTS.md docs/ARCHITECTURE.md \
  docs/THREAT_MODEL.md docs/DATA_CLASSIFICATION.md docs/EVALUATION_PLAN.md \
  docs/FAILURE_MODES.md docs/ROADMAP.md docs/SOURCE_REVIEW.md docs/BRANDING.md \
  docs/BUILD_STATUS.md \
  references/memory-system.html \
  configs/aira_tiny.toml; do
  check_file "$f"
done

echo
echo "2) Step 00 deliverables exist"
for f in PROJECT_PLAN.md ASSUMPTIONS.md RISKS.md \
  adr/001-separate-core-memory.md adr/002-sqlite-first.md \
  adr/003-keyword-before-vector.md adr/004-deterministic-policy-first.md \
  adr/005-delete-audit-no-content.md adr/006-graceful-memory-degradation.md \
  adr/007-owner-isolation-v1.md; do
  check_file "$f"
done

echo
echo "3) Every prompt stage 00..14 has a completion gate row in PROJECT_PLAN.md"
for n in 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14; do
  if grep -qE "^\| *${n} \|" PROJECT_PLAN.md; then
    note "OK" "stage ${n} has a gate row"
  else
    note "MISS" "stage ${n} gate row"; fail=1
  fi
done

echo
echo "4) All 12 hard invariants mapped in the traceability matrix"
for n in $(seq 1 12); do
  # Match a matrix row beginning "| <n> |"
  if grep -qE "^\| *${n} \|" PROJECT_PLAN.md; then
    note "OK" "invariant ${n} mapped"
  else
    note "MISS" "invariant ${n} mapping"; fail=1
  fi
done

echo
echo "5) Control-tower discipline: no Python runtime/package code yet"
py_count=$(find src -name '*.py' 2>/dev/null | wc -l | tr -d ' ')
if [[ "${py_count}" == "0" ]]; then
  note "OK" "no .py files under src/"
else
  note "FAIL" "${py_count} .py file(s) under src/ — Step 00 excludes runtime code"; fail=1
fi
if [[ -f pyproject.toml ]]; then
  note "FAIL" "pyproject.toml exists — that belongs to Step 01, not Step 00"; fail=1
else
  note "OK" "no pyproject.toml yet"
fi

echo
if [[ "${fail}" -ne 0 ]]; then
  echo "RESULT: FAIL — control tower is incomplete."
  exit 1
fi
echo "RESULT: PASS — control tower is complete. Next: ./scripts/start_step.sh 01"
