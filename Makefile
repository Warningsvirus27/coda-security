.PHONY: help install install-poetry install-pip venv build run stop run-backend run-frontend test test-backend test-frontend test-pytest migrate makemigrations docker-up docker-down clean

# Python and Virtualenv resolution (prioritizes local venv)
PYTHON ?= $(if $(wildcard backend/venv/Scripts/python.exe),backend/venv/Scripts/python.exe,python)
PYTEST ?= $(if $(wildcard backend/venv/Scripts/pytest.exe),backend/venv/Scripts/pytest.exe,pytest)
MANAGE = backend/manage.py

# Docker binary resolution (prioritizes DockerDesktop bin on Windows)
DOCKER_CMD ?= $(if $(wildcard C:/Users/sachi/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe),C:/Users/sachi/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe,docker)

help:
	@echo "SecureCoda Build & Execution Commands"
	@echo "====================================="
	@echo "  make venv            - Create Python virtual environment (backend/venv)"
	@echo "  make install         - Auto-detects Poetry or Pip and installs backend + frontend deps"
	@echo "  make install-poetry  - Install backend dependencies via Poetry"
	@echo "  make install-pip     - Install backend dependencies via standard Pip"
	@echo "  make build           - Build all Docker containers (backend, frontend, worker)"
	@echo "  make run             - Execute and run all project containers via Docker Compose"
	@echo "  make stop            - Stop and tear down all project containers"
	@echo "  make docker-up       - Build and start Docker containers in background"
	@echo "  make docker-down     - Stop and remove Docker containers"
	@echo "  make run-backend     - Start Django/Daphne ASGI dev server locally"
	@echo "  make run-frontend    - Start React dashboard on port 3000 locally"
	@echo "  make test            - Run all backend and frontend unit tests"
	@echo "  make test-backend    - Run Django unit tests"
	@echo "  make test-pytest     - Run backend test suite via pytest with fixtures"
	@echo "  make test-frontend   - Run React unit tests via Jest"
	@echo "  make migrate         - Apply database migrations"
	@echo "  make makemigrations  - Generate Django migrations"
	@echo "  make clean           - Remove cached files and test artifacts"

venv:
	python -m venv backend/venv
	@echo "Virtual environment created at backend/venv"

build:
	$(DOCKER_CMD) compose build

run:
	$(DOCKER_CMD) compose up -d

stop:
	$(DOCKER_CMD) compose down

install:
	@echo "Installing dependencies..."
	@which poetry >/dev/null 2>&1 && (cd backend && poetry install) || (cd backend && $(PYTHON) -m pip install -r requirements.txt)
	cd frontend && npm install

install-poetry:
	cd backend && poetry install
	cd frontend && npm install

install-pip:
	cd backend && $(PYTHON) -m pip install -r requirements.txt
	cd frontend && npm install

run-backend:
	$(PYTHON) $(MANAGE) runserver 0.0.0.0:8000

run-frontend:
	cd frontend && npm start

test: test-backend test-frontend

test-backend:
	$(PYTHON) $(MANAGE) test tests

test-pytest:
	pytest backend/tests

test-frontend:
	cd frontend && npm test -- --watchAll=false

migrate:
	$(PYTHON) $(MANAGE) migrate

makemigrations:
	$(PYTHON) $(MANAGE) makemigrations

docker-up:
	$(DOCKER_CMD) compose up --build -d

docker-down:
	$(DOCKER_CMD) compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
