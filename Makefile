.PHONY: run install freeze clean

# Configuration
MAIN_FILE = main.py
VENV = .venv

# Detect OS
ifeq ($(OS),Windows_NT)
	PYTHON = $(VENV)/Scripts/python.exe
	PIP = $(VENV)/Scripts/pip.exe
	VENV_CMD = python -m venv $(VENV)
else
	PYTHON = $(VENV)/bin/python
	PIP = $(VENV)/bin/pip
	VENV_CMD = python3 -m venv $(VENV)
endif

run:
	$(PYTHON) $(MAIN_FILE)

install:
	$(VENV_CMD)
	$(PIP) install --upgrade pip
	-$(PIP) install -r requirements.txt

freeze:
	$(PIP) freeze > requirements.txt

clean:
	rm -rf $(VENV)
