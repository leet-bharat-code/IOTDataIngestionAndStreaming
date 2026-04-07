# IoT Data Ingestion & Streaming Service

A production-grade FastAPI service for real-time IoT data ingestion, storage, and streaming. Built with **Clean Architecture** principles, async MongoDB (Motor), JWT authentication, WebSocket push, and an event-driven messaging abstraction.

---

## Table of Contents

- [Architecture](#architecture)
- [Data Flow](#data-flow)
- [Design Decisions](#design-decisions)
- [Setup](#setup)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [WebSocket Endpoints](#websocket-endpoints)
- [Error Format](#error-format)
- [Testing](#testing)
- [Scaling Considerations](#scaling-considerations)

---

## Architecture

```
app/
├── api/              # FastAPI route handlers (thin — no business logic)
│   ├── auth.py
│   ├── users.py
│   ├── iot.py
│   └── websockets.py
├── services/         # Business logic orchestration
│   ├── auth_service.py
│   ├── user_service.py
│   └── iot_service.py
├── domain/           # Pure validation rules (no I/O, no framework deps)
│   └── validators.py
├── repository/       # MongoDB access via Motor (async)
│   ├── database.py
│   ├── user_repository.py
│   └── iot_repository.py
├── messaging/        # Event publishing abstraction
│   └── event_bus.py
├── websocket/        # Connection manager + event-to-WS bridge
│   ├── manager.py
│   └── broadcaster.py
├── core/             # Config, auth, logging, DI, exception hierarchy
│   ├── config.py
│   ├── security.py
│   ├── dependencies.py
│   ├── exceptions.py
│   └── logging.py
├── schemas/          # Pydantic request/response models
│   ├── auth.py
│   ├── user.py
│   ├── iot.py
│   ├── events.py
│   └── common.py
└── main.py           # Application entrypoint & lifespan
```

Each layer has a single responsibility and depends only on layers below it:

- **api/** never contains business logic -- it maps HTTP/WS to service calls.
- **services/** orchestrates domain validation, repository access, and event publishing.
- **domain/** is pure Python functions with zero I/O -- trivially unit-testable.
- **repository/** is the only layer that knows about MongoDB.
- **messaging/** is the seam between the service layer and any delivery mechanism.
- **websocket/** is infrastructure -- only the event bus calls into it.

---

## Data Flow

### REST Ingestion (POST /iot/data)

```
Client ──► api/iot.py ──► iot_service.process_iot_data()
              │
              ├─► domain/validators.py       (validate metrics + timestamp)
              ├─► repository/user_repository  (check user exists & active)
              ├─► repository/iot_repository   (persist with unique-index idempotency)
              └─► messaging/event_bus         (publish_event → broadcaster → WS clients)
```

### WebSocket Ingestion (/ws/ingest)

```
Client ──► api/websockets.py ──► iot_service.process_iot_data()
              │
              └─► (exact same pipeline as REST)
```

Both REST and WebSocket call the **exact same** `process_iot_data()` function.

### Real-time Subscription (/ws/subscribe)

```
Client ──► /ws/subscribe?user_id=U1001 ──► connection added to ConnectionManager
              ◄── NEW_DATA events pushed whenever data arrives for U1001
```

### Messaging Decoupling

```
Service Layer ──► publish_event() ──► event_bus ──► [subscribers...]
                                                          │
                                         broadcaster ──► ConnectionManager ──► WS clients
```

The service layer **never** imports or calls WebSocket code. The event bus is the architectural seam.

---

## Design Decisions

| Decision | Rationale |
|---|---|
| **Single ingestion pipeline** | REST and WS share `process_iot_data()` -- zero duplication, identical validation |
| **Event bus abstraction** | Service publishes events without knowing about WebSockets. Swap to Redis pub/sub later without touching business logic |
| **Idempotency via unique compound index** | `(user_id, timestamp)` unique index in MongoDB -- the DB enforces deduplication at write time with zero application-level locking |
| **Domain validators are pure functions** | No I/O, no framework imports -- trivially testable, deterministic |
| **Pydantic v2 at the boundary** | Schema validation at the API edge; domain validators enforce business rules separately |
| **Motor (async MongoDB driver)** | Non-blocking I/O end-to-end -- no thread pool needed |
| **`dict[user_id, set[ws]]` connection manager** | O(1) fan-out lookup; stale connections auto-pruned on send failure |
| **JWT validated at WS connect** | Unauthorized clients rejected before entering the message loop |
| **Structured error codes** | Every error response carries a machine-readable `error` code plus a human `message` |

---

## Setup

### Prerequisites

- Python 3.12+
- MongoDB 6+ (or use Docker)

### Docker (Recommended)

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`. Health check: `GET /health`.

### Local Development

```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run
uvicorn app.main:app --reload
```

---

## Configuration

All settings are loaded from environment variables (or `.env` file):

| Variable | Default | Description |
|---|---|---|
| `MONGODB_URL` | `mongodb+srv://kaushikbharat3990:HrPWmgq9PXXAccqC@cluster0.umexzhi.mongodb.net/?appName=Cluster0` | MongoDB connection string |
| `MONGODB_DB_NAME` | `iot_platform` | Database name |
| `agHfbiV0yPa4v2dOVf4fnUjAbvwez8zMUZU2jIcSYWDQcTJc5A3dT4JEKjmXTu4YRXU86Jy48uhQsTUvaYv6Ry91NDrpi6fb` | `change-me` | HMAC secret for JWT signing -- **must override in production** |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_EXPIRATION_MINUTES` | `60` | Token TTL in minutes |
| `LOG_LEVEL` | `INFO` | Python logging level |

---

## API Reference

### Health Check

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

### Authentication

**POST /auth/login**

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id": "U1001", "password": "mypassword"}'
```

Response:
```json
{"access_token": "eyJ...", "token_type": "bearer"}
```

### User Management

**POST /users** (create -- no auth required)

```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"user_id": "U1001", "name": "Alice", "password": "secret123"}'
```

**GET /users/{user_id}** (requires auth)

```bash
curl http://localhost:8000/users/U1001 \
  -H "Authorization: Bearer <token>"
```

**PUT /users/{user_id}** (requires auth)

```bash
curl -X PUT http://localhost:8000/users/U1001 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Updated"}'
```

### IoT Data Ingestion (REST)

**POST /iot/data** (requires auth)

```bash
curl -X POST http://localhost:8000/iot/data \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "U1001",
    "metric_1": 42.5,
    "metric_2": 120.3,
    "metric_3": 7.8,
    "timestamp": 1712500000
  }'
```

Validation rules:
- `metric_1`: 0--100
- `metric_2`: 0--200
- `timestamp`: must not be in the future (5s drift tolerance)
- `user_id`: must reference an existing, active user

### Fetch Data

**GET /users/{user_id}/iot/latest** (requires auth)

```bash
curl http://localhost:8000/users/U1001/iot/latest \
  -H "Authorization: Bearer <token>"
```

**GET /users/{user_id}/iot/history?limit=50** (requires auth)

```bash
curl "http://localhost:8000/users/U1001/iot/history?limit=20" \
  -H "Authorization: Bearer <token>"
```

---

## WebSocket Endpoints

All WebSocket connections require a `token` query parameter with a valid JWT.

### /ws/ingest -- Data Producers

```python
import asyncio, json, websockets

async def produce():
    uri = "ws://localhost:8000/ws/ingest?token=<jwt>"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            "user_id": "U1001",
            "metric_1": 55.0,
            "metric_2": 110.0,
            "metric_3": 9.2,
            "timestamp": 1712500100
        }))
        print(await ws.recv())

asyncio.run(produce())
```

### /ws/subscribe -- Data Consumers

```python
import asyncio, websockets

async def subscribe():
    uri = "ws://localhost:8000/ws/subscribe?user_id=U1001&token=<jwt>"
    async with websockets.connect(uri) as ws:
        while True:
            msg = await ws.recv()
            print("Received:", msg)

asyncio.run(subscribe())
```

Event format pushed to subscribers:

```json
{
  "event": "NEW_DATA",
  "user_id": "U1001",
  "timestamp": 1712500100,
  "data": {
    "metric_1": 55.0,
    "metric_2": 110.0,
    "metric_3": 9.2
  }
}
```

---

## Error Format

Every error response uses a consistent envelope:

```json
{
  "error": "VALIDATION_ERROR",
  "message": "IoT data validation failed",
  "details": [
    "metric_1 must be between 0.0 and 100.0, got 150.0"
  ]
}
```

| HTTP Status | Error Code | When |
|---|---|---|
| 401 | `AUTHENTICATION_ERROR` | Invalid/missing JWT, wrong password, inactive account |
| 403 | `AUTHORIZATION_ERROR` | Insufficient permissions |
| 404 | `NOT_FOUND` | User or IoT data not found |
| 409 | `DUPLICATE` | Duplicate `(user_id, timestamp)` data point |
| 422 | `VALIDATION_ERROR` | Metric range violations, future timestamp, inactive user |

---

## Testing

```bash
pip install -r requirements.txt
pytest -v
```

Tests use `mongomock-motor` -- no running MongoDB instance required.

Test coverage:

- **Security** -- password hashing round-trip, JWT encode/decode, tampered token rejection
- **Domain validators** -- boundary values, drift tolerance, composite error collection
- **Auth service** -- login success, wrong password, nonexistent user, inactive user
- **User service** -- create, read, update, duplicate detection
- **IoT service** -- ingestion, event publishing, idempotency, inactive user rejection, future timestamp, latest/history queries

---

## Scaling Considerations

This design is built to scale horizontally. The key architectural seam is the **event bus**.

### Current State (In-Process)

The event bus fans out events within a single process. This is correct for single-instance deployments.

### Production Scale (Redis Pub/Sub)

Replace `messaging/event_bus.py` with a Redis-backed implementation:

```
Service ──► publish_event() ──► Redis PUBLISH
                                     │
       Instance A subscriber ──► broadcast to local WS clients
       Instance B subscriber ──► broadcast to local WS clients
```

Changes required:

1. Swap `event_bus.py` for a Redis pub/sub adapter (same `publish_event` / `subscribe` interface)
2. **No changes** to services, domain, repository, or API layers

### Further Scaling

| Concern | Solution |
|---|---|
| **Write throughput** | Batch inserts, MongoDB sharding on `user_id` |
| **WS connection count** | Multiple API instances behind a load balancer with sticky sessions, or Redis pub/sub for cross-instance fan-out |
| **Data retention** | TTL indexes on `iot_data`, archival to cold storage |
| **Backpressure** | Message queue (Kafka / RabbitMQ) between ingestion API and the processing pipeline |
| **Observability** | Structured JSON logging, OpenTelemetry traces, Prometheus metrics |

---

## License

MIT
