.PHONY: test test-unit test-integration test-coverage lint format clean help

help:
	@echo "Available commands:"
	@echo "  make test              - Run all tests"
	@echo "  make test-unit         - Run unit tests only"
	@echo "  make test-integration  - Run integration tests only"
	@echo "  make test-coverage     - Run tests with coverage report"
	@echo "  make lint              - Run code linters"
	@echo "  make format            - Format code"
	@echo "  make clean             - Clean temporary files"

test:
	pytest gdrive_sync/tests/

test-unit:
	pytest gdrive_sync/tests/ -m "not integration"

test-integration:
	pytest gdrive_sync/tests/test_integration/

test-coverage:
	pytest gdrive_sync/tests/ --cov=gdrive_sync --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	flake8 gdrive_sync tests
	pylint gdrive_sync
	mypy gdrive_sync

format:
	black gdrive_sync tests
	isort gdrive_sync tests

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
