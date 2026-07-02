# Makefile for Telegram Forwarder Userbot

# Set the Python interpreter to use (default: python3)
PYTHON ?= python3

# Install dependencies (production)
setup:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install .

# Install dependencies (dev)
setup_dev:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements-dev.txt
	$(PYTHON) -m pip install -e .

# Create a virtual environment
venv:
	$(PYTHON) -m venv .venv
	@echo "Virtual environment created. Activate it with 'source .venv/bin/activate'"

# Format and lint code (black, flake8)
format:
	@echo "Formatting source code"
	$(PYTHON) -m black ./ src/
	$(PYTHON) -m flake8 ./ src/

# Clean temporary files
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} +
	find . -type f -name "*.pyc" -exec rm -f {} +
	@echo "Clean complete!"

# Help: show available commands
help:
	@echo "Available make targets:"
	@grep -E '^[a-zA-Z_-]+:' Makefile | cut -d':' -f1 | grep -v '^_' | sort

.PHONY: setup setup_dev venv format clean help