.PHONY: install test lint format clean dev run setup deploy

# Install dependencies
install:
	uv pip install -e .
	uv pip install -e ".[dev]"

# Install in development mode
dev: install
	uv pip install -e ".[dev]"

# Run tests
test:
	pytest tests/ -v --cov=src --cov-report=html

# Lint code
lint:
	mypy src/
	ruff check src/

# Format code
format:
	black src/ tests/
	ruff format src/ tests/

# Clean cache and build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov/
	rm -rf build/ dist/ *.egg-info/

# Run the server
run:
	python main.py

# Run with development dependencies
run-dev: dev
	python main.py

# Setup GCP environment (first time only)
setup:
	cd setup && ./setup_gcp.sh && ./create_project.sh && ./enable_apis.sh

# Deploy to Google Cloud Run
deploy:
	cd deployment && ./deploy.sh

# Load environment variables (use with: make env && source .env)
env:
	@echo "Run: source setup/set_env.sh"