# Task 5 Report — Host session & auth

**Status:** DONE  |  **Commit:** 8e75e62

## Files
- backend/app/services/host_session.py (+ __init__.py)
- backend/app/api/auth.py
- backend/app/schemas/host.py (+ __init__.py)
- backend/tests/services/test_host_session.py (+ __init__.py), 7 tests

## Public signatures
```python
check_password(candidate: str, settings: Settings) -> bool
issue_host_token(settings: Settings) -> tuple[str, datetime]
verify_host_token(token: str, settings: Settings) -> bool   # never raises
verify_ws_token(token: str | None, settings: Settings) -> bool
require_host(settings=Depends(get_settings), authorization: Header) -> None  # 401 + WWW-Authenticate
class HostLoginRequest(BaseModel): password: str
class HostLoginResponse(BaseModel): token: str; expiresAt: datetime
```

## Settings used
HOST_PASSWORD, HOST_TOKEN_TTL_SECONDS, SECRET_KEY (all pre-existing; none added).

## Results
pytest: 78 passed (71 + 7). ruff clean, black clean.

## Deviations / assumptions
- Login route not added (Task 10).
- Schema field is `expiresAt` (camelCase) directly, with noqa N815, instead of alias config.
- Expiry tested via negative TTL rather than time mocking.
