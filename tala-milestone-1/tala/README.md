# TALA — Cybersecurity Lab Journal

> Document. Analyze. Learn.

A personal cybersecurity lab journal for documenting TryHackMe/HTB labs, CTF
challenges, home labs, and security investigations — with structured
write-ups, evidence handling, skill/tool/MITRE ATT&CK tracking, and a
sanitized public portfolio view.

**This is a documentation and learning platform. It does not perform
attacks, scans, exploitation, or automated CTF solving.**

This README currently covers **Milestone 1 (project setup, database,
authentication)** only. It will be expanded into the full project README
(features, architecture, security considerations, screenshots, etc.) as
later milestones are completed.

---

## Milestone 1 status: Project setup + database + authentication

### What's implemented
- Docker Compose stack: PostgreSQL, FastAPI backend, React frontend
- Alembic migration for `users` and `audit_logs` tables
- Registration, login, logout, `/auth/me` — JWT delivered via HttpOnly cookie
- Single-user enforcement (registration closes after the first account)
- Password hashing (bcrypt), rate limiting on auth endpoints, audit logging
  of register/login events, generic error messages (no account enumeration)
- Global exception handler that never leaks internals to the client
- Frontend: login/register pages, auth context, protected routing, and the
  full sidebar navigation (other sections show a "coming in Milestone N"
  placeholder until built)
- Backend test suite covering the auth flows

### Running it

1. Copy the environment template and fill in real secrets:
   ```bash
   cp .env.example .env
   ```
   At minimum, change `POSTGRES_PASSWORD` and generate a real
   `JWT_SECRET_KEY`:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. Start everything:
   ```bash
   docker compose up --build
   ```

3. Apply the database migration (first run only):
   ```bash
   docker compose exec backend alembic upgrade head
   ```

4. Open the app:
   - Frontend: http://localhost:5173
   - API docs (Swagger UI): http://localhost:8000/docs

5. Register your one account at `/register`, then sign in.

### Running tests

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -v
```

The test suite uses an in-memory SQLite database, so it runs without a
live Postgres connection.

### What remains
Everything past authentication: lab management, evidence, skills/tools,
MITRE ATT&CK, CTF tracker, dashboard analytics, learning roadmap, portfolio
mode, reports/export, and the final security-hardening pass. See the
milestone plan for the full roadmap.
