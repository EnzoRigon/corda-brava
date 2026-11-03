### Task 5: Host session & auth (login, token, require_host)

**Files:**
- Create: `backend/app/services/host_session.py`, `backend/app/api/auth.py` (deps), `backend/app/schemas/host.py`
- Test: `backend/tests/services/test_host_session.py`

**Interfaces:**
- Produces: `issue_host_token(settings) -> (token, expires_at)` (PyJWT, `role=host`, exp from `HOST_TOKEN_TTL_SECONDS`, signed `SECRET_KEY`); `verify_host_token(token, settings) -> bool`; `check_password(candidate, settings) -> bool` via `secrets.compare_digest`; FastAPI deps `require_host` (Bearer → 401) and `verify_ws_token(token)`.

- [ ] **Step 1:** Write tests: right password → valid token that verifies; wrong password → false; tampered/expired token → verify false; `require_host` dependency rejects missing/bad Bearer.
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat(auth): host login, JWT token, require_host + tests`.

---

## PHASE B — Backend services, consumer loop, API & WS

