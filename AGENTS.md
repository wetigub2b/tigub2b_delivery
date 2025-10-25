# Repository Guidelines

## Project Structure & Module Organization
- `frontend/` holds the Vue 3 delivery client (Vite, Pinia, Google Maps integrations); see `frontend/README.md` for feature specs.
- `bff/` contains the FastAPI layer bridging the client with MySQL, Redis, and external services; design notes live in `bff/README.md`.
- Shared assets (design docs, scripts) belong at the repo root; create language-specific subfolders as needed (e.g., `scripts/python/`).

## Build, Test, and Development Commands
- Frontend: `npm install`, `npm run dev`, `npm run build`, `npm run test:unit`, `npm run lint` (run from `frontend/`).
- BFF: `pip install -r requirements.txt`, `uvicorn app.main:app --reload`, `pytest`, `ruff check .` (run from `bff/`).
- Use Vite proxy (`VITE_API_URL`) to point the frontend at the local BFF during development.
- to deploy front end use script deploy_frontend.sh
- to deploy backend use script deploy_backend.sh

## Coding Style & Naming Conventions
- Vue components and directories use PascalCase (`DriverDashboard.vue`); composables use `useThing.ts` naming.
- Python modules use snake_case; FastAPI routes grouped by resource (`orders.py`, `auth.py`).
- Apply Prettier + ESLint in the frontend and Ruff + Black in the BFF; run formatters before every PR.
- Use 2-space indentation for Vue/TS, 4 spaces for Python; keep line length ≤ 100 chars.

## Testing Guidelines
- Favor Vitest component tests for complex interaction states (maps, offline queues) and Cypress e2e smoke flows.
- BFF tests cover Pydantic schemas, service functions, and route contracts with async `pytest` fixtures.
- Provide seed factories for critical tables (`tigu_order`, `tigu_order_item`, `tigu_user_address`) to mirror delivery scenarios.
- Aim for 80% line coverage, with explicit justification if lower.

## Commit & Pull Request Guidelines
- Follow Conventional Commits (`feat:`, `fix:`, `docs:`); scope by module (`feat(frontend): add proof upload`).
- Keep commits focused; include schema or command references when touching MySQL entities (`refs tigu_order.shipping_status`).
- PRs must state purpose, testing evidence, screenshots/GIFs for UI, and affected API endpoints; link Jira/GitHub issues.
- Request review from both frontend and backend maintainers when changes cross the boundary.

## Security & Configuration Tips
- Never commit secrets; rely on `.env.local` (frontend) and `.env` (BFF) ignored by Git.
- Restrict BFF credentials to read/write accounts scoped to `tigu_b2b`; rotate keys quarterly.
- Validate all status transitions against `sys_dict_data` enumerations to prevent invalid delivery states.
## mysql data base
- use database tigu_b2b
- use sudo mysql command to investigate the mysql database data
