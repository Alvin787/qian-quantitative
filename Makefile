# Lightweight monorepo orchestration for backend/ and frontend/
PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
UVICORN ?= uvicorn

.PHONY: help install install-backend install-frontend \
	run-backend run-frontend \
	build build-frontend \
	lint lint-backend lint-frontend

help:
	@echo "Available targets:"
	@echo "  make install            Install backend and frontend dependencies"
	@echo "  make install-backend    Install Python deps from backend/requirements.txt"
	@echo "  make install-frontend   Install npm deps in frontend/"
	@echo "  make run-backend        Run FastAPI via uvicorn (from repo root)"
	@echo "  make run-frontend       Run Vite dev server"
	@echo "  make build              Build frontend for production"
	@echo "  make build-frontend     Same as build"
	@echo "  make lint               Lint backend (compileall) and frontend (eslint)"
	@echo "  make lint-backend       Python syntax check via compileall"
	@echo "  make lint-frontend      ESLint in frontend/"

install: install-backend install-frontend

install-backend:
	$(PIP) install -r backend/requirements.txt

install-frontend:
	cd frontend && npm install

run-backend:
	$(UVICORN) backend.main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	cd frontend && npm run dev

build: build-frontend

build-frontend:
	cd frontend && npm run build

lint: lint-backend lint-frontend

lint-backend:
	$(PYTHON) -m compileall -q backend

lint-frontend:
	cd frontend && npm run lint
