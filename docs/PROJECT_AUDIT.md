# SHOPNOVA Project Audit

## 1. Existing project state

The repository at `D:\SHOPNOVA` is a git repository on branch `main` with **no commits yet**. It contains a partially implemented e-commerce application with three top-level areas:

- `backend/` — Python FastAPI application with SQLAlchemy 2.x models, Alembic migrations, API routers, Kafka/OpenSearch integration modules, consumer workers, seed scripts and unit/security/integration tests.
- `frontend/` — React + TypeScript + Vite + Tailwind storefront (incomplete: no app entry point, missing several required pages).
- `docs/` — `architecture.md` and `aiven-setup.md`.
- `scripts/` — `secret_scan.py`.

### Backend files present

| Area | Files |
|------|-------|
| Config | `app/core/config.py` (pydantic-settings, all required env names, no secret logging) |
| Security | `app/core/security.py` (Argon2 hashing, PyJWT access/refresh tokens) |
| Logging | `app/core/logging.py` (redacting formatter, structured-ish) |
| Database | `app/database/base.py`, `app/database/session.py` (sync psycopg[binary], UTC session setting) |
| Migrations | `alembic.ini`, `alembic/env.py`, `alembic/versions/0001_initial.py` |
| Models | `app/models/{user,catalog,inventory,order,cart,events,notification}.py` |
| Schemas | `app/schemas/common.py` (only common schemas; no per-domain schemas yet) |
| Services | `app/services/{auth_service,order_service,outbox,product_document}.py` |
| Kafka | `app/kafka/{envelope,producer}.py` |
| OpenSearch | `app/opensearch/{client,index,search}.py` |
| Routers | `app/api/routers/{auth,products,search,categories,cart,orders,addresses,inventory,admin}.py` + `deps.py` |
| Consumers | `consumers/{runtime,outbox_publisher,inventory_consumer,search_indexer,notification_consumer}.py` |
| Scripts | `scripts/{seed_catalog,catalog_data,provision_admin,reindex_products,verify_services}.py` |
| Entrypoint | `app/main.py` (CORS, SlowAPI limiter, security headers, `/api/health`) |
| Config example | `backend/.env.example` (placeholders only, all required names present) |
| Tests | `tests/unit/{test_inventory_sql,test_event_envelope,test_password,test_redaction,test_search_query}.py`, `tests/security/test_authorization_rules.py`, `tests/integration/{test_aiven_required,test_concurrent_orders}.py` |
| Dependencies | `requirements.txt` + `requirements-dev.txt` (pins match the mandated baseline) |

### Frontend files present

| Area | Files |
|------|-------|
| Build | `package.json`, `vite.config.ts`, `tailwind.config.js`, `tsconfig.json`, `index.html`, `postcss.config.js` |
| Entry | `index.html` references `/src/main.tsx` — **this file does not exist** |
| Styles | `src/index.css` (Tailwind + component utilities) |
| API client | `src/services/api.ts` (fetch client, `inr()` formatter) |
| Types | `src/types/index.ts` |
| Utils | `src/utils/format.ts` |
| Contexts | `src/contexts/AuthContext.tsx`, `src/contexts/ToastContext.tsx` |
| Layouts | `src/layouts/StoreLayout.tsx`, `src/layouts/AdminLayout.tsx` |
| Components | `src/components/ProductCard.tsx` (`src/components/ui/` empty) |
| Pages | `src/pages/{Home,Shop,Search,Product}.x`, `src/pages/admin/` empty |
| Hooks | `src/hooks/` empty |
| Config | `frontend/.env.example` |

### Docs present

- `docs/architecture.md` — service roles, Kafka Inkless constraints, OpenSearch mapping notes, process topology, trust boundaries.
- `docs/aiven-setup.md` — private setup steps for CA cert, `.env`, Kafka topics, OpenSearch index, migrations, seed, verification.

### Missing frontend pages vs. requirements

Required pages absent: **Cart, Checkout, Order Confirmation, Customer Orders (My Orders), Login, Register, Account/Profile**. Admin pages are entirely absent (`src/pages/admin/` is empty). There is no app router entry (`main.tsx`/`App.tsx`).

### Backend gaps vs. mandatory requirements

