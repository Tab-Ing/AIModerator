SHELL := /bin/bash
VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
UV := uv

.PHONY: help venv install install-local dev test test-integration lint format typecheck migrate revision docker-up docker-down clean

help:
	@echo "Objetivos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

venv: ## Crea el entorno virtual .venv (usa uv si está disponible)
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) venv $(VENV); \
	else \
		python3 -m venv $(VENV); \
	fi
	@$(MAKE) install

install: ## Instala el paquete en modo editable con extras dev
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) pip install -e ".[dev]"; \
	else \
		$(PIP) install --upgrade pip && $(PIP) install -e ".[dev]"; \
	fi

install-local: ## Instala además los motores locales (sentence-transformers/torch)
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) pip install -e ".[dev,local]"; \
	else \
		$(PIP) install -e ".[dev,local]"; \
	fi

dev: ## Levanta la API en modo desarrollo
	$(VENV)/bin/uvicorn aimoderator.main:app --reload --host 0.0.0.0 --port 8000

test: ## Ejecuta la suite de tests (sin Postgres)
	$(VENV)/bin/pytest -m "not integration" --cov=aimoderator --cov-report=term-missing

test-integration: ## Ejecuta tests de integración (requiere Postgres)
	$(VENV)/bin/pytest -m integration

lint: ## Verifica estilo con ruff
	$(VENV)/bin/ruff check .

format: ## Formatea el código con ruff
	$(VENV)/bin/ruff format .
	$(VENV)/bin/ruff check --fix .

typecheck: ## Analiza tipos con mypy
	$(VENV)/bin/mypy src

migrate: ## Aplica migraciones de Alembic
	$(VENV)/bin/alembic upgrade head

revision: ## Crea una nueva migración (msg="...")
	$(VENV)/bin/alembic revision --autogenerate -m "$(msg)"

docker-up: ## Levanta Postgres + API con docker compose
	docker compose up --build -d

docker-down: ## Detiene docker compose
	docker compose down

clean: ## Elimina caches y artefactos
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
