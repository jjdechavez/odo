# Variables
VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
FLASK = $(VENV)/bin/flask

# Default target
.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@echo 'Usage:'
	@echo '  make <target>'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: setup install run clean test lint

setup: $(VENV)/bin/activate ## Setup development environment (venv, dependencies, directories)
	@echo "Creating uploads directory..."
	@mkdir -p uploads
	@echo "Creating .env file..."
	@cp .env.example .env || echo "FLASK_ENV=development\nFLASK_APP=app.py\nFLASK_DEBUG=1\nUPLOAD_FOLDER=uploads\nALLOWED_EXTENSIONS=png,jpg,jpeg\nMAX_CONTENT_LENGTH=2097152\nAPI_PORT=8086\nAPI_HOST=0.0.0.0\nCORS_ORIGINS=http://localhost:3000,http://localhost:8081,exp://192.168.1.2:8081,exp://localhost:8081" > .env
	@echo "Setup complete!"

$(VENV)/bin/activate: requirements.txt
	@echo "Creating virtual environment..."
	@python -m venv $(VENV)
	@echo "Installing dependencies..."
	@$(PIP) install -r requirements.txt
	@touch $(VENV)/bin/activate

install: ## Install/update dependencies
	@echo "Installing dependencies..."
	@$(PIP) install -r requirements.txt

run: ## Run the API server
	@echo "Starting API server..."
	@$(FLASK) run --host=0.0.0.0 --port=8086

clean: ## Remove virtual environment and cached files
	@echo "Cleaning up..."
	@rm -rf $(VENV)
	@rm -rf __pycache__
	@rm -rf .pytest_cache
	@echo "Cleanup complete!"

.PHONY: docker-build
docker-build: ## Build Docker image
	docker build -t odometer-api .

.PHONY: docker-run
docker-run: ## Run Docker container
	docker run -p 5000:5000 --env-file .env odometer-api

.PHONY: requirements
requirements: ## Update requirements.txt
	$(PIP) freeze > requirements.txt