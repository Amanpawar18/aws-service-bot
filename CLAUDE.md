# CLAUDE.md — AWS Support Bot

Project instructions for Claude Code and all sub-agents. These rules are non-negotiable and apply to every agent, every session, every task.

---

## 1. Commits — NEVER

**Claude must never run `git commit`, `git add`, `git push`, or any git command that writes to history.**

The developer reviews all changes and commits manually after each phase.

Read-only git commands (`git status`, `git diff`, `git log`) are acceptable only when explicitly needed to understand state. Never as part of a workflow.

---

## 2. TDD — Red → Green, Always

Every implementation phase follows this exact order:

1. **Write failing tests first** (RED) — tests must fail before any implementation exists
2. **Run the tests** — confirm they fail for the right reason
3. **Implement the minimum code** to make them pass (GREEN)
4. **Run the tests again** — confirm all pass
5. **Present the completed phase** to the developer for review

Never write implementation code before the tests exist for it. No exceptions.

---

## 3. Phase Discipline

Work is divided into small, independent phases (see the design spec). Each phase:

- Has a single clear deliverable
- Is fully implemented and tested before moving on
- Ends with a clear message to the developer: what was built, what the tests cover, what to review before committing

**Never start Phase N+1 until the developer has confirmed Phase N is complete.**

---

## 4. Python Best Practices (enforced in every file)

- **Python 3.12** — use modern syntax (`match`, `|` unions, `tomllib`, etc.)
- **Type hints on every function** — parameters, return types, local variables where non-obvious. No bare `Any` unless truly unavoidable.
- **`async def` everywhere** in FastAPI routes and LangGraph nodes — this is an async-first codebase
- **Pydantic v2 style** — `model_config = ConfigDict(...)`, not `class Config:`. `model_validator`, not `validator`.
- **`pydantic-settings`** for all config — no raw `os.environ.get()` calls in business logic
- **`logging` module** — never `print()` in non-test code. Use structured JSON logging via `python-json-logger`
- **`pathlib.Path`** over `os.path`
- **No bare `except:`** — always name the exception type
- **`__all__`** defined in every `__init__.py`
- **Docstrings** only where the WHY is non-obvious. Never write docstrings that restate what the function name already says.
- **No comments** describing what the code does — only comments explaining non-obvious constraints or workarounds

---

## 5. Tooling (use exactly these, no substitutions)

| Tool | Purpose | Config location |
|---|---|---|
| `uv` | Package management | `pyproject.toml` |
| `ruff` | Lint + format | `[tool.ruff]` in `pyproject.toml` |
| `mypy` | Type checking (strict mode) | `[tool.mypy]` in `pyproject.toml` |
| `pytest` | Test runner | `[tool.pytest.ini_options]` in `pyproject.toml` |
| `pytest-asyncio` | Async test support | `asyncio_mode = "auto"` |

Run before presenting any phase as complete:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy app/
uv run pytest tests/ -v
```

All four must pass. Do not present a phase as done if any of these fail.

---

## 6. Package Versions

Dependencies are managed via `uv.lock` for reproducible installs. `pyproject.toml` declares floating deps — the lockfile is the source of truth for exact versions. Never delete or manually edit `uv.lock`.

Run `uv sync --frozen` (or `uv sync --no-dev --frozen` in Docker) to install exactly what the lockfile specifies.

### Backend dependencies
`fastapi`, `uvicorn[standard]`, `langchain`, `langgraph`, `langchain-aws`, `langchain-tavily`, `pydantic`, `pydantic-settings`, `python-json-logger`

### Frontend dependencies
`streamlit`, `httpx`, `pydantic-settings`

### Infrastructure dependencies
`aws-cdk-lib==2.254.0`, `constructs>=10.5.0`

---

## 7. Architecture Decisions (do not revisit without developer approval)

- **LLM:** Amazon Nova Pro via AWS Bedrock (`amazon.nova-pro-v1:0`)
- **Search:** Tavily (`langchain-tavily`) with `include_domains=["docs.aws.amazon.com"]`
- **Agent:** LangChain `create_agent` (ReAct tool-calling agent with LangGraph execution backend) — the agent autonomously decides when to call Tavily and what query to use
- **Session memory:** LangGraph `MemorySaver` checkpointer with `thread_id = session_id`
- **Backend:** FastAPI with `lifespan` context, synchronous JSON response on `/chat` via `agent.ainvoke`
- **Frontend:** Streamlit calling FastAPI via `httpx.Client` (synchronous — Streamlit is not async)
- **Infra:** AWS CDK Python, ECS Fargate, public subnets only (no NAT Gateway)
- **Service communication:** Frontend calls backend via ALB DNS URL (`BACKEND_URL` env var)
- **IaC:** 2 CDK stacks — `EcrStack`, `EcsStack`
- **No Bedrock Knowledge Base, no S3, no OpenSearch Serverless**

---

## 8. Sub-agent Instructions

When a sub-agent is dispatched to implement any part of this project, the sub-agent must:

1. Read this `CLAUDE.md` before writing a single line of code
2. Follow the TDD red → green sequence — tests first, always
3. Never commit code — present the completed work for developer review
4. Use only the pinned package versions listed in Section 6
5. Run ruff, mypy, and pytest before reporting a phase complete
6. Follow the Python best practices in Section 4 without exception
7. Implement only what the current phase specifies — no scope creep, no "nice to have" extras
8. If a design decision is unclear, stop and ask — do not assume

---

## 9. Design Spec

Full design spec is at:
```
docs/superpowers/specs/2026-05-15-aws-support-bot-design.md
```

Read it before starting any implementation work.

---

## 10. Known Tech Debt

These are known gaps identified in code review. Do not work around them — fix them properly when addressed.

**Security (priority)**
- `TAVILY_API_KEY` is passed as a plaintext ECS environment variable. Should be stored in AWS Secrets Manager and injected via `secrets` in the task definition.
- `tavily_api_key: str` in `config.py` should be `SecretStr` to prevent the value appearing in logs and tracebacks.
- Both Dockerfiles run the process as root. Add `USER nobody` before `CMD`.

**Error handling**
- `/chat` route has no exception handling — a Bedrock throttle or Tavily timeout returns a raw 500. Should catch and return a clean `503 Service Unavailable`.

**CI/CD**
- `build.yml` builds Docker images locally but never pushes to ECR. It is a build-check workflow, not a real build pipeline. Needs ECR push + ECS force-redeploy steps (blocked on OIDC setup).

**Docker**
- Neither service has a `.dockerignore`. Build context includes `tests/`, `.venv/`, and `__pycache__/` unnecessarily.

**Tests**
- Agent tests only assert configuration passed to mocks — no behavioural coverage.
- No test for the error path when `agent.ainvoke` raises an exception.
