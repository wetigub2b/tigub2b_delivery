# Delivery BFF (FastAPI)

## Purpose
Bridges Vue delivery client with core `tigu_b2b` services, enforcing auth, data shaping, and integration with maps/geocoding.

## Tech Stack
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (async) with MySQL connector
- Redis for session tokens, order assignment cache
- Pydantic models mirroring `tigu_order`, `tigu_order_item`, `tigu_user_address`, `tigu_warehouse`
- HTTPX for upstream calls (payments, notifications)

## Key Modules
- `auth`: OAuth2 password flow (driver login via `sys_user` with role `driver`), refresh tokens
- `orders`:
  - `GET /orders/assigned` – list active tasks (status `1/2` and shipping status `<3`)
  - `POST /orders/{id}/accept`
  - `POST /orders/{id}/status` – update `shipping_status`, log event trail
  - `POST /orders/{id}/proof` – upload POD images to object storage, link into `tigu_uploaded_files`
- `navigation`:
  - `POST /routes/optimize` – call Google Directions API, persist plan snapshot
  - `PATCH /routes/{id}/location` – live GPS ticks for dispatcher dashboard (future)
- `warehouses`: `GET /warehouses/active` for pickup site selection
- `notifications`: push to FCM/websocket hub for urgent tasks

## Data Access
- Use read/write replicas if available; default pool size 10
- Soft map dictionary values using `sys_dict_data` for localization
- Store driver geo updates in Redis TTL 15m for real-time map overlays

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
    workers/
  tests/
    integration/
    unit/
```

## Local Development
- `pip install -r requirements.txt`
- `uvicorn app.main:app --reload`
- `.env` sample
  - `DATABASE_URL=mysql+asyncmy://user:pass@localhost:3306/tigu_b2b`
  - `REDIS_URL=redis://localhost:6379/0`
  - `GOOGLE_MAPS_API_KEY=...`

## Observability & Ops
- Structured logging (JSON) with request ID bridging client telemetry
- Healthcheck: `GET /health` verifying DB and maps token
- Background task to reconcile `tigu_order` shipping state with upstream ERP every 5 min
