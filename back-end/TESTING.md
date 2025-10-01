# Backend Testing Documentation

## Testing Philosophy

Our testing approach ensures that if all tests pass, the Django server is production-ready. Tests focus on the **API surface exposed to the front-end application**, not the internals of third-party libraries.

## Test Setup

### Dependencies

Testing uses **pytest** with Django integration:

```bash
pip install -r requirements.txt
```

Key testing packages:
- `pytest` - Test framework
- `pytest-django` - Django integration
- `pytest-cov` - Coverage reporting
- `pytest-xdist` - Parallel test execution
- `factory-boy` - Test data factories
- `faker` - Generate realistic test data

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov

# Run specific test file
pytest api/test_spa_auth.py

# Run tests matching a pattern
pytest -k "test_authorization"

# Run tests in parallel (faster)
pytest -n auto

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only OAuth tests
pytest -m oauth
```

### Test Configuration

Configuration is in `pytest.ini`:
- **Test discovery**: Finds `tests.py`, `test_*.py`, `*_tests.py`
- **Coverage threshold**: 80% minimum
- **Test markers**: `unit`, `integration`, `oauth`, `slow`

## SPA Authentication Flow

The React front-end uses OAuth2 **Implicit Grant Flow**:

### 1. Authorization Request

```
User clicks "Login" in SPA
  ↓
SPA redirects to: /api/o/authorize/?
  - response_type=token
  - client_id=spa-client-id-12345
  - redirect_uri=http://localhost:5173/auth/callback
  - scope=read write
```

### 2. User Authentication & Authorization

```
User logs in via Django admin
  ↓
User sees authorization prompt
  ↓
User clicks "Authorize"
```

### 3. Token Response

```
OAuth2 redirects to callback:
  http://localhost:5173/auth/callback#
    access_token=abc123xyz...
    &token_type=Bearer
    &expires_in=36000
    &scope=read+write
```

### 4. Authenticated API Requests

```javascript
// SPA extracts token from URL fragment
const token = extractTokenFromFragment();

// Makes authenticated requests
fetch('http://localhost:8000/api/users/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

## Test Structure

### `api/test_spa_auth.py`

Comprehensive tests for the SPA authentication flow, organized into test classes:

- **TestSPAAuthorizationFlow** - OAuth2 authorization endpoint and user approval flow
- **TestSPAAuthenticatedRequests** - API requests using OAuth2 tokens
- **TestSPATokenLifecycle** - Token creation, expiration, and reuse
- **TestSPAEndpointSecurity** - Security enforcement and scope validation

### `api/tests.py`

Basic sanity tests for public endpoints.

## OAuth2 Scopes

| Scope | Description | Required For |
|-------|-------------|--------------|
| `read` | Read user data | GET /api/users/ |
| `write` | Create/update users | POST /api/users/ |
| `groups` | Access groups | GET /api/groups/ |

## Creating New Tests

### Example: Testing a New Endpoint

```python
import pytest
from rest_framework import status

@pytest.mark.django_db
@pytest.mark.integration
def test_new_endpoint(authenticated_client):
    """Test description."""
    response = authenticated_client.get('/api/new-endpoint/')

    assert response.status_code == status.HTTP_200_OK
    assert 'expected_field' in response.data
```

### Using Fixtures

Common fixtures in `conftest.py`:
- `api_client` - Unauthenticated API client
- `test_user` - Regular user
- `test_superuser` - Admin user
- `authenticated_client` - Client with valid OAuth2 token
- `authenticated_client_with_groups` - Client with groups scope
- `spa_oauth_application` - OAuth app configured for SPA

## Production Readiness Checklist

Before deploying to production, ensure:

- [ ] All tests passing: `pytest`
- [ ] Coverage meets threshold: `pytest --cov --cov-fail-under=80`
- [ ] `DEBUG = False` in settings.py
- [ ] `SECRET_KEY` is properly secured (environment variable)
- [ ] `ALLOWED_HOSTS` is restricted to actual domains
- [ ] `CORS_ALLOW_ALL_ORIGINS = False` and whitelist specific origins
- [ ] HTTPS enforced for OAuth2 redirects
- [ ] Database credentials secured

## Troubleshooting

### Tests Fail with Database Errors

Ensure PostgreSQL is running:
```bash
docker compose -f ../compose.yml up -d
```

### Import Errors

Activate virtual environment:
```bash
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```
