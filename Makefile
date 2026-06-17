API_DIR   := apps/api
FRONT_DIR := frontend
VENV      := $(API_DIR)/.venv/bin

# Parse port numbers passed as positional args: make prod <FRONT_PORT> <API_PORT>
_ARGS      := $(filter-out $(firstword $(MAKECMDGOALS)),$(MAKECMDGOALS))
FRONT_PORT ?= $(or $(word 1,$(_ARGS)),3000)
API_PORT   ?= $(or $(word 2,$(_ARGS)),8000)

.PHONY: dev api frontend install install-api install-frontend prod

dev: ## Start backend and frontend concurrently
	@trap 'kill 0' INT; \
	$(MAKE) api & $(MAKE) frontend & wait

api: ## Start backend (FastAPI)
	cd $(API_DIR) && .venv/bin/uvicorn main:app --reload

frontend: ## Start frontend (Next.js)
	cd $(FRONT_DIR) && npm run dev

venv: ## Create Python virtual environment in apps/api/.venv
	python3 -m venv $(API_DIR)/.venv

install: install-api install-frontend ## Install all dependencies

install-api: ## Install backend dependencies
	cd $(API_DIR) && .venv/bin/pip install -r requirements.txt

install-frontend: ## Install frontend dependencies
	cd $(FRONT_DIR) && npm install

prod: ## Start in production mode: make prod [FRONT_PORT] [API_PORT] (defaults: 3000 8000)
	@trap 'kill 0' INT; \
	(cd $(API_DIR) && .venv/bin/uvicorn main:app --host 0.0.0.0 --port $(API_PORT)) & \
	(cd $(FRONT_DIR) && NEXT_PUBLIC_API_URL=https://srv28-$(API_PORT).wykr.es npm run build && npm run start -- -p $(FRONT_PORT)) & \
	wait

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# Absorb port numbers passed as positional make targets
ifneq ($(_ARGS),)
$(_ARGS):
	@:
endif
