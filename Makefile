.PHONY: run run-file download create-sqlite extract-data svd install freeze clean

# Configuration
MAIN_FILE = main.py
DOWNLOAD_SCRIPT = etl/descarga.py
CREATE_DB_SCRIPT = etl/create_sqlite_db.py
EXTRACT_DATA_SCRIPT = etl/extract_data.py
SVD_SCRIPT = metodo_SVD/metodo_SVD.py
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

create-sqlite:
	$(PYTHON) $(CREATE_DB_SCRIPT)

extract-data:
	$(PYTHON) $(EXTRACT_DATA_SCRIPT)

svd:
	$(PYTHON) $(SVD_SCRIPT)

install:
	$(VENV_CMD)
	$(PYTHON) -m pip install --upgrade pip
	-$(PIP) install -r requirements.txt

freeze:
	$(PIP) freeze > requirements.txt

clean:
	$(RM_CMD)
