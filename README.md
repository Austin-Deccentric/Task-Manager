# Task Manager API

FastAPI + SQLModel task management API with user auth, SQLite persistence, API-key-guarded task routes, pagination, and background completion reports.

## Features

| Area | Endpoint | Description |
|------|----------|-------------|
| **Auth** | `POST /auth/register` | Create user — argon2 hashing via `pwdlib` |
| | `POST /auth/login` | Verify credentials, return profile |
| **Tasks** (`X-API-Key` required) | `GET /tasks/?skip=&limit=` | Paginated list |
| | `POST /tasks/?user_id=<email>` | Create task for existing user |
| | `PUT /tasks/{id}` | Partial update — `title` / `description` / `status` |
| | `PATCH /tasks/{id}/status?status=done` | Status-only update |
| | `DELETE /tasks/{id}` | Delete task |

- `TaskStatus`: `todo` · `in_progress` · `done`
- Password rule (8+ chars, letters+digits only, must contain upper + lower + digit) — enforced in Python with `field_validator` + `re` because Pydantic's Rust regex engine does not support `(?=...)` look-ahead.
- Background task: transitioning a task to `done` via `PUT` or `PATCH` appends a line to `completion_reports.log` using FastAPI `BackgroundTasks`.

## Tech Stack

- **Python** `>=3.14` — managed with [`uv`](https://docs.astral.sh/uv/) (`uv.lock` committed)
- **FastAPI** `>=0.141` (`fastapi[standard]`)
- **SQLModel** `>=0.0.42` (SQLAlchemy + Pydantic v2)
- **pwdlib[argon2]** `>=0.3.1`
- **SQLite** — no migrations, `SQLModel.metadata.create_all()` on startup

## Project Structure

```
.
├── main.py                  # FastAPI app + lifespan (create tables / dispose engine)
├── pyproject.toml / uv.lock
├── task_manager.db          # SQLite file (created on startup, gitignored via *.db)
├── completion_reports.log   # DONE-task log (gitignored via *.log)
└── src/
    ├── db.py                # engine, DB_FILE, create_db_and_tables(), SessionDep
    ├── auth/
    │   ├── models.py        # UserBase / UserCreate (+password validator) / UserLogin
    │   ├── schemas.py       # User table (PK=email, Relationship → Task)
    │   └── router.py        # /auth/register, /auth/login
    └── task/
        ├── models.py        # TaskStatus enum, TaskCreate / TaskUpdate / TaskResponse
        ├── schemas.py       # Task table (FK user.email CASCADE, Relationship → User)
        ├── router.py        # CRUD + PATCH /status (documented path params)
        ├── dependencies.py  # verify_api_key (X-API-Key), PaginationParams
        └── report.py        # log_completion_report() → completion_reports.log
```

`User ↔ Task` is a bidirectional relationship using `TYPE_CHECKING` forward refs (`list["Task"]` / `Relationship(back_populates=...)`). `src/db.py` imports both models before `create_all()` so metadata is complete.

## Prerequisites

- `uv` installed — https://docs.astral.sh/uv/getting-started/installation/
- Python 3.14 will be provisioned by `uv` automatically. Do **not** use system `python` directly (`requires-python = ">=3.14"`).

## Installation

```bash
git clone <repo-url> && cd Task-Manager

# install deps (creates .venv)
uv sync
```

No linter / formatter / test runner is configured.

## Running

```bash
# dev with auto-reload + docs
uv run fastapi dev main.py

# or
uv run uvicorn main:app --reload
```

- App title: `Task Manager`
- Lifespan prints `Application is starting up, creating database...` and creates `task_manager.db` if missing.
- Docs: http://127.0.0.1:8000/docs (Swagger) · http://127.0.0.1:8000/redoc

> **Note on prefix:** `FastAPI(prefix="/api/v1")` in `main.py:28` has no effect in FastAPI — routers are mounted at `/auth` and `/tasks` directly. Use `app.include_router(..., prefix="/api/v1")` if versioned paths are desired.

## API Reference

All `/tasks` routes require:

```
X-API-Key: my_api_key
```

`src/task/dependencies.py:7` — hardcoded for this exercise; replace with env var / secrets in production.

### Register

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"ada","email":"ada@example.com","password":"Passw0rd1","age":30}'
# 201 → {username, email}  ·  400 email already exists
```

### Login

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ada@example.com","password":"Passw0rd1"}'
# 200 → {username, email}  ·  404 unknown email  ·  401 wrong password
```

### Create Task

```bash
curl -X POST "http://127.0.0.1:8000/tasks/?user_id=ada@example.com" \
  -H "Content-Type: application/json" -H "X-API-Key: my_api_key" \
  -d '{"title":"Write README","description":"Document the API","status":"todo"}'
# 201 → {id, title, description, status, user_id}  ·  404 user not found
```

### List (paginated)

```bash
curl "http://127.0.0.1:8000/tasks/?skip=0&limit=10" -H "X-API-Key: my_api_key"
```

### Update / Status / Delete

```bash
# partial update (any of title/description/status)
curl -X PUT http://127.0.0.1:8000/tasks/1 \
  -H "Content-Type: application/json" -H "X-API-Key: my_api_key" \
  -d '{"status":"done"}'

# status-only
curl -X PATCH "http://127.0.0.1:8000/tasks/1/status?status=done" \
  -H "X-API-Key: my_api_key"

# delete
curl -X DELETE http://127.0.0.1:8000/tasks/1 -H "X-API-Key: my_api_key"
```

### Completion Report

When a task flips to `done` (via `PUT` or `PATCH` — guarded by `was_done` so re-marking does not duplicate), a background task appends to `completion_reports.log`:

```
[2026-09-09T21:25:38.406247+00:00] TASK 1 DONE - "Write README" (owner: ada@example.com)
```

The router snapshots plain values (`id`, `title`, `user_id`, `datetime.now(timezone.utc)`) before the session closes — the ORM object is never passed to the background task (`src/task/router.py:80`, `src/task/report.py:4`).

## Data Models

```python
# User  — src/auth/schemas.py:12
email: EmailStr (PK) | username: str(3-50, unique) | hashed_password | age 16..119 | created_at

# Task  — src/task/schemas.py:15
id: int PK | title: str(≤128) | description | status: TaskStatus | created_at | user_id FK → user.email
```

`created_at` uses a dual default: `default_factory=lambda: datetime.now(timezone.utc)` (Python) + `sa_column_kwargs={"server_default": func.datetime("now")}` (SQLite). SQLite has no `timezone()` function — `func.datetime("now")` renders as `DEFAULT (datetime('now'))`; bare `DEFAULT datetime('now')` is a syntax error.

## Configuration & Gotchas

- **DB location:** `src/db.py:11` → `Path(__file__).parent.parent / "task_manager.db"` (repo root), `check_same_thread=False`, `echo=True`.
- **Per-request session:** `SessionDep = Annotated[Session, Depends(get_session)]` — `get_session()` yields and closes per request.
- **Stale DB:** `task_manager.db` / `completion_reports.log` are gitignored (`*.db`, `*.log` in `.gitignore:3`) but persist on disk. `create_all()` skips existing tables — after model changes run `rm task_manager.db` to regenerate.
- **Smoke check:** `uv run python -c "import src.task.router, src.auth.router"` — this is the only lightweight verification currently available.

## Troubleshooting

| Symptom | Cause / Fix |
|---------|-------------|
| `ImportError: circular import` | Keep runtime imports one-way; type-only side under `if TYPE_CHECKING:` with string annotations |
| `SchemaError: look-around not supported` | Don't use `(?=...)` in `Field(pattern=)` — use `@field_validator` + `re` |
| `sqlite3.OperationalError: unknown function: timezone()` | SQLite lacks Postgres `timezone()` — use `func.datetime("now")` / `CURRENT_TIMESTAMP` and delete the stale `.db` |
| `401 Invalid API Key` | Missing `X-API-Key: my_api_key` on `/tasks` requests |
