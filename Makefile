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
else
	PYTHON = $(VENV)/bin/python
	PIP = $(VENV)/bin/pip
	RM = rm -rf
	VENV_CMD = python3 -m venv $(VENV)
endif

run:
	$(PYTHON) $(MAIN_FILE)

install:
	$(VENV_CMD)
	$(PIP) install --upgrade pip
ifeq ($(OS),Windows_NT)
	@if exist requirements.txt $(PIP) install -r requirements.txt
else
	@if [ -f requirements.txt ]; then \
		$(PIP) install -r requirements.txt; \
	fi
endif

freeze:
	$(PIP) freeze > requirements.txt

clean:
	$(RM) $(VENV)
