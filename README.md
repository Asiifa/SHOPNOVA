# SHOPNOVA

SHOPNOVA is a full-stack e-commerce platform built with **React, TypeScript, FastAPI, PostgreSQL, Apache Kafka, and OpenSearch**. It provides a modern shopping experience supported by backend APIs, event-driven processing, inventory management, and product search.

The project uses Aiven-managed infrastructure for PostgreSQL, Kafka, and OpenSearch.

---

## 1. Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React 18, TypeScript, Vite |
| Styling | Tailwind CSS |
| Backend | Python 3.12, FastAPI |
| Database | PostgreSQL, SQLAlchemy 2.x |
| Migrations | Alembic |
| Event Streaming | Apache Kafka (Aiven) |
| Search Engine | OpenSearch (Aiven) |
| Authentication | JWT, Argon2 password hashing |
| Validation | Pydantic 2, Zod |
| Testing | Pytest, Vitest, Testing Library |
| Infrastructure | Aiven Cloud Services |

## 2. Key Features

### Customer Storefront
- Modern and responsive e-commerce interface.
- Product catalogue and product detail pages.
- Product search and category browsing.
- Customer registration and login.
- Shopping cart management.
- Checkout and order placement.
- Order history and order details.
- Customer account management.

### Admin Dashboard
- Product management.
- Category management.
- Inventory monitoring.
- Order management.
- Customer management.
- Search management.
- System health monitoring.
- Event monitoring.

### Backend and Distributed Architecture
- RESTful APIs using FastAPI.
- PostgreSQL-backed data access.
- JWT-based authentication and authorization.
- Password hashing with Argon2.
- Event-driven order and inventory processing.
- Transactional outbox pattern.
- Kafka event publishing and consumer services.
- OpenSearch product indexing and search.
- Idempotent event processing.
- Dead-letter event handling.

## 3. System Architecture

```text
              CUSTOMER
                  |
                  v
        React + TypeScript
          SHOPNOVA Store
                  |
                  v
           FastAPI Backend
                  |
       +----------+-----------+
       |          |           |
       v          v           v
  PostgreSQL    Kafka     OpenSearch
   (Aiven)     (Aiven)      (Aiven)
       |          |           ^
       |          v           |
       |    Event Consumers   |
       |          |           |
       +----------+-----------+
                  |
                  v
       Inventory and Order
          Processing
```

The transactional outbox pattern helps ensure that order events are recorded in the same database transaction as the corresponding order operation. Background workers publish events to Kafka for asynchronous processing.

## 4. Project Structure

```text
SHOPNOVA/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routers/
│   │   ├── core/
│   │   ├── database/
│   │   ├── kafka/
│   │   ├── models/
│   │   ├── opensearch/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── alembic/
│   ├── consumers/
│   ├── scripts/
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── contexts/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.tsx
│   │
│   ├── package.json
│   └── .env.example
│
├── docs/
│   ├── architecture.md
│   ├── aiven-setup.md
│   ├── COMPLETION_REPORT.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── PROJECT_AUDIT.md
│
├── scripts/
│   └── secret_scan.py
│
├── .gitignore
└── README.md
```

## 5. Prerequisites

Install the following:

- Python 3.12 or later.
- Node.js 18 or later.
- npm.
- Git.
- Aiven PostgreSQL, Kafka, and OpenSearch credentials for cloud-backed functionality.

## 6. Local Setup

Clone the repository:

```bash
git clone https://github.com/Asiifa/SHOPNOVA.git
cd SHOPNOVA
```

### Backend Setup

Open a terminal:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment on Windows:

```cmd
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your local environment file from the example:

```cmd
copy .env.example .env
```

Configure the required environment variables privately in `backend/.env`.

### Backend Environment Configuration

The backend supports the following service configurations:

**PostgreSQL**
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_SSLMODE`
- `AIVEN_CA_PATH`

**Kafka**
- `KAFKA_BOOTSTRAP_SERVERS`
- `KAFKA_SECURITY_PROTOCOL`
- `KAFKA_SASL_MECHANISM`
- `KAFKA_SASL_USERNAME`
- `KAFKA_SASL_PASSWORD`
- `KAFKA_SSL_CAFILE`
- `KAFKA_TOPIC_PREFIX`

