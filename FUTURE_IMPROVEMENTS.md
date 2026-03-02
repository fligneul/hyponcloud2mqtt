# Future Improvements

Suggestions for the next wave of modernization, roughly ordered by impact/effort ratio.

## 🔥 High Impact, Low Effort

### 1. Migrate to `uv`

Replace `pip` with [`uv`](https://docs.astral.sh/uv/) for dependency management.

- 10-50x faster installs
- Proper lockfile (`uv.lock`) for reproducible builds
- Faster Docker builds
- Migration: `uv init` + move deps from `pyproject.toml`

### 2. Async `httpx`

Convert `DataFetcher` from threads (`ThreadPoolExecutor`) to `async/await` with `httpx.AsyncClient`.

- Simplifies concurrency — remove `ThreadPoolExecutor` and `_reauth_lock`
- The daemon loop in `daemon.py` would become an `asyncio` event loop
- `httpx` already supports async natively

### 3. `structlog` for structured logging

Replace stdlib `logging` with [`structlog`](https://www.structlog.org/) for structured JSON logs.

- Automatic context (timestamps, log levels as fields)
- Much better debugging in containerized environments (ELK/Loki/Grafana)
- Lazy `%s`-style formatting groundwork is already in place

## 🛠️ Medium Impact

### 4. Proper resource cleanup

`DataFetcher` creates an `httpx.Client` but never explicitly closes it. Add `__enter__`/`__exit__` (context manager) or a `close()` method, and call it in `Daemon.run()` cleanup.

### 5. `pydantic` for Config

Replace the manual `Config` dataclass + `_validate_config()` with a `pydantic.BaseModel`.

- Automatic validation and type coercion
- Env var loading via `pydantic-settings`
- The 100+ lines of manual env var parsing would collapse to ~30 lines

### 6. Pre-commit hooks

Add a `.pre-commit-config.yaml` with:

- `ruff` (lint + format)
- `mypy`

Catches issues before they hit CI.

### 7. Dockerfile update

- Bump the base image to Python 3.13
- If `uv` is adopted, use `uv pip install` in the Docker build for faster layer rebuilds

## 📐 Architecture

### 8. Health check improvement

The current `HealthServer` uses `http.server` which is blocking and single-threaded. If going async, replace with a lightweight async server (e.g., a single `aiohttp` route or an `asyncio` TCP server).

### 9. Graceful shutdown

The current signal handling + `self.running` flag could be replaced with `asyncio` cancellation for cleaner shutdown semantics (once async migration is done).

### 10. Test coverage reporting

Add `pytest-cov` and a coverage badge. The project already has good test coverage — making it visible would be a nice addition.
