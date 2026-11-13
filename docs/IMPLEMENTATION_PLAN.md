# SHOPNOVA Implementation Plan

## Target architecture

- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS + React Router + TanStack Query + React Hook Form. Single storefront with protected customer routes and a separate protected admin branch.
- **Backend:** FastAPI + SQLAlchemy 2.x (sync psycopg[binary] against Aiven PostgreSQL via TLS verify-full) + Alembic + Pydantic 2 + PyJWT (access/refresh) + Argon2 + SlowAPI + structlog-style redacting logger.
- **PostgreSQL (source of truth):** users, customer profiles/addresses, roles, products, categories, product images, inventory, inventory transactions, carts, cart items, orders, order items (historical prices), outbox events, processed events (idempotency), notifications.
- **Kafka (Aiven Inkless, no transactions):** topics `shopnova.order-events`, `shopnova.inventory-events`, `shopnova.product-events`, `shopnova.notification-events`, `shopnova.dead-letter-events`. Event types: `order.created`, `order.confirmed`, `order.rejected`, `inventory.changed`, `product.created`, `product.updated`, `product.deleted`.
- **OpenSearch:** index `shopnova-products`, mapping with fuzzy full-text search, category/price/city/availability filters, sorting, pagination; kept in sync via the search-indexer consumer.
- **Transactional outbox:** PostgreSQL `outbox_events` table written in the same transaction as business state; independent publisher polls and publishes; published flag set after Kafka ack; idempotency via `processed_events`; offsets committed only after the DB transaction succeeds.

## Implementation phases

### Phase 1 — Audit and architecture (this document)
- `docs/PROJECT_AUDIT.md` — existing state, gaps, risks.
- `docs/IMPLEMENTATION_PLAN.md` — this plan.

### Phase 2 — Project foundation
- Create Python venv, install `backend/requirements.txt` (pinned versions preserved).
- Create `backend/.env` from `.env.example` with placeholders only (gitignored).
- Create frontend entry `src/main.tsx` with Router, AuthProvider, ToastProvider, QueryClient.
- Add shared UI components (Button, Input, Card, Skeleton, EmptyState) in `src/components/ui`.
- Add `.env` for frontend (`VITE_API_BASE_URL`).

### Phase 3 — PostgreSQL and core business services
- Rework `order_service.place_order()`: create order in `PLACED` (pending inventory) state, persist historical-priced order items, write `order.created` outbox event in the same transaction; **do not** decrement stock here.
- Add deterministic multi-item inventory locking in the inventory consumer: `SELECT ... FOR UPDATE` ordered by `product_id`, validate all quantities, decrement only if fully satisfiable, record `inventory_transactions`, flip order to `CONFIRMED` or `CANCELLED`, write `order.confirmed` / `order.rejected` + `inventory.changed` to outbox in the same transaction; record `processed_events` idempotency row.
- Align event emission to required names: `order.created`, `order.confirmed`, `order.rejected`, `inventory.changed`, `product.created`, `product.updated`, `product.deleted` (products router + admin stock adjustment).
- Enforce SlowAPI rate limit on `/api/auth/login` (`RATE_LIMIT_LOGIN`); default limit on other routes.
- Make `get_db` degrade to HTTP 503 when PostgreSQL is unconfigured so the API starts in dev mode without credentials.
- Expand `/api/health` with reachability probes (DB ping, Kafka bootstrap, OpenSearch ping) without logging secrets.
- Add per-domain Pydantic schemas (`app/schemas/products.py`, `orders.py`, `cart.py`, `auth.py`, `admin.py`).
- Ensure Alembic migration covers outbox/processed_events (already present in `0001_initial`).

### Phase 4 — Storefront (customer-facing)
- Pages: Home (exists, verify), Shop/Listing (exists, verify), Product detail (exists, verify), **Cart**, **Checkout** (name, email, phone, address, city, state, PIN, COD/simulated payment, order summary), **Order Confirmation**, **My Orders** (list + detail + status), **Login**, **Register**, **Account**.
- Cart persisted server-side (PostgreSQL carts/cart items); frontend reads/writes via API.
- Checkout validates prices/inventory against PostgreSQL on the backend; demo COD only, no real card fields.
- Loading skeletons, empty states, validation errors, INR formatting, responsive layout.

