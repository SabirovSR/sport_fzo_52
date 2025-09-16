.PHONY: help install test lint format security build deploy clean

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test: ## Run tests
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

lint: ## Run linting
	flake8 app tests --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 app tests --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	black --check app tests
	isort --check-only app tests
	mypy app --ignore-missing-imports

format: ## Format code
	black app tests
	isort app tests

security: ## Run security scans
	safety check
	bandit -r app -ll
	semgrep --config=auto app/

build: ## Build Docker image
	docker build -t fok-bot:latest .

build-ssl: ## Build SSL-enabled Docker image
	docker build -f Dockerfile.ssl -t fok-bot-ssl:latest .

build-all: build build-ssl ## Build all Docker images

run: ## Run the bot locally
	python main.py

run-docker: ## Run with Docker Compose
	docker-compose up -d

run-ssl: ## Run with SSL Docker Compose
	docker-compose -f docker-compose.ssl.yml up -d

stop: ## Stop Docker containers
	docker-compose down

stop-ssl: ## Stop SSL Docker containers
	docker-compose -f docker-compose.ssl.yml down

logs: ## Show logs
	docker-compose logs -f

logs-ssl: ## Show SSL logs
	docker-compose -f docker-compose.ssl.yml logs -f

ssl-setup: ## Setup SSL certificate
	python scripts/ssl_manager.py --domain $(DOMAIN) --email $(EMAIL)

ssl-renew: ## Renew SSL certificate
	python scripts/ssl_manager.py --domain $(DOMAIN) --email $(EMAIL) --renew

ssl-check: ## Check SSL certificate status
	python scripts/ssl_manager.py --domain $(DOMAIN) --email $(EMAIL) --check

deploy-staging: ## Deploy to staging
	@echo "Deploying to staging..."
	# Add your staging deployment commands here

deploy-production: ## Deploy to production
	@echo "Deploying to production..."
	# Add your production deployment commands here

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/
	docker system prune -f

clean-docker: ## Clean up Docker resources
	docker-compose down -v
	docker-compose -f docker-compose.ssl.yml down -v
	docker system prune -af

setup-dev: install-dev ## Setup development environment
	@echo "Setting up development environment..."
	@echo "Please create a .env file with your configuration"
	@echo "Run 'make test' to verify everything is working"

ci: lint test security ## Run CI pipeline locally

all: clean install test lint security build ## Run everything