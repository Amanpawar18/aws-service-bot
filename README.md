# AWS Support Bot

A conversational assistant that answers AWS questions using live AWS documentation. Powered by a **self-correcting agentic RAG pipeline** built on LangChain, Amazon Bedrock, and Tavily — deployed on ECS Fargate via AWS CDK.

---

## Agent Architecture

The core of this project is an **agentic pipeline** built with LangChain and LangGraph — not a simple prompt-response call. The agent autonomously decides when and what to search, then grounds its answer in the results.

```
User Question
      │
      ▼
LangChain ReAct Agent (LangGraph execution)
      │
      ├── AWS question? ──► Tavily Search (docs.aws.amazon.com)
      │                           │
      │                           ▼
      │                    Retrieved docs
      │                           │
      │                           ▼
      │                  Amazon Nova Pro (Bedrock)
      │                  generates grounded answer
      │                  with source URLs
      │
      ├── Greeting? ──► brief response, no search
      │
      └── Non-AWS question? ──► polite decline, no search
                    │
                    ▼
         Answer + Session Memory updated
         (persisted across turns via MemorySaver)
```

**Key agent properties:**
- **Tool-calling:** the agent autonomously decides when to invoke Tavily search and what query to use — the LLM drives the retrieval, not hardcoded logic
- **Grounded:** answers are sourced exclusively from `docs.aws.amazon.com`, never from model training data alone. Every answer includes a Sources section with URLs
- **Stateful:** session memory via LangGraph `MemorySaver` persists full conversation history across turns using a `thread_id`, enabling follow-up questions with complete context
- **Intent-aware:** the system prompt distinguishes between AWS questions, greetings, and off-topic questions — each handled differently without unnecessary tool calls

---

## System Architecture

```
User → Streamlit (Frontend) → FastAPI (Backend) → LangChain Agent
                                                        │
                                          ┌─────────────┴─────────────┐
                                          │                           │
                                    Tavily Search              Amazon Bedrock
                                  (docs.aws.amazon.com)         (Nova Pro)
```

**Infrastructure (AWS CDK):**
```
AWS
├── ECR
│   ├── aws-support-bot-backend
│   └── aws-support-bot-frontend
└── ECS Fargate (public subnets, no NAT Gateway)
    ├── BackendService  — FastAPI, port 8000, ALB on port 80
    └── FrontendService — Streamlit, port 8501, ALB on port 80
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Amazon Nova Pro via AWS Bedrock |
| Agent | LangGraph 1.2 (self-correcting RAG, max 3 retries) |
| Search | Tavily — scoped to `docs.aws.amazon.com` |
| Backend | FastAPI + uvicorn |
| Frontend | Streamlit |
| IaC | AWS CDK (Python) |
| Package manager | uv |
| Linting | ruff |
| Type checking | mypy (strict) |
| Testing | pytest + pytest-asyncio |

---

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Docker
- AWS CLI configured (`aws configure`)
- AWS account with Bedrock access to `amazon.nova-pro-v1:0`
- [Tavily API key](https://tavily.com)

---

## Local Development

**1. Copy and fill environment variables:**
```bash
cp .env.example .env
# Edit .env — set TAVILY_API_KEY and AWS credentials
```

**2. Install dependencies:**
```bash
make install
```

**3. Run locally:**
```bash
# Terminal 1 — backend
make run-be

# Terminal 2 — frontend
make run-fe
```

Backend: http://localhost:8000  
Frontend: http://localhost:8501

**Or with Docker Compose:**
```bash
make up
```

---

## Deployment

**First-time setup — deploy ECR repos:**
```bash
export $(cat .env | grep -v '^#' | xargs)
make deploy
```

**Push images to ECR:**
```bash
export $(cat .env | grep -v '^#' | xargs)
make push
```

**Deploy infrastructure changes:**
```bash
export $(cat .env | grep -v '^#' | xargs)
make deploy
```

The `FrontendUrl` and `BackendUrl` are printed at the end of `make deploy`.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `TAVILY_API_KEY` | Yes | Tavily search API key |
| `AWS_ACCESS_KEY_ID` | Yes | AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | Yes | AWS credentials |
| `AWS_REGION` | Yes | Target region (e.g. `us-east-1`) |
| `BACKEND_URL` | Frontend only | Backend ALB URL (set automatically in ECS) |

---

## Makefile Reference

| Command | Description |
|---|---|
| `make install` | Install all dependencies |
| `make run-be` | Run backend locally |
| `make run-fe` | Run frontend locally |
| `make up` | Start both via Docker Compose |
| `make down` | Stop Docker Compose |
| `make test-backend` | Run backend tests |
| `make test-frontend` | Run frontend tests |
| `make test-all` | Run all tests + CDK synth |
| `make lint` | Run ruff on all packages |
| `make typecheck` | Run mypy on all packages |
| `make fmt` | Format + auto-fix all packages |
| `make build` | Build Docker images |
| `make push` | Build and push both images to ECR |
| `make push-backend` | Push backend image only |
| `make push-frontend` | Push frontend image only |
| `make synth` | CDK synth (validate templates) |
| `make diff` | CDK diff (preview changes) |
| `make deploy` | CDK deploy all stacks |
| `make health` | Hit local backend health endpoint |

---

## Project Structure

```
aws-support-bot/
├── backend/          # FastAPI app + LangChain agent
│   ├── app/
│   │   ├── agent.py      # LangChain self-correcting RAG agent
│   │   ├── main.py       # FastAPI routes + lifespan
│   │   └── config.py     # pydantic-settings config
│   └── tests/
├── frontend/         # Streamlit UI
│   └── app/
│       ├── main.py       # Streamlit chat interface
│       └── client.py     # httpx backend client
├── infra/            # AWS CDK stacks
│   └── stacks/
│       ├── ecr_stack.py  # ECR repositories
│       └── ecs_stack.py  # ECS Fargate + ALB + VPC
├── tests/
│   └── integration/  # End-to-end integration tests
├── docker-compose.yml
├── Makefile
└── CLAUDE.md         # AI agent instructions
```
