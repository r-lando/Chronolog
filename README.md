# TALA — Cybersecurity Lab Journal

> Document. Analyze. Learn.

TALA is a personal cybersecurity lab journal: a place to document TryHackMe/HTB labs, CTF challenges, home-lab experiments, and investigations, turn them into structured technical write-ups, track the skills/tools/MITRE ATT&CK techniques you've actually practiced, and showcase selected work on a public portfolio page.

**TALA does not perform attacks, exploits, scans, or automated CTF solving.** It is a documentation, evidence-handling, and learning-tracking platform — the write-ups and solutions inside it come entirely from work the user already did elsewhere, on systems they were authorized to test.

This is a portfolio project built by a BSCS student for cybersecurity/SOC analyst job applications. It's intentionally scoped like a real, shippable product rather than a toy: real authentication, real file-upload security, a real database schema with proper foreign keys, and a real automated test suite (180+ tests) — not a feature list with no substance behind it.

---

## Table of contents

- [Problem being solved](#problem-being-solved)
- [Features](#features)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Database design](#database-design)
- [Installation](#installation)
- [Environment variables](#environment-variables)
- [Docker setup](#docker-setup)
- [Sample data](#sample-data)
- [Security considerations](#security-considerations)
- [Testing](#testing)
- [Example lab workflow](#example-lab-workflow)
- [Limitations](#limitations)
- [Future improvements](#future-improvements)
- [Skills demonstrated](#skills-demonstrated)

---

## Problem being solved

Cybersecurity students accumulate a lot of hands-on experience — TryHackMe rooms, HTB machines, CTF challenges, home-lab experiments — but that experience usually lives nowhere coherent. Platform progress bars don't capture *what you actually learned*, scattered notes don't show growth over time, and "trust me, I've done a lot of labs" isn't evidence in a job interview.

TALA gives that experience a structured home: every lab becomes a real technical write-up (objective, methodology, findings, analysis, lessons learned), tagged with the skills, tools, and MITRE ATT&CK techniques genuinely practiced, backed by actual evidence (screenshots, logs, PCAPs) with integrity hashes, and summarized into dashboards and reports that show real, measurable activity — never a self-rated "90% proficient" with nothing behind it.

## Features

- **Lab management** — full CRUD with category/difficulty/status, structured write-up editor (Objective, Environment, Methodology, Findings, Analysis, Lessons Learned, Reflection, Next Steps), tags.
- **Evidence management** — secure file upload (screenshots, logs, PCAPs, configs, reports) with extension whitelisting, magic-byte verification, UTF-8 validation for text, SHA-256 hashing, and safe server-generated filenames.
- **Skills & Tools tracking** — shared master lists with real, computed statistics (labs practiced, last practiced, related items) — never a self-reported percentage.
- **MITRE ATT&CK integration** — map labs/CTF challenges to a curated set of real ATT&CK techniques, with a *required, minimum-length justification* so mappings can't be fabricated or rubber-stamped.
- **CTF tracker** — events and challenges across Web/Pwn/Crypto/Forensics/OSINT/Reverse Engineering/Misc/Cloud/Mobile, with Solved/Partially Solved/Unsolved tracking and the same evidence/skills/tools/techniques model as labs.
- **Dashboard & analytics** — labs completed, learning hours, current streak, skills/tools/techniques practiced, labs-by-category, difficulty distribution, activity timeline, MITRE coverage by tactic — all computed live from stored data.
- **Learning Roadmap** — a self-referencing goal tree (e.g. "SOC Analyst" → Networking, SIEM, Incident Response, ...), with progress and a simple recommended-next-activity derived from real lab data for any goal linked to a skill.
- **Portfolio mode** — mark a lab portfolio-ready and it appears on a public, unauthenticated page at a random, non-enumerable URL. Evidence stays private by default even when a lab is published; the write-up's private Reflection field is never shown publicly.
- **Global search** — one search box across labs, CTF challenges, findings, tags, skills, tools, and MITRE techniques.
- **Reports & export** — a full Lab Report or an account-wide Learning Summary, each as PDF or Markdown, generated from the same data the dashboard shows.

## Architecture

A deliberately simple three-tier design — a single-user learning journal doesn't need microservices, message queues, or a service mesh, and demonstrating that you know *not* to over-engineer something is itself a signal worth sending in a portfolio project.

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT (Browser)                           │
│  React + TypeScript SPA — Tailwind, Recharts, React Router,    │
│  TanStack Query                                                 │
└───────────────────────────┬────────────────────────────────┘
                             │ HTTPS / REST (JSON)
                             │ JWT in an HttpOnly, SameSite=Lax cookie
┌───────────────────────────▼────────────────────────────────┐
│                   API LAYER — FastAPI                          │
│  Routers → Services → SQLAlchemy ORM models                    │
│  Pydantic schemas validate every request/response               │
│  slowapi rate limiting · audit logging · security headers       │
└───────────┬───────────────────────────────┬─────────────────┘
            │                               │
┌───────────▼───────────┐       ┌───────────▼─────────────────┐
│     PostgreSQL          │       │   Evidence storage            │
│  (all structured data:  │       │   /app/storage/evidence        │
│   labs, users, skills,  │       │   Non-web-servable; files are  │
│   MITRE, evidence meta) │       │   only ever read/written via   │
│                         │       │   authenticated/validated code │
└─────────────────────────┘       └───────────────────────────┘
```

**Why these specific choices:**
- **Evidence files live on disk, not in the database.** Only metadata (hash, size, MIME type, server-generated filename) is stored in Postgres. Files are served exclusively through authenticated API endpoints that re-check ownership on every request — never through a static file mount.
- **JWT in an HttpOnly cookie, not localStorage.** JavaScript can never read the token, which closes off an entire class of XSS-driven token theft. Combined with `SameSite=Lax`, this also gives meaningful built-in CSRF protection for state-changing requests (see [Security considerations](#security-considerations)).
- **One well-normalized schema, radiated outward.** Skills, Tools, and MITRE techniques are shared master lists referenced by both labs and CTF challenges — the same "Wireshark" row is reused everywhere it's attached, which is what makes aggregate statistics (dashboard, Skills page) possible without a separately-maintained stats table that could drift out of sync.

## Tech stack

**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, React Router, Recharts, react-markdown.

**Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 (ORM), Pydantic v2, Alembic (migrations), slowapi (rate limiting), passlib/bcrypt (password hashing), python-jose (JWT), WeasyPrint + Jinja2 (PDF/Markdown report generation).

**Database:** PostgreSQL 16.

**Infrastructure:** Docker Compose (three services: `db`, `backend`, `frontend`). No Kubernetes, no message queue, no cache layer — deliberately, for a single-user application at this scale.

## Database design

18 tables, all with real foreign keys, indexes on every foreign key and frequently-filtered column, and junction tables (not arrays-of-IDs or JSON blobs) for every many-to-many relationship.

```
users 1───* labs 1───1 lab_writeups
              │
              ├──* findings 1───* evidence
              ├──* evidence (lab-level, finding_id null)
              ├──* lab_skills *───1 skills
              ├──* lab_tools  *───1 tools
              ├──* lab_techniques *───1 mitre_techniques   (association object — carries a required justification)
              └──* lab_tags   *───1 tags

users 1───* ctf_events 1───* ctf_challenges
                                  ├──* ctf_challenge_skills *───1 skills
                                  ├──* ctf_challenge_tools  *───1 tools
                                  ├──* ctf_challenge_techniques *───1 mitre_techniques
                                  └──* ctf_evidence

users 1───* learning_goals (self-referencing tree via parent_goal_id, optional FK to skills)
users 1───* audit_logs
```

**Notable design decisions:**
- `lab_techniques` and `ctf_challenge_techniques` are **association objects**, not plain many-to-many tables — the mapping itself carries a required `justification` column, which is the schema-level half of the anti-fabrication guardrail (the other half is API-level: a minimum length check, and rejecting any technique not in the seeded reference list).
- Category/difficulty/status are validated in the Pydantic schema layer against a shared Python list (`app/constants.py`), not a Postgres `ENUM` type — adding a new category is a one-line code change plus a data migration, not a schema migration that locks the column type.
- `is_portfolio_ready` and `portfolio_slug` live on `labs` from the start (Milestone 2's schema), and `is_public` lives on `evidence` from Milestone 3 — both default to private/false, so later turning on the portfolio feature never silently exposed anything that existed before it.

Full schema: see `backend/alembic/versions/` for the complete, incremental migration history (one file per milestone).

## Installation

### Prerequisites
- Docker and Docker Compose
- (For local, non-Docker development) Python 3.12+ and Node 20+

### Quick start

```bash
git clone <your-repo-url>
cd tala
cp .env.example .env
```

Edit `.env` and set at minimum:
- `POSTGRES_PASSWORD` — any strong password
- `JWT_SECRET_KEY` — generate one with:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

```bash
docker compose up --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed.seed_data   # optional, see "Sample data" below
```

- Frontend: http://localhost:5173
- API docs (Swagger UI, development only): http://localhost:8000/docs

Register your one account at `/register`, then sign in. TALA is configured for a single user — once one account exists, registration closes (see [Limitations](#limitations)).

## Environment variables

All configuration is via environment variables (see `.env.example`); nothing is hardcoded in source.

| Variable | Purpose | Default |
|---|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Database credentials | — (must be set) |
| `DATABASE_URL` | Full SQLAlchemy connection string | built from the above in `docker-compose.yml` |
| `JWT_SECRET_KEY` | Signs/verifies session JWTs | — (must be set to a strong random value) |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Session length | `60` |
| `ENVIRONMENT` | `development` or `production` — gates API docs exposure | `development` |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins | `http://localhost:5173` |
| `COOKIE_SECURE` | Require HTTPS for the auth cookie; also gates the HSTS header | `false` |
| `ALLOW_SINGLE_USER_ONLY` | Closes `/auth/register` after the first account | `true` |
| `EVIDENCE_STORAGE_PATH` | Where uploaded evidence files are written | `/app/storage/evidence` |
| `MAX_UPLOAD_SIZE_MB` | Per-file upload size limit | `25` |
| `RATE_LIMIT_LOGIN` | Login/register rate limit | `5/minute` |
| `RATE_LIMIT_UPLOAD` | Evidence upload rate limit | `20/minute` |
| `RATE_LIMIT_PUBLIC` | Public portfolio endpoint rate limit | `60/minute` |

## Docker setup

Three services, defined in `docker-compose.yml`:

- **`db`** — PostgreSQL 16, with a health check so `backend` waits for it to be ready.
- **`backend`** — FastAPI + Uvicorn (with `--reload` for development), built from `backend/Dockerfile`, which also installs WeasyPrint's native dependencies (Pango, Cairo) needed for PDF generation.
- **`frontend`** — Vite dev server, built from `frontend/Dockerfile`.

Evidence files persist in a named Docker volume (`tala_evidence`), separate from the Postgres data volume (`tala_pgdata`), so you can reset the database without losing uploaded files (or vice versa).

## Sample data

Running the seed script populates:
- **16 skills** and **10 tools** (shared reference lists, used immediately)
- **18 MITRE ATT&CK techniques** — a curated, representative subset of the real framework (not all 600+ techniques), spanning most tactics
- **10 sample labs** matching the categories/difficulties/statuses in the spec, each with a full write-up, attached skills/tools, one MITRE mapping where applicable, and structured findings — including one `Planned` and one `In Progress` lab, so the dashboard's "not yet practiced" exclusion rule has real data to demonstrate
- **1 CTF event** ("PicoCTF 2026") with **5 challenges** across Crypto/Web/Forensics/Pwn/OSINT, covering all three statuses (Solved/Partially Solved/Unsolved)
- **The exact learning roadmap tree from the product spec** (SOC Analyst → Networking, Linux, Windows Event Logs, SIEM, Detection Engineering, Threat Hunting, Incident Response), with the skill-linked sub-goals wired to real skills

```bash
docker compose exec backend python -m app.seed.seed_data
```

The script is fully idempotent — safe to run multiple times, and it will only seed sample labs/CTF/roadmap once a user account exists (it looks up the first registered user). Every sample value is also re-validated in the test suite against the exact same Pydantic schemas the real API enforces (`tests/test_sample_data.py`), so the sample data can't silently drift out of sync with what the app actually allows.

No sample evidence files are seeded — uploading a real screenshot or log is quick to do manually and demonstrates the actual upload-validation pipeline, which a seeded placeholder file wouldn't.

## Security considerations

Treating TALA itself as a security-relevant project, not just a CRUD app:

- **Password hashing**: bcrypt via passlib, with a minimum 10-character, letter+digit password policy (favoring length over mandatory special characters, which does more real work against brute force).
- **Authentication**: JWT in an HttpOnly, SameSite=Lax cookie — never exposed to JavaScript, and never sent on cross-site state-changing requests (SameSite=Lax cookies aren't attached to cross-site POST/PUT/DELETE, which is meaningful built-in CSRF protection for this app's cookie-based auth).
- **Authorization**: every resource lookup by ID is scoped to the requesting user's ownership, enforced via explicit joins (never a global "is admin" bypass). A request for another user's lab, evidence, CTF event, or learning goal returns **404, not 403** — this avoids confirming to an unauthorized caller that the resource even exists.
- **File upload security** (the single most security-sensitive code path in the app, in `app/services/evidence_service.py`): a **whitelist-only** extension policy (not a blocklist), **magic-byte verification** for binary types so a renamed script can't masquerade as an image, **UTF-8 validation** for text types, size limits enforced during the actual read (not trusted from the `Content-Length` header), and **server-generated filenames** — the original filename is kept only for display and is never used to construct a filesystem path, which is what makes path traversal structurally impossible rather than merely filtered.
- **Evidence downloads** always set `Content-Disposition: attachment`, never `inline` — so an uploaded `.log` file that happens to contain HTML/script can never render in the browser.
- **Public portfolio sanitization**: a single audited function (`build_public_lab_view` in `app/services/portfolio_service.py`) is the only place public lab data is assembled. It never includes the write-up's Reflection field, never includes evidence not individually marked public, and never includes an evidence item's private `notes` field even when the evidence itself is public. Unpublishing a lab immediately revokes access to its evidence files too — checked live on every request, not cached.
- **Parameterized queries**: 100% SQLAlchemy ORM/Core — no string-formatted SQL anywhere in the codebase (verified by grep as part of this milestone's hardening pass).
- **Rate limiting**: login/register (5/min), evidence uploads (20/min), and public portfolio endpoints (60/min) — slowapi, keyed by client IP.
- **Audit logging**: register, login, lab create/update/delete/status-change/portfolio-publish, evidence upload/delete — who, what, when, and from what IP, with the entry committed in the same transaction as the action itself.
- **Secure error handling**: a global exception handler logs full details server-side and returns only a generic message to the client — stack traces and internal paths never leak.
- **Security headers** on every response: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, and `Strict-Transport-Security` once the app is actually configured for HTTPS (`COOKIE_SECURE=true`).
- **No secrets in source control**: `.env` is gitignored; every secret is loaded from the environment via `app/config.py`.
- **API docs gated by environment**: `/docs`, `/redoc`, and `/openapi.json` are only served when `ENVIRONMENT` is not `production`.
- **What TALA does *not* attempt**: there is no automated scanner for credentials/API keys/secrets accidentally typed into write-up text or evidence descriptions — that would be unreliable to build well and would give false confidence. Instead, the "Publish to Portfolio" action shows an explicit confirmation dialog naming exactly which sections are about to go public and warning about secrets before the user proceeds.

## Testing

180+ automated backend tests (`pytest`), organized one file per feature area, plus a single end-to-end test walking the entire real user journey.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -v
```

Tests run against an isolated in-memory SQLite database (with `PRAGMA foreign_keys=ON`, so cascade-delete behavior is exercised faithfully, matching Postgres's native behavior rather than just being assumed) — no live Postgres connection needed to run the suite.

**Coverage includes:** authentication and session handling, authorization/ownership isolation between users (tested by directly inserting a second user's data and confirming the first user can't reach it), lab CRUD and write-up saving, evidence upload validation (extension whitelist, magic-byte mismatch, non-UTF-8 text, oversized files, path-traversal-attempt safety), skills/tools/MITRE relationship tracking and their computed statistics, CTF tracker CRUD, dashboard statistics (including a dedicated pure-function test suite for the streak-calculation logic), the learning roadmap's cycle-prevention logic, portfolio publish/unpublish and exhaustive checks that private data never reaches the public endpoints, PDF/Markdown report generation, global search, security headers, and sample data integrity.

**End-to-end test** (`tests/test_e2e_workflow.py`): Create Lab → Add Write-up → Add Evidence → Add Skills → Add Tools → Add MITRE Technique → Complete Lab → Mark Portfolio Ready → View Public Write-up — using a second, unauthenticated test client for the final step to genuinely simulate an outside visitor.

## Example lab workflow

1. **Create a lab** — title, platform, category, difficulty; status starts at `Planned`.
2. **Write it up** as you work — Methodology, Findings, Analysis, Lessons Learned, Reflection, Next Steps, in Markdown with a live preview.
3. **Upload evidence** — a screenshot, a log excerpt, a PCAP. Each file is validated, hashed, and stored under a random filename.
4. **Attach skills and tools** you actually used — typing a name reuses the existing entry if it matches (case-insensitively) or creates a new one.
5. **Map a MITRE ATT&CK technique**, selecting from the real reference list and writing a short justification for why it applies.
6. **Mark the lab Completed** once you're done, with a completion date — this is what makes it count in your dashboard stats.
7. **(Optional) Publish to your portfolio** — review the confirmation dialog, mark any evidence you want shown as Public, and share the generated link.
8. **Export a report** any time — a PDF or Markdown document with everything you documented, for your own records or to send to someone directly.

## Limitations

Being upfront about what this MVP doesn't do, rather than letting a reviewer discover it:

- **Single-user by design.** The schema has `user_id` on every owned table, so multi-user support is a config/authorization change away, not a rewrite — but registration is intentionally closed after the first account.
- **No password reset flow.** If you forget your password, there's no "forgot password" email flow; you'd need to update the password hash directly in the database or re-create the account.
- **No automated secret/credential scanning** on free-text fields before publishing to the portfolio — this is explicitly a user responsibility, with a clear warning shown before publishing (see [Security considerations](#security-considerations)).
- **MITRE technique list is curated, not complete.** 18 representative techniques, not the full 600+-technique ATT&CK matrix.
- **No real-time collaboration or multi-device sync** beyond what a shared Postgres database naturally provides.
- **PDF reports don't paginate charts as images** — the Learning Summary's "activity over time" section is a data table, not a rendered chart graphic, to avoid adding a headless-chart-rendering dependency for an MVP.
- **No session refresh token** — sessions expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60) and require signing in again, rather than silently refreshing.

## Future improvements

Explicitly out of scope for this MVP (see the original project brief):

- AI-assisted write-up summarization
- Automatic lab difficulty estimation
- Browser extension
- GitHub integration
- TryHackMe/HTB API integration
- Automated screenshot OCR
- Automatic MITRE technique extraction from write-up text
- SIEM integration
- Certification tracking
- Team collaboration / multi-user accounts
- Public user profiles
- Advanced analytics beyond what's in the current dashboard

## Skills demonstrated

- **Secure web application development**: authentication, session management, authorization/ownership enforcement, secure file handling, rate limiting, security headers, audit logging, and a documented, deliberate sanitization boundary for public data exposure.
- **Database design**: a normalized relational schema with 18 tables, proper foreign keys and indexes, junction tables (including association objects carrying their own data) for many-to-many relationships, and 7 incremental Alembic migrations.
- **Cybersecurity domain modeling**: structured technical write-ups matching real SOC/DFIR report conventions, MITRE ATT&CK mapping with an anti-fabrication guardrail, evidence handling with SHA-256 integrity hashing (a chain-of-custody concept from digital forensics), and severity-rated structured findings.
- **Full-stack engineering**: a typed REST API (FastAPI + Pydantic) consumed by a typed React frontend (TanStack Query for server state, React Router, Tailwind), with consistent patterns (ownership checks, error handling, loading/empty states) applied across 10+ feature areas.
- **Automated testing discipline**: 180+ tests covering happy paths, validation failures, security boundaries, and cross-user isolation — plus a single consolidated end-to-end test of the real user journey, and tests that re-validate seeded sample data against the same schemas real user input goes through.
- **Technical writing and documentation**: this README, inline code comments explaining *why* a security decision was made (not just what the code does), and milestone-by-milestone incremental delivery with test coverage at every stage.
