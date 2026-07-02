# Makefile for Telegram Forwarder Userbot

# Install dependencies (production)
setup:
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	pip install .

# Install dependencies (dev)
setup_dev:
	python -m pip install --upgrade pip
	pip install -r requirements-dev.txt
	pip install -e .

# Format and lint code (black, flake8)
format:
	@echo "Formatting source code"
	python -m black ./ src/
	python -m flake8 ./ src/

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

.PHONY: setup format clean help