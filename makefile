.PHONY: install-devel check lint test venv

# NOTE: ZT_VENV and BASEPYTHON are advanced undocumented features
# Customize your venv name by running make as "ZT_VENV=my_venv_name make <command>"

BASEPYTHON?=python3
ZT_VENV?=zt_venv

VENV_ACTIVATE=. $(ZT_VENV)/bin/activate
PYTHON=${ZT_VENV}/bin/$(BASEPYTHON)

SOURCES = zulipterminal tests setup.py

# Default target at top
install-devel: venv

### LINT/TEST FILES ###

check: lint test

lint: venv
	@tools/lint-all

test: venv
	@pytest

### VENV SETUP ###
# Short name for file dependency
venv: $(ZT_VENV)/bin/activate

# If setup.py is updated or activate script doesn't exist, update virtual env
$(ZT_VENV)/bin/activate: setup.py
	@echo "=== Installing development environment ==="
	test -d $(ZT_VENV) || $(BASEPYTHON) -m venv $(ZT_VENV)
	$(PYTHON) -m pip install -U pip && $(PYTHON) -m pip install -e .[dev] && touch $(ZT_VENV)/bin/activate
