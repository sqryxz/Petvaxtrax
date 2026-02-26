# PetVaxHK Makefile for local CI/CD tasks

.PHONY: help install test test-cov lint format clean build run-web run-cli

# Default target
help:
	@echo "PetVaxHK - Local CI/CD Commands"
	@echo ""
	@echo "Available targets:"
	@echo "  install    - Install package and dev dependencies"
	@echo "  test       - Run unit tests"
	@echo "  test-cov   - Run tests with coverage report"
	@echo "  lint       - Run linting checks"
	@echo "  format     - Format code with black"
	@echo "  clean      - Clean up cache and build files"
	@echo "  build      - Build package"
	@echo "  run-web    - Run Flask web app"
	@echo "  run-cli    - Run CLI help"

install:
	pip install -e ".[dev]"

test:
	pytest app/tests/ -v

test-cov:
	pytest app/tests/ -v --cov=app --cov-report=term-missing

lint:
	ruff check app/
	@echo "Running black check..."
	@black --check app/ || true

format:
	ruff check app/ --fix
	black app/

clean:
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	python -m build

run-web:
	cd petvax && python run_web.py

run-cli:
	cd petvax && python -m app.cli --help
