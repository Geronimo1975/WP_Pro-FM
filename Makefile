# Makefile for WP_Pro-FM Django Project

# Load environment variables from .env
include .env
export

.PHONY: help build up down logs shell migrate makemigrations createsuperuser test lint clean ssh ssh-docker ssh-logs deploy

# Default target
help:
	@echo "WP_Pro-FM Django Project Commands"
	@echo "=================================="
	@echo "make build          - Build Docker containers"
	@echo "make up             - Start all containers"
	@echo "make down           - Stop all containers"
	@echo "make logs           - View container logs"
	@echo "make shell          - Open Django shell"
	@echo "make bash           - Open bash in backend container"
	@echo "make migrate        - Run database migrations"
	@echo "make makemigrations - Create new migrations"
	@echo "make createsuperuser- Create admin user"
	@echo "make test           - Run tests"
	@echo "make clean          - Remove containers and volumes"
	@echo ""
	@echo "VPS Commands ($(VPS_HOST))"
	@echo "=================================="
	@echo "make ssh            - Connect to VPS server"
	@echo "make ssh-docker     - Show Docker status on VPS"
	@echo "make ssh-logs       - View Docker logs on VPS"
	@echo "make ssh-status     - Show server status (disk, memory, docker)"
	@echo "make deploy         - Deploy to VPS server"

# Docker commands
build:
	docker-compose build

up:
	docker-compose up -d

up-logs:
	docker-compose up

down:
	docker-compose down

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-celery:
	docker-compose logs -f celery

# Django commands
shell:
	docker-compose exec backend python manage.py shell

bash:
	docker-compose exec backend bash

migrate:
	docker-compose exec backend python manage.py migrate

makemigrations:
	docker-compose exec backend python manage.py makemigrations

createsuperuser:
	docker-compose exec backend python manage.py createsuperuser

collectstatic:
	docker-compose exec backend python manage.py collectstatic --noinput

# Development
test:
	docker-compose exec backend python manage.py test

lint:
	docker-compose exec backend flake8 .

# Database
dbshell:
	docker-compose exec db psql -U postgres -d wp_profm

backup-db:
	docker-compose exec db pg_dump -U postgres wp_profm > backup_$$(date +%Y%m%d_%H%M%S).sql

# Celery
celery-logs:
	docker-compose logs -f celery celery-beat

# Cleanup
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Production
prod-up:
	docker-compose --profile production up -d

prod-down:
	docker-compose --profile production down

# Quick start
start: build up migrate createsuperuser
	@echo "Project started! Visit http://localhost:8000/admin"

# VPS Commands
ssh:
	@echo "Connecting to VPS $(VPS_HOST)..."
	ssh $(VPS_USER)@$(VPS_HOST)

ssh-docker:
	@echo "Docker status on VPS $(VPS_HOST):"
	ssh $(VPS_USER)@$(VPS_HOST) "docker ps"

ssh-logs:
	ssh $(VPS_USER)@$(VPS_HOST) "cd $(VPS_PATH) && docker-compose logs -f --tail=100"

ssh-status:
	@echo "Server status on $(VPS_HOST):"
	ssh $(VPS_USER)@$(VPS_HOST) "echo '=== Disk ===' && df -h / && echo '' && echo '=== Memory ===' && free -m && echo '' && echo '=== Docker ===' && docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

deploy:
	@echo "Deploying to VPS $(VPS_HOST)..."
	rsync -avz --progress \
		--exclude='.git' --exclude='venv' --exclude='__pycache__' --exclude='.env' --exclude='*.pyc' \
		./ $(VPS_USER)@$(VPS_HOST):$(VPS_PATH)/
	ssh $(VPS_USER)@$(VPS_HOST) "cd $(VPS_PATH) && docker-compose down && docker-compose build --no-cache backend && docker-compose up -d"
	@echo "Deployment complete!"
