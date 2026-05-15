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
| `ruff 0.15.13` | Lint + format | `[tool.ruff]` in `pyproject.toml` |
| `mypy 2.1.0` | Type checking (strict mode) | `[tool.mypy]` in `pyproject.toml` |
| `pytest 9.0.3` | Test runner | `[tool.pytest.ini_options]` in `pyproject.toml` |
| `pytest-asyncio 1.1.0` | Async test support | `asyncio_mode = "auto"` |
| `pytest-mock 3.15.1` | Mocking | — |

Run before presenting any phase as complete:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy app/
uv run pytest tests/ -v
```

All four must pass. Do not present a phase as done if any of these fail.

---

## 6. Package Versions (pinned, verified May 2026)

Never upgrade or downgrade without confirming the new version from PyPI first. Always pin exact versions.

### Backend

```
fastapi==0.136.1
uvicorn[standard]==0.47.0
langchain==1.3.0
langgraph==1.2.0
langchain-aws==1.4.6
langchain-tavily==0.2.18
pydantic==2.13.4
pydantic-settings==2.14.1
boto3==1.43.8
httpx==0.28.1
python-json-logger==4.1.0
```

Dev:
```
pytest==8.4.2
pytest-asyncio==1.1.0
pytest-mock==3.15.1
ruff==0.15.13
mypy==2.1.0
boto3-stubs[bedrock-runtime]==1.43.8
```

### Frontend

```
streamlit==1.57.0
httpx==0.28.1
pydantic==2.13.4
pydantic-settings==2.14.1
```

### Infrastructure

```
aws-cdk-lib==2.254.0
constructs>=10.5.0
```

---

## 7. Architecture Decisions (do not revisit without developer approval)

- **LLM:** Amazon Nova Pro via AWS Bedrock (`amazon.nova-pro-v1:0`)
- **Search:** Tavily (`langchain-tavily`) with `include_domains=["docs.aws.amazon.com"]`
- **Agent:** LangGraph 1.2.0 with self-correcting retrieval loop (max 3 retries)
- **Session memory:** `MemorySaver` with `thread_id = session_id`
- **Backend:** FastAPI with `lifespan` context, `StreamingResponse` SSE for `/chat`
- **Frontend:** Streamlit calling FastAPI via `httpx.AsyncClient`
- **Infra:** AWS CDK Python, ECS Fargate, public subnets + security groups (no NAT Gateway)
- **Service communication:** ECS Service Connect (`http://backend:8000`)
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
