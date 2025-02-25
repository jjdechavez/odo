# Variables
VENV = venv
PYTHON = $(VENV)/bin/python3.13
PIP = $(VENV)/bin/pip3.13
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

.PHONY: venv
venv: ## Create virtual environment
	python3 -m venv $(VENV)

.PHONY: install
install: venv ## Install dependencies
	$(PIP) install -r requirements.txt

.PHONY: setup
setup: install ## Setup project (create venv and install dependencies)
	mkdir -p uploads

.PHONY: clean
clean: ## Remove virtual environment and cache files
	rm -rf $(VENV)
	rm -rf __pycache__
	rm -rf *.pyc
	rm -rf uploads/*

.PHONY: run
run: ## Run development server
	$(PYTHON) app.py

.PHONY: docker-build
docker-build: ## Build Docker image
	docker build -t odometer-api .

.PHONY: docker-run
docker-run: ## Run Docker container
	docker run -p 5000:5000 --env-file .env odometer-api

.PHONY: requirements
requirements: ## Update requirements.txt
	$(PIP) freeze > requirements.txt