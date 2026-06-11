API_DIR   := apps/api
FRONT_DIR := frontend
VENV      := $(API_DIR)/.venv/bin

.PHONY: dev api frontend install install-api install-frontend

dev: ## Start backend and frontend concurrently
	@trap 'kill 0' INT; \
	$(MAKE) api & $(MAKE) frontend & wait

api: ## Start backend (FastAPI)
	cd $(API_DIR) && .venv/bin/uvicorn main:app --reload

frontend: ## Start frontend (Next.js)
	cd $(FRONT_DIR) && npm run dev

install: install-api install-frontend ## Install all dependencies

install-api: ## Install backend dependencies
	cd $(API_DIR) && .venv/bin/pip install -r requirements.txt

install-frontend: ## Install frontend dependencies
	cd $(FRONT_DIR) && npm install

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
