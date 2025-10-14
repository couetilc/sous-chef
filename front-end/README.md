# Frontend Testing

## Unit Tests

Unit tests mock the backend and test core logic in isolation.

```bash
docker compose run frontend pnpm test
```

**Coverage:** 11 tests covering CSRF token initialization, retry logic, and concurrent request handling.

## Integration Tests

Integration tests run against a real Django backend.

```bash
# Start backend first
docker compose up -d backend db

# Run integration tests
docker compose run frontend pnpm test:integration
```

**Coverage:** 9 tests validating user registration, login, and error handling against the real backend.

## Run All Tests

```bash
docker compose up -d backend db
docker compose run frontend pnpm test -- --run
```
