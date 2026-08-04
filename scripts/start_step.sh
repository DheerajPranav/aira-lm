#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 STEP_NUMBER"
  echo "Example: $0 00"
  exit 2
fi

step="$(printf "%02d" "$((10#$1))")"
shopt -s nullglob
matches=(prompts/"${step}"_*.md)
shopt -u nullglob

if [[ ${#matches[@]} -ne 1 ]]; then
  echo "Could not resolve exactly one prompt for step ${step}."
  exit 1
fi

prompt_file="${matches[0]}"
echo "Launching Claude Code for ${prompt_file}"
echo "Claude must execute this step only and stop after verification."
echo

claude "Read CLAUDE.md, docs/BUILD_STATUS.md, and ${prompt_file}. Execute only Step ${step}. Follow all prerequisites and completion gates. Update BUILD_STATUS.md with evidence, then stop."
