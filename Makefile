.PHONY: help env steps verify

help:
	@echo "make env      Check Git, Python, uv and Claude Code"
	@echo "make steps    List numbered Claude Code build stages"
	@echo "make verify   Run tests, lint, format and mypy after Step 01"

env:
	@./scripts/check_environment.sh

steps:
	@./scripts/list_steps.sh

verify:
	@./scripts/verify.sh
