# SHOPNOVA

E-commerce platform with a FastAPI backend (SQLAlchemy 2, Alembic, Kafka event sourcing, OpenSearch search) and a React + Vite + Tailwind storefront. Uses the transactional outbox pattern for order/inventory consistency.

## Stack

**Backend** (`backend/`)
- FastAPI, SQLAlchemy 2.x, Alembic, Pydantic 2
- PyJWT (access/refresh), Argon2 password hashing, SlowAPI rate limiting
- Aiven PostgreSQL (TLS verify-full), Aiven Kafka Inkless (SASL_SSL/SCRAM-SHA-256), Aiven OpenSearch
- Dev mode: starts without credentials; `/api/health` reports unconfigured services as 503

**Frontend** (`frontend/`)
- React 18 + TypeScript + Vite + Tailwind CSS
- React Router, TanStack Query, React Hook Form + zod
- vitest + @testing-library + jsdom

**Events** (Kafka topics)
- `shopnova.order-events`: `order.created`, `order.confirmed`, `order.rejected`
- `shopnova.inventory-events`: `inventory.changed`
- `shopnova.product-events`: `product.created`, `product.updated`, `product.deleted`
- `shopnova.notification-events`
- `shopnova.dead-letter-events`

## Repository layout

```
SHOPNOVA/
├── backend/
│   ├── app/
│   │   ├── api/routers/     # auth, orders, cart, categories, inventory, admin, products
│   │   ├── schemas/         # Pydantic v2 schemas
│   │   ├── models/          # SQLAlchemy models (catalog, events/outbox)
│   │   ├── database/        # session/engine with dev-mode fallback
│   │   ├── services/        # order_service
│   │   └── main.py          # FastAPI app, lifespan, health, middleware
│   ├── consumers/           # inventory_consumer, outbox_publisher, runtime, search_indexer, notification_consumer
│   ├── requirements.txt
│   ├── .env                 # gitignored placeholders
│   └── tests/               # unit + security (16 tests)
├── frontend/
│   ├── src/
│   │   ├── main.tsx, App.tsx
│   │   ├── pages/           # Cart, Checkout, OrderConfirmation, MyOrders, OrderDetail, Login, Register, Account, admin pages
│   │   ├── components/ui/   # Button, Input, Card, Skeleton, EmptyState, Badge
│   │   ├── contexts/        # AuthContext, ToastContext
│   │   ├── services/        # api client
│   │   └── *.test.*         # vitest (8 tests)
│   ├── vitest.config.ts
│   ├── package.json
│   └── tsconfig.json
├── docs/
│   ├── architecture.md, aiven-setup.md, PROJECT_AUDIT.md, IMPLEMENTATION_PLAN.md
├── scripts/
│   └── secret_scan.py
└── README.md
```

## Prerequisites

- Python 3.12 + `venv`
- Node 18+ + npm
- Aiven services (PostgreSQL, Kafka Inkless, OpenSearch) for full operation — optional for dev mode

## Backend setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy `.env` (placeholders only, gitignored) and fill in Aiven credentials for PostgreSQL, Kafka, and OpenSearch. Leave them blank to run in dev mode (DB-backed endpoints return 503 until configured).

### Run the API

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run background workers

```powershell
.\.venv\Scripts\python.exe -m consumers.outbox_publisher   # outbox poll + publish
.\.venv\Scripts\python.exe -m consumers.runtime            # Kafka consumer runtime
.\.venv\Scripts\python.exe -m consumers.inventory_consumer # stock reservation processor
.\.venv\Scripts\python.exe -m consumers.search_indexer     # OpenSearch sync
.\.venv\Scripts\python.exe -m consumers.notification_consumer # notifications
```

### Migrations

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

### Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit tests/security
# 16 tests, runnable without Aiven credentials
```

### Lint / typecheck

```powershell
.\.venv\Scripts\python.exe -m ruff check app consumers tests   # if ruff installed
.\.venv\Scripts\python.exe -m mypy app consumers              # if mypy configured
```

## Frontend setup

```powershell
cd frontend
npm install
cp .env.example .env.local   # set VITE_API_BASE_URL=http://localhost:8000
```

### Run dev server

```powershell
npm run dev      # Vite on http://localhost:5173
```

### Tests

```powershell
npm test         # vitest run — 8 tests
```

### Build

```powershell
npm run build    # tsc -b && vite build
npm run preview  # serve production build locally
```

## Environment variables

Backend (`backend/.env`):
- `POSTGRES_HOST/PORT/DB/USER/PASSWORD`, `POSTGRES_SSLMODE=verify-full`, `AIVEN_CA_PATH`
- `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_SECURITY_PROTOCOL`, `KAFKA_SASL_MECHANISM`, `KAFKA_SASL_USERNAME/PASSWORD`, `KAFKA_SSL_CAFILE`, `KAFKA_TOPIC_PREFIX`
- `OPENSEARCH_URL`, `OPENSEARCH_USER/PASSWORD`, `OPENSEARCH_INDEX=shopnova-products`
- `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`
- `CORS_ORIGINS`, `FRONTEND_ORIGIN`, `RATE_LIMIT_LOGIN`, `RATE_LIMIT_DEFAULT`
- `OUTBOX_POLL_INTERVAL_SECONDS`, `CONSUMER_POLL_TIMEOUT_MS`, `SEED_DEMO_DATA`, `ADMIN_BOOTSTRAP_EMAIL/PASSWORD`

Frontend (`frontend/.env.local`):
- `VITE_API_BASE_URL=http://localhost:8000`

## Security

- `.env`, `.env.*`, `certs/` are gitignored; no credentials are committed.
- `scripts/secret_scan.py` scans tracked files for likely secrets (AWS keys, private keys, DB URLs with credentials, long passwords). Run before any public push:

```powershell
.\.venv\Scripts\python.exe scripts/secret_scan.py
```

- Login is rate-limited via SlowAPI (`RATE_LIMIT_LOGIN`). Passwords are hashed with Argon2. JWTs expire; refresh tokens rotate. Authorization is enforced on the backend, never the frontend.

## Key design points

- **Transactional outbox:** `order.created` is written to `outbox_events` in the same transaction as the order (`PLACED` state, no stock decrement). The outbox publisher polls and publishes to Kafka; the published flag is set only after Kafka ack. Failures go to the dead-letter topic after `MAX_PUBLISH_ATTEMPTS` — never silently discarded.
- **Inventory:** the inventory consumer locks products with `SELECT ... FOR UPDATE ORDER BY product_id`, validates all quantities, decrements only if fully satisfiable, then flips the order to `CONFIRMED` or `CANCELLED` and emits `order.confirmed`/`order.rejected` + `inventory.changed` in the same transaction. `processed_events` makes delivery idempotent.
- **OpenSearch:** the `shopnova-products` index is created at startup and kept in sync by the search-indexer consumer (`product.created/updated`, `inventory.changed`, `product.deleted`). Fuzzy search covers typos (e.g. `bluetoth` → Bluetooth).
- **Dev mode:** without Aiven credentials the API still starts; DB-backed endpoints return HTTP 503 and `/api/health` shows which services are unconfigured (no secrets logged).

## API

Interactive docs: `http://localhost:8000/docs` (Swagger) and `http://localhost:8000/openapi.json`.

Core endpoints:
- `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/refresh`, `POST /api/auth/logout`, `GET /api/auth/me`
- `GET /api/products`, `GET /api/products/{id}`, `POST /api/products` (admin), `PUT /api/products/{id}` (admin), `DELETE /api/products/{id}` (admin)
- `GET /api/cart`, `PUT /api/cart/items/{id}`, `DELETE /api/cart/items/{id}`
- `POST /api/orders` (checkout), `GET /api/orders`, `GET /api/orders/{id}`
- `GET /api/health` (DB, Kafka, OpenSearch reachability)

## Testing

- Backend: `pytest` — 16 tests (auth, passwords, search body, inventory SQL, redaction, authorization, order-service pending state, outbox enqueue, consumer idempotency). Runs without credentials.
- Frontend: `npm test` — 8 vitest tests (cart add/remove/update, checkout validation). Runs without a backend (API mocked).
- Acceptance: `pytest`, `npm run test`, `tsc -b`, `vite build` all green.

## Known items awaiting live Aiven credentials

- End-to-end Kafka flow (order.created → consumer → stock → order.confirmed/rejected).
- OpenSearch indexing and search against a live cluster.
- PostgreSQL-backed order/cart persistence beyond dev-mode stubs.
- Alembic migrations applied against a live database.

See `docs/IMPLEMENTATION_PLAN.md` acceptance criteria and `docs/PROJECT_AUDIT.md` for gaps and risks.

## License

Internal project — no license specified.
