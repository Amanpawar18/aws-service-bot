AWS_ACCOUNT_ID := $(shell aws sts get-caller-identity --query Account --output text 2>/dev/null)
ECR_REGISTRY   := $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com

.PHONY: install test-backend test-frontend test-infra test-all test-integration lint typecheck fmt build up down synth diff deploy ecr-login push-backend push-frontend push run-be run-fe health

install:
	cd backend && uv sync --group dev
	cd frontend && uv sync --group dev
	cd infra && uv sync --group dev

test-backend:
	cd backend && uv run pytest tests/ -v

test-frontend:
	cd frontend && uv run pytest tests/ -v || [ $$? -eq 5 ]

test-infra:
	cd infra && uv run cdk synth
	
test-all: test-backend test-frontend test-infra

test-integration:
	uv run pytest tests/integration/ -v

lint:
	cd backend && uv run ruff check .
	cd frontend && uv run ruff check .
	cd infra && uv run ruff check .

typecheck:
	cd backend && uv run mypy app/
	cd frontend && uv run mypy app/
	cd infra && uv run mypy stacks/

fmt:
	cd backend && uv run ruff format . && uv run ruff check --fix .
	cd frontend && uv run ruff format . && uv run ruff check --fix .
	cd infra && uv run ruff format . && uv run ruff check --fix .

build:
	docker compose build

up:
	docker compose up

down:
	docker compose down

synth:
	cd infra && uv run cdk synth

diff:
	cd infra && uv run cdk diff

deploy:
	cd infra && TAVILY_API_KEY=$$TAVILY_API_KEY uv run cdk deploy --all

ecr-login:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_REGISTRY)

push-backend: ecr-login
	docker build -t aws-support-bot-backend ./backend
	docker tag aws-support-bot-backend:latest $(ECR_REGISTRY)/aws-support-bot-backend:latest
	docker push $(ECR_REGISTRY)/aws-support-bot-backend:latest

push-frontend: ecr-login
	docker build -t aws-support-bot-frontend ./frontend
	docker tag aws-support-bot-frontend:latest $(ECR_REGISTRY)/aws-support-bot-frontend:latest
	docker push $(ECR_REGISTRY)/aws-support-bot-frontend:latest

push: push-backend push-frontend

run-be:
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-fe:
	cd frontend && PYTHONPATH=. uv run streamlit run app/main.py --server.port 8501

health:
	curl -s http://localhost:8000/health | python3 -m json.tool
