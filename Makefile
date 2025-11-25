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
	NULL = nul
else
	PYTHON = $(VENV)/bin/python
	PIP = $(VENV)/bin/pip
	RM = rm -rf
	VENV_CMD = python3 -m venv $(VENV)
	NULL = /dev/null
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
	-$(RM) $(VENV)