### Phase 5 — OpenSearch
- Auto-create index at API startup when OpenSearch is configured (`ensure_product_index()`).
- Keep `index_product_document` version-guarded; add `remove_product_document` for `product.deleted`.
- Search-indexer consumer handles `product.created`, `product.updated`, `inventory.changed`, `product.deleted`.
- Reindex script (`scripts/reindex_products.py`) exists — keep, add CLI wrapper if needed.
- Fuzzy `bluetoth` → Bluetooth coverage verified by unit test on `build_search_body`.

### Phase 6 — Kafka (Inkless, no transactions)
- Outbox publisher: poll loop, publish per row, mark published after ack; on repeated failure increment attempts, move to dead-letter topic after max attempts, log structured error, continue with next row (do not stop).
- Consumers: per-message try/except; on unrecoverable failure send to DLQ and commit offset; on transient failure leave uncommitted / retry with backoff; `enable_auto_commit=False`, commit after DB transaction.
- `inventory_consumer` becomes the authoritative stock processor (see Phase 3).
- `notification_consumer` persists order confirmation notifications.
- Consumer offset management: manual commit after DB commit; never commit before DB success.

### Phase 7 — Admin interface
- Backend: product CRUD (create/update/deactivate), inventory adjustment with `inventory.changed` event, order list + status update with `order.status.updated`-style event, customer list, dashboard stats, outbox/processed event monitoring, reindex trigger.
- Frontend admin pages (protected, `role === ADMIN`, backend-enforced): Dashboard, Products, Categories, Orders, Inventory, Customers, Events, Search sync, Health.
- Backend authorization never relies on frontend.

### Phase 8 — Testing
- Backend unit tests (runnable without Aiven): auth (register/login/token), password hashing, event envelope, search query body (fuzzy + filters), inventory reservation SQL, redaction, authorization guards, plus new tests for order-service pending state, outbox enqueue, consumer idempotency (fakes).
- Backend integration tests: skipped without credentials; documented how to run against live Aiven.
- Frontend vitest tests: cart add/remove/update, checkout form validation, product listing, auth guard, search fuzzy hint.
- Run `pytest`, `npm run test`, `tsc -b`, `vite build`.

### Phase 9 — Documentation and delivery
- `README.md`: overview, features, architecture, stack, structure, setup, env config, PostgreSQL/Kafka/OpenSearch config, migrations, seeding, running frontend/backend/workers/tests, API docs, security, troubleshooting.
- `docs/ARCHITECTURE.md`, `docs/DATABASE_SCHEMA.md`, `docs/KAFKA_EVENTS.md`, `docs/OPENSEARCH.md`, `docs/SETUP_AIVEN.md`, `docs/TESTING.md`, `docs/DEMO_GUIDE.md` (refresh existing `architecture.md`/`aiven-setup.md` as needed).
- Mermaid diagrams for architecture and event flows.
- Secret scan (`scripts/secret_scan.py`) clean; `.env` and `certs/` gitignored; no credentials in code/docs.
- `docs/COMPLETION_REPORT.md`: features, files changed, test results, integrations awaiting credentials, known issues, start commands.

## Acceptance criteria (checked at the end)

1. Existing files preserved; no git history destroyed; no `.env` committed.
2. Frontend builds and runs; all required pages functional against real backend APIs.
3. Backend starts without Aiven credentials (dev mode, health shows unconfigured).
4. Orders persist in PostgreSQL; inventory reservation prevents overselling under concurrency.
5. `order.created` → Kafka → consumer → stock locked → `order.confirmed`/`order.rejected` + `inventory.changed` → Kafka.
6. Duplicate event delivery is idempotent (`processed_events`).
7. OpenSearch powers search; `bluetoth` typo returns Bluetooth products; category/price/city filters work; inventory changes update indexed documents.
8. Admin login + CRUD protected on backend.
9. Auth: register/login/refresh/logout/me; Argon2 hashes; JWT expiration.
10. Tests run; results reported honestly; no claimed live-integration runs without real services.
