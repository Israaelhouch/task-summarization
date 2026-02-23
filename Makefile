.PHONY: help install install-dev run run-prod test docker-build docker-run

PYTHON ?= python
PORT ?= 8000
IMAGE ?= task-summarizer
NAME ?= text-summarizer

help:
	@echo "Targets:"
	@echo "  install       Install runtime dependencies"
	@echo "  install-dev   Install dev dependencies"
	@echo "  run           Run the API locally"
	@echo "  test          Run tests"
	@echo "  docker-build  Build Docker image"
	@echo "  docker-run    Run Docker container"

install:
	$(PYTHON) -m pip install -e .

install-dev:
	$(PYTHON) -m pip install -e .[dev]

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port $(PORT)

run-prod:
	gunicorn -k uvicorn.workers.UvicornWorker -w $(WEB_CONCURRENCY) -b 127.0.0.1:$(PORT) app.main:app

test:
	pytest

docker-build:
	docker build -t $(IMAGE) .

docker-run:
	docker run --rm --name $(NAME) -p $(PORT):8000 $(IMAGE)