**OpenSearch**
- `OPENSEARCH_URL`
- `OPENSEARCH_USER`
- `OPENSEARCH_PASSWORD`
- `OPENSEARCH_INDEX`

Additional application settings include JWT configuration, CORS origins, rate limits, and worker settings. Refer to `.env.example` and `docs/aiven-setup.md`.

**Important:** Never commit `.env`, passwords, private keys, certificates, or service credentials.

### Run the Backend

From the `backend` directory:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend API:

`http://127.0.0.1:8000`

Interactive API documentation:

`http://127.0.0.1:8000/api/docs`

Health endpoint:

`http://127.0.0.1:8000/api/health`

### Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
```

Create the local frontend environment file:

```cmd
copy .env.example .env.local
```

Configure:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Run the development server:

```bash
npm run dev
```

Frontend:

`http://localhost:5173`

## 7. Background Workers

The backend includes background processing components for event publishing and asynchronous operations.

Run the workers from the backend directory:

```bash
python -m consumers.outbox_publisher
```

```bash
python -m consumers.runtime
```

```bash
python -m consumers.inventory_consumer
```

```bash
python -m consumers.search_indexer
```

```bash
python -m consumers.notification_consumer
```

These workers require the corresponding infrastructure services and configurations.

## 8. Event-Driven Processing

SHOPNOVA uses Kafka for asynchronous event communication.

The event categories include:

| Topic | Purpose |
|---|---|
| `shopnova.order-events` | Order lifecycle events |
| `shopnova.inventory-events` | Inventory updates |
| `shopnova.product-events` | Product changes |
| `shopnova.notification-events` | Notification events |
| `shopnova.dead-letter-events` | Failed event handling |

The architecture includes:

- Transactional outbox pattern.
- Asynchronous event publishing.
- Inventory processing.
- Idempotent event handling.
- Order confirmation and rejection events.
- Dead-letter handling for failed processing.

Actual end-to-end event processing depends on successful configuration and operation of the connected Kafka infrastructure and workers.

## 9. Product Search

SHOPNOVA integrates OpenSearch for product search capabilities.

The search architecture supports:

- Product indexing.
- Search index updates through background processing.
- Product document synchronization.
- Search queries and filtering.
- Fuzzy matching for typo-tolerant searches.

For example, a search for `bluetoth` can be configured to match products containing `Bluetooth`.

## 10. Database Migrations

The project uses Alembic for database schema migrations.

Run migrations from the backend directory:

```bash
python -m alembic upgrade head
```

## 11. Testing

### Backend Tests

From the backend directory:

```bash
python -m pytest tests/unit tests/security
```

The repository includes backend unit, security, and integration test suites.

### Frontend Tests

From the frontend directory:

```bash
npm test
```

### Production Build

```bash
npm run build
```

The production build is generated in the frontend `dist/` directory.

## 12. Security

Security measures implemented in the project include:

- Argon2 password hashing.
- JWT-based authentication.
- Backend authorization checks.
- Login rate limiting.
- Environment-based configuration.
- Sensitive-file exclusion through `.gitignore`.
- Database TLS configuration.
- Secret-scanning utility.

Run the secret scanner from the project root using an available Python environment:

```bash
python scripts/secret_scan.py
```

## 13. Infrastructure and Integration Status

SHOPNOVA is configured to use the following Aiven services:

| Service | Integration |
|---|---|
| Aiven PostgreSQL | Connection verified |
| Aiven Kafka | Producer startup tested; health-check discrepancy remains under investigation |
| Aiven OpenSearch | Application client connection verified |

The health endpoint reports the reachability of configured services. At the time of this documentation, the Kafka health probe reports an issue even though standalone application producer startup was successful.

Full end-to-end validation of order events, inventory consumers, and search indexing remains subject to further integration testing.

## 14. Documentation

Additional project documentation is available in the `docs/` directory:

- `architecture.md` — System architecture.
- `aiven-setup.md` — Aiven service configuration.
- `IMPLEMENTATION_PLAN.md` — Implementation details and acceptance criteria.
- `PROJECT_AUDIT.md` — Project audit and known limitations.
- `COMPLETION_REPORT.md` — Project completion report.

**SHOPNOVA — Building a modern, scalable, and event-driven e-commerce experience.**
