# Delivery BFF (FastAPI)

## Purpose
Bridges Vue delivery client with core delivery services, enforcing auth, data shaping, and integration with maps/geocoding.

## Tech Stack
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (async) with **SQLite** (`aiosqlite`) by default; MySQL (`asyncmy`) still supported via `DATABASE_URL`
- Redis for session tokens / driver locations (**optional** — in-memory fallback when unreachable)
- Pydantic models mirroring `tigu_order`, `tigu_order_item`, `tigu_warehouse`
- HTTPX for upstream calls (payments)

## Key Modules
- `auth`: driver login via `sys_user` (phone + OTP `123456`), admin login (username + password), refresh tokens
- `orders`:
  - `GET /orders/{order_sn}` – order detail
  - `POST /orders/{id}/status` – update `shipping_status`, log event trail
- `prepare_goods`: merchant preparation workflow (`/prepare-goods/*`)
- `routes`:
  - `POST /routes/optimize` – route plan
  - `PATCH /routes/{id}/location` – live GPS ticks (stored in Redis w/ in-memory fallback)
- `warehouses`: `GET /warehouses/active` for pickup site selection
- `marks`: `GET /marks` – pickup location pins from `tigu_driver_marks`
- `notifications`: local-DB notifications (`tigu_notification`) — see `NOTIFICATION.md`
  - Admin: `POST /notifications/broadcast`, `POST /notifications/driver/{id}`, `POST /notifications/alert/{id}`
  - Driver: `GET /notifications/mine`, `POST /notifications/mine/{id}/read|dismiss`, `/mine/read-all`, `/mine/clear`

## Data Access
- Default DB: SQLite file `bff/data/delivery.db` (`DATABASE_URL=sqlite+aiosqlite:///./data/delivery.db`)
- Portable column types (`BigInteger`/`Integer`) work on both SQLite and MySQL
- Auto-increment PKs use `Integer` (SQLite `rowid`); snowflake-ID tables keep `BigInteger`
- Store driver geo updates in Redis (TTL 15m) with in-memory fallback

## Folder Layout
```
bff/
  app/
    api/
      v1/
        routes/
    core/
    db/
    models/
    schemas/
    services/
  tests/
    integration/
    unit/
  init_sqlite.py   # create tables + seed admin/driver/warehouse/marks
  data/
    delivery.db    # SQLite file (gitignored)
```

## Local Development
- `pip install -r requirements.txt` (from `bff/`)
- `DATABASE_URL="sqlite+aiosqlite:///./data/delivery.db" ./​.venv/bin/python init_sqlite.py` – create + seed
- `uvicorn app.main:app --reload --port 9000` (or `bash ../deploy_backend.sh`)
- `.env` sample
  - `DATABASE_URL=sqlite+aiosqlite:///./data/delivery.db`
  - `REDIS_URL=redis://localhost:6379/0` (optional)
  - `GOOGLE_MAPS_API_KEY=...`
- Seed accounts: admin `admin/admin123`, driver `15888888888/123456`

## Observability & Ops
- Structured logging with request ID bridging client telemetry
- Healthcheck: `GET /health` verifying DB and Redis
