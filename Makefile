.PHONY: run run-file download install freeze clean

# Configuration
MAIN_FILE = main.py
DOWNLOAD_SCRIPT = descarga.py
VENV = .venv

# Detect OS
ifeq ($(OS),Windows_NT)
	PYTHON = $(VENV)/Scripts/python.exe
	PIP = $(VENV)/Scripts/pip.exe
	VENV_CMD = python -m venv $(VENV)
	RM_CMD = powershell -Command "if (Test-Path $(VENV)) { Remove-Item -Recurse -Force $(VENV) }"
else
	PYTHON = $(VENV)/bin/python
	PIP = $(VENV)/bin/pip
	VENV_CMD = python3 -m venv $(VENV)
	RM_CMD = rm -rf $(VENV)
endif

run:
	$(PYTHON) $(MAIN_FILE)

run-file:
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please specify a file with FILE=<filename>"; \
		echo "Usage: make run-file FILE=script.py"; \
		exit 1; \
	fi
	$(PYTHON) $(FILE)

download:
	$(PYTHON) $(DOWNLOAD_SCRIPT)

install:
	$(VENV_CMD)
	$(PYTHON) -m pip install --upgrade pip
	-$(PIP) install -r requirements.txt

freeze:
	$(PIP) freeze > requirements.txt

clean:
	$(RM_CMD)