1. **Order flow does not match the transactional outbox spec.** `place_order()` in `app/services/order_service.py` decrements stock synchronously inside the HTTP request and creates the order already reserved. The spec requires: order created in a pending-inventory state + `order.created` outbox record in the same transaction; a separate Kafka consumer locks inventory, validates stock, confirms or rejects, and writes `order.confirmed` / `order.rejected` + `inventory.changed` outbox events in one DB transaction.
2. **Missing required event types.** Required: `order.created`, `order.confirmed`, `order.rejected`, `inventory.changed`, `product.created`, `product.updated`, `product.deleted`. Currently emitted: `OrderPlaced`, `InventoryUpdated`, `ProductCreated`, `ProductUpdated`, `OrderStatusUpdated`.
3. **No `product.deleted` handling** — OpenSearch documents are never removed/deactivated when a product is deactivated.
4. **No deterministic multi-row inventory locking.** Stock is checked/update one row at a time without `ORDER BY ... FOR UPDATE`, so two concurrent buyers of the last unit are only protected by the conditional UPDATE (good) but not by explicit ordered row locks as specified.
5. **Rate limiting configured but not enforced.** `SlowAPI` limiter exists in `main.py`; the login route has `if limiter: pass` — no `@limiter.limit` applied.
6. **Outbox publisher has no DLQ/dead-letter strategy** — rows simply stop being retried after 12 attempts.
7. **Consumer error handling is brittle** — `run_consumer` re-raises on handler failure, stopping the consumer; no per-message dead-lettering.
8. **Offset commit happens after DB commit** (correct), but a failed handler aborts the whole consumer loop instead of isolating the message.
9. **Health endpoint reports configuration only, not reachability.**
10. **`app/database/session.py` raises at connection time when PostgreSQL is unconfigured**, which prevents the API from starting in the required "development mode without pretending integrations are connected."
11. No per-domain Pydantic request/response schemas beyond `common.py`.
12. Frontend-only cart validation exists; backend checkout validation of prices/inventory against PostgreSQL at order time needs the rework in (1).

### What already works (by design; requires live Aiven credentials to execute)

- Database models, Alembic initial migration, seed script (idempotent by SKU), admin provisioning.
- Auth: register/login/refresh/me with Argon2 + JWT.
- Product catalog: list/detail with inventory; category list.
- Cart: add/update/remove with stock checks.
- Orders: place + list + get (currently synchronous reservation).
- Search: OpenSearch query builder with `fuzziness: AUTO`, filters, sorting, pagination (not executable without OpenSearch).
- Kafka: outbox envelope, producer, consumers with idempotency via `processed_events` (not executable without Kafka).
- OpenSearch: index creation, indexing, search, version-guarded upserts (not executable without OpenSearch).
- Admin: dashboard, orders, status update, inventory history, customers, notifications, system health (read-only against DB).
- Unit/security tests are self-contained and runnable without services.

### Risks / notes

- No `.env` exists; it must be created locally with placeholders and never committed (`.gitignore` covers `.env` and `certs/`).
- `certs/aiven-ca.pem` does not exist (only `.gitkeep`); TLS verification will fail until the user adds it.
- Frontend entry point missing → app cannot build/run.
- No frontend tests exist (vitest configured but no test files).
- Backend tests requiring PostgreSQL/Kafka/OpenSearch skip gracefully without credentials.

## 2. Identified issues (summary)

| # | Issue | Severity | Phase |
|---|-------|----------|-------|
| 1 | Order flow bypasses Kafka inventory consumer (synchronous stock reservation) | High | 3/6 |
| 2 | Required event names not used (`order.created`, `order.confirmed`, `order.rejected`, `inventory.changed`, `product.deleted`) | High | 3/6 |
| 3 | No deterministic ordered row-level locking for multi-item inventory | High | 6 |
| 4 | `product.deleted` / deactivation not synced to OpenSearch | Medium | 5 |
| 5 | Login rate limit not enforced | Medium | 3 |
| 6 | No DLQ / dead-letter strategy for persistently failing outbox events | Medium | 6 |
| 7 | Consumer crashes on single-message failure instead of isolating | Medium | 6 |
| 8 | API hard-fails when PostgreSQL unconfigured; must start in dev mode | Medium | 2/3 |
| 9 | Health reports config, not reachability | Low | 3 |
| 10 | Frontend entry point (`main.tsx`) missing | High | 2 |
| 11 | Missing pages: Cart, Checkout, Order Confirmation, My Orders, Login, Register, all admin pages | High | 4/7 |
| 12 | No frontend tests | Medium | 8 |
