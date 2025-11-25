.PHONY: run install freeze clean

# Configuration
MAIN_FILE = main.py
VENV = .venv

# Detect OS
ifeq ($(OS),Windows_NT)
	PYTHON = $(VENV)/Scripts/python.exe
	PIP = $(VENV)/Scripts/pip.exe
	RM = rmdir /s /q
	VENV_CMD = python -m venv $(VENV)
	INSTALL_REQS = if exist requirements.txt $(PIP) install -r requirements.txt
else
	PYTHON = $(VENV)/bin/python
	PIP = $(VENV)/bin/pip
	RM = rm -rf
	VENV_CMD = python3 -m venv $(VENV)
	INSTALL_REQS = test -f requirements.txt && $(PIP) install -r requirements.txt || true
endif

run:
	$(PYTHON) $(MAIN_FILE)

install:
	$(VENV_CMD)
	$(PIP) install --upgrade pip
	$(INSTALL_REQS)

freeze:
	$(PIP) freeze > requirements.txt

clean:
	$(RM) $(VENV)
