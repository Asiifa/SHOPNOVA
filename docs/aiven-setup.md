# Aiven setup (private configuration)

Do **not** paste passwords, tokens or certificates into chat.

Service identifiers already allocated:

| Service | Identifier | Role |
|---|---|---|
| PostgreSQL | `pg-39f21b1d` | System of record |
| Apache Kafka (Inkless) | `kafka-12572b23` | Domain events |
| OpenSearch | `os-114c34a2` | Product search |

## 1. Download the CA certificate

In the Aiven console, download the CA for each service (they may share a project CA).

Save it locally as:

```
backend/certs/aiven-ca.pem
```

That path is gitignored.

## 2. Create `backend/.env` from the example

```powershell
cd backend
copy .env.example .env
```

Fill values **only** from the Aiven service overview / connection info panels:

- PostgreSQL: host, port, database, user, password
- Kafka: bootstrap host:port, SASL username, SASL password, mechanism
- OpenSearch: HTTPS URL, user, password

Set:

```
POSTGRES_SSLMODE=verify-full
KAFKA_SECURITY_PROTOCOL=SASL_SSL
OPENSEARCH_VERIFY_CERTS=true
```

## 3. Kafka topics

On Inkless services, prefer **classic** topics if you need compaction later; this app does not require compaction.

Create (console → Topics), typically 3 partitions, replication as the Free plan allows (often 2 or 3; diskless may require RF=1):

- `shopnova.order-events`
- `shopnova.inventory-events`
- `shopnova.product-events`
- `shopnova.notification-events`
- `shopnova.dead-letter-events`

Grant the application user **readwrite** on `shopnova.*` (Aiven ACL wildcard).

Do not enable Kafka transactions for these topics.

## 4. OpenSearch index

The API creates `shopnova-products` on startup if it is missing. You can also run:

```powershell
python -m scripts.ensure_opensearch_index
```

## 5. Verify without printing secrets

```powershell
cd backend
python -m scripts.verify_services
```

Expected: three `ok` statuses. Connection strings are never logged.

## 6. Migrations and seed

```powershell
alembic upgrade head
python -m scripts.seed_catalog
python -m scripts.provision_admin
```

`provision_admin` reads `ADMIN_BOOTSTRAP_EMAIL` and `ADMIN_BOOTSTRAP_PASSWORD` from `.env` and does not echo them.

## When you are ready

Reply in this project that **private `.env` and CA files are in place**. Do not send the values. Integration tests against live Aiven can then be run.
