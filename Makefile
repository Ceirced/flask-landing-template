.PHONY: help dev local prod prod-app stop clean setup-dirs build-css sync

# Default target - show help
help:
	@echo "Flask Application Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make dev       - Run everything in Docker (development mode)"
	@echo "  make local     - Run only Redis and Celery in Docker (for local Flask development)"
	@echo "  make prod      - Run in production mode (builds CSS first)"
	@echo "  make prod-app  - Rebuild and restart only the app container (prod)"
	@echo "  make build-css - Build production CSS with npm"
	@echo "  make sync      - Install/sync dependencies with uv"
	@echo "  make stop      - Stop all containers"
	@echo "  make clean     - Stop containers and remove volumes"
	@echo "  make help      - Show this help message"

# Setup required directories
setup-dirs:
	@mkdir -p ./logs/app ./instance

# Build production CSS
build-css:
	@echo "Building production CSS..."
	npm run build

# Install/sync dependencies
sync:
	@echo "Syncing dependencies with uv..."
	uv sync

# Development mode - run everything in Docker
dev: setup-dirs
	@echo "Starting Flask server in DEV..."
	docker compose up -d --build

# Local development - only Redis and Celery in Docker
local: setup-dirs
	@echo "Starting Redis and Celery only for local development..."
	@echo "Redis will be available on localhost:6379"
	docker compose up -d --build redis celery
	@echo ""
	@echo "Redis and Celery are running. Now start Flask with:"
	@echo "  uv run flask run"

# Production mode
prod: setup-dirs build-css
	@echo "Starting Flask server in PROD..."
	docker compose up -d --build

# Production mode - app only (skip redis, celery, nginx)
prod-app: setup-dirs build-css
	@echo "Rebuilding and restarting app container only..."
	docker compose up -d --build --no-deps app

# Stop all containers
stop:
	@echo "Stopping Flask server..."
	docker compose down

# Clean everything including volumes
clean:
	@echo "Stopping containers and removing volumes..."
	docker compose down -v
