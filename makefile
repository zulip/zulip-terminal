.PHONY: install-devel check lint test check-clean-tree fix force-fix venv

# NOTE: ZT_VENV is an advanced undocumented feature
# Customize your venv name by running make as "ZT_VENV=my_venv_name make <command>"

ZT_VENV?=.venv

SOURCES = zulipterminal tests

# Default target at top
install-devel: venv

### LINT/TEST FILES ###

check: lint test

lint: venv
	@uv run ./tools/lint-all

test: venv
	@uv run pytest

### FIX FILES ###

check-clean-tree:
	@git diff --exit-code --quiet || (echo 'Tree is not clean - commit changes in git first' && false)

fix: check-clean-tree
	@make force-fix

force-fix: venv
	@echo "=== Auto-fixing files ==="
	uv run isort $(SOURCES) tools
	uv run black zulipterminal/ tests/
	uv run ruff --fix $(SOURCES)

### VENV SETUP ###
# Short name for file dependency
venv: $(ZT_VENV)/bin/activate

# If project metadata changes or activate script doesn't exist, update virtual env
$(ZT_VENV)/bin/activate: pyproject.toml uv.lock
	@echo "=== Installing development environment ==="
	uv sync --extra dev
