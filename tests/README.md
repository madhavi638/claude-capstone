# HMS-6 Test Suite

## Unit tests (no dependencies)

```
pytest tests/unit
```

Covers the status transition table (`domain/appointment_state_machine.py`) — every legal and
illegal transition pair, including all three terminal states — and the auth principal stub.

## Integration tests (require Postgres)

Start the database first:

```
docker compose -f database/docker-compose.yml up -d
```

Set the `HMS6_DB_*` environment variables to match (see `configs/.env.example`; the defaults
already match `database/docker-compose.yml`'s defaults), then:

```
pytest tests/integration
```

Each test runs inside a transaction that is rolled back on teardown, so the suite never leaves
data behind in the container even though the service/repository layers call `session.commit()`
internally.

Covers: slot-exclusion conflict detection, cancelled-slot rebooking, append-only status history,
authorization scoping by role, the state-machine integration in the service layer, notification
outbox durability (same-transaction write, retry/backoff, never-deleted-on-failure), and the
FastAPI router's status codes and pagination bounds.

## Full suite

```
pytest
```
