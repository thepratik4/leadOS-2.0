# LeadOS 2.0 — Evidence-First B2B Prospecting Platform

A production-minded, evidence-first B2B prospecting platform developed for the **Caprae Capital Full Stack Developer** hiring assignment.

LeadOS is engineered around one defining principle:
> **Every meaningful company claim must be traceable to a primary source, and every lead score must have an understandable, deterministic explanation.**

---

### 🌐 Live Deployment & Submission Artifacts
- **Live Web Application**: [https://leados-v2-ashy.vercel.app/](https://leados-v2-ashy.vercel.app/)
- **Live Interactive API Docs**: [https://leados-v2-ashy.vercel.app/docs](https://leados-v2-ashy.vercel.app/docs)
- **Section 4 Written Responses**: [`BUSINESS_UNDERSTANDING.md`](./BUSINESS_UNDERSTANDING.md)
- **Interactive Technical Walkthrough (Jupyter)**: [`demo_notebook.ipynb`](./demo_notebook.ipynb)
- **Automated CLI Demo Script**: [`demo_walkthrough.py`](./demo_walkthrough.py)

---

## 1. System Architecture

```
                                  +---------------------------------------+
                                  |         LeadOS Next.js Frontend       |
                                  |  - Base UI Sidebar Navigation         |
                                  |  - Discovery Workspace & Quick Presets|
                                  |  - Evidence & Dossier Sheet Inspector |
                                  |  - Saved Leads & Formula-Safe Export  |
                                  +-------------------+-------------------+
                                                      |
                                                      | HTTP / REST (/api/v1)
                                                      v
                                  +---------------------------------------+
                                  |         FastAPI Backend (Python 3.13) |
                                  |  - /api/v1/health                     |
                                  |  - /api/v1/discovery/search & history |
                                  |  - /api/v1/companies/{id}/evidence    |
                                  |  - /api/v1/companies/{id}/dossier     |
                                  |  - /api/v1/companies/{id}/outreach    |
                                  |  - /api/v1/saved-leads & /export      |
                                  +---------+-------------------+---------+
                                            |                   |
               +----------------------------+                   +----------------------------+
               |                                                                             |
               v                                                                             v
+-----------------------------+                                               +-----------------------------+
|    Candidate Discovery      |                                               | SSRF-Guarded Web Crawler    |
| - BaseSearchProvider        |                                               | - Validates public host/IP  |
| - DuckDuckGo (Zero-Config)  |                                               | - Blocks loopback & 169.254 |
| - Brave Search API support  |                                               | - Manual redirect validator |
+--------------+--------------+                                               +--------------+--------------+
               |                                                                             |
               |                                                                             v
               |                                                              +-----------------------------+
               |                                                              | Evidence Validation Engine  |
               |                                                              | - Exact quotation check     |
               |                                                              | - Metric & numeric audits   |
               |                                                              | - Timestamp preservation    |
               +----------------------------+---------------------------------+
                                            |
                                            v
                              +-----------------------------+
                              | Deterministic Lead Scoring  |
                              | - Verified Trigger (Max 30) |
                              | - Industry Fit     (Max 25) |
                              | - Geographic Fit   (Max 20) |
                              | - Company Size Fit (Max 15) |
                              | - Evidence Quality (Max 10) |
                              +--------------+--------------+
                                             |
                                             v
                              +-----------------------------+
                              | Persistence Layer           |
                              | - SQLite (aiosqlite local)  |
                              | - PostgreSQL 16 (production)|
                              | - SQLAlchemy 2.0 + Alembic  |
                              +-----------------------------+
```

---

## 2. Key Engineering Decisions & Principles

1. **Zero Fabrication**:
   - No mock company lists silently returned when a search provider fails.
   - If DuckDuckGo or Brave Search encounters rate-limits or network failures, LeadOS surfaces an honest, structured diagnostic error.
   - Claims are strictly classified into: `verified`, `partially_verified`, `unverified`, or `unknown`. A claim is **never** marked verified merely because an LLM produced it or a search snippet mentions it.

2. **Controlled, SSRF-Guarded Source Retrieval**:
   - Only `http` and `https` schemes are accepted.
   - DNS resolution blocks RFC 1918 private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopbacks (`127.0.0.1`), and cloud metadata endpoints (`169.254.169.254`).
   - HTTP redirects are resolved manually up to 3 hops, re-validating the resolved destination IP at each hop before fetching content.
   - Resource bounded: 8.0s timeout, 2MB max payload size, 5-worker concurrency semaphore.

3. **Deterministic 5-Dimension Scoring Engine**:
   - Scores are computed via a pure mathematical function (0 to 100), never via non-deterministic LLM prompting:
     - **Verified Business Trigger** (30 pts max): Scaled by verified vs partially verified buying signal.
     - **Industry Fit** (25 pts max): Strict match on industry and product description.
     - **Geographic Fit** (20 pts max): Target country, state, or city verification.
     - **Company Size Fit** (15 pts max): Headcount range match when verified.
     - **Evidence Quality & Freshness** (10 pts max): Mathematical ratio of verified primary sources to total claims.
   - Every point awarded is accompanied by an understandable explanation and data-quality indicators.

4. **Structured Company Dossier**:
   - Dissected into:
     - **Verified Facts**: Direct source citations and exact quotations.
     - **Unverified Claims**: Explicitly flagged to prevent misrepresentation.
     - **Grounded Inferences**: Inferences derived *only* from verified facts, with explicit reasoning.
     - **Recommendations**: Tactical next steps for sales outreach.

5. **Grounded Cold Outreach Guard**:
   - LeadOS will only generate outreach drafts when substantiated by an active, verified business trigger (e.g. engineering hiring or technology adoption).
   - If evidence is lacking, LeadOS returns a structured **Insufficient Evidence Notice**, refusing to hallucinate recipient names or events.

6. **Formula-Injection Safe CSV Export**:
   - All string outputs sanitize spreadsheet formula injection characters (`=`, `+`, `-`, `@`, `\t`, `\r`) with leading single quotes.

---

## 3. Technology Stack

### Backend
- **Python**: 3.13 / 3.12 compatible
- **Framework**: FastAPI (asynchronous ASGI)
- **Validation**: Pydantic v2 & Pydantic-Settings
- **ORM / Database**: SQLAlchemy 2.0 async engine (`aiosqlite` for local dev; `asyncpg` for PostgreSQL in production)
- **Migrations**: Alembic
- **HTTP Client**: `httpx` (async client with connection pools & manual redirect checks)
- **HTML Parsing**: BeautifulSoup4 + lxml
- **Testing & Quality**: pytest, pytest-asyncio, Ruff

### Frontend
- **Framework**: Next.js 15 (App Router)
- **UI & State**: React 19, TypeScript (strict mode)
- **Styling**: Tailwind CSS v4, Lucide Icons
- **Design System**: shadcn/ui components with Base UI sidebar navigation
- **Validation**: Zod & React Hook Form

---

## 4. Quickstart Guide

### Prerequisites
- Python 3.12+ (or 3.13)
- Node.js 20+ or Bun 1.3+

### Backend Setup

1. Open a terminal in `./backend`:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   pip install aiosqlite beautifulsoup4 ddgs pytest pytest-asyncio ruff
   ```

3. Run automated tests:
   ```bash
   pytest tests -v
   ```
   *(All 18 unit & integration tests run and pass in under 1 second)*

4. Start the backend development server:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   - OpenAPI Documentation is available at: `http://127.0.0.1:8000/docs`
   - Health check: `http://127.0.0.1:8000/api/v1/health`

### Frontend Setup

1. Open a terminal in the root workspace directory:
   ```bash
   bun install   # or npm install
   ```

2. Build for production or start the dev server:
   ```bash
   # Production build verification:
   bun run build   # or npm run build

   # Start local dev server:
   bun run dev     # or npm run dev
   ```

3. Open `http://localhost:3000` in your browser.

---

## 5. Docker Deployment (Optional)

A multi-container Docker Compose configuration is provided for running LeadOS with persistent PostgreSQL:

```bash
docker compose up --build
```

This launches:
- PostgreSQL 16 on port `5432` with automatic health checks.
- LeadOS Backend on port `8000` with automated database migrations.

---

## 6. Testing & Quality Verification

### Automated Backend Tests
Run the complete test suite:
```bash
pytest backend/tests -v
```
Test categories covered:
- **`test_scoring_service.py`**: Mathematical determinism, unverified penalties, boundary clamps [0, 100].
- **`test_evidence_validator.py`**: Exact quotation matching, numeric/metric validation, missing keyword penalties, partial match ratios.
- **`test_ssrf_validator.py`**: Loopbacks, RFC 1918 private ranges, AWS/GCP cloud metadata IP, invalid schemes.
- **`test_saved_leads.py`**: Complete lifecycle (Save, List, PATCH status/notes, formula-safe CSV export, DELETE).
- **`test_api_endpoints.py`**: Health checks, company details, dossier generation, grounded outreach, and insufficient evidence guards.

### Frontend Production Build
Run:
```bash
npm run build   # or bun run build
```
Compiles with 0 TypeScript errors and generates optimized static routes for production.

---

## 7. Interactive Demonstrations (CLI & Jupyter Notebook)

Two standalone demonstration options are provided to satisfy the Caprae hiring handbook's demonstration recommendation:

### Option A: Standalone CLI Demo Script
Run the automated end-to-end Python demo from the repository root:
```bash
python demo_walkthrough.py
```
This demonstrates the four core engines without requiring web servers:
1. **SSRF Guard**: Verifies blocked AWS cloud metadata (`169.254.169.254`), loopbacks, and RFC 1918 subnets.
2. **Evidence Engine**: Tests exact quotation matches, numeric/metric validation, and flags fabricated claims.
3. **Deterministic Lead Scoring**: Executes the 5-dimension mathematical algorithm [0, 100] with full breakdown.
4. **Grounded Cold Outreach Guard**: Demonstrates citation on verified triggers and refusal on unverified signals.

### Option B: Interactive Jupyter Notebook
Open and execute the step-by-step interactive notebook:
```bash
# Launch in Jupyter:
jupyter notebook demo_notebook.ipynb

# Or open directly in VS Code / GitHub to inspect pre-formatted markdown and cell outputs.
```

---

## 8. Data Storage Architecture (Local vs Docker vs Hosted)

### How is the Database Stored Locally?
- **Zero-Config SQLite**: By default, LeadOS uses asynchronous SQLite via `aiosqlite`.
  - Database file location: `./backend/leados.db`
  - Connection string: `sqlite+aiosqlite:///./leados.db`
  - All company profiles, primary source evidence, search runs, and saved leads are stored locally in this single file. You can inspect it directly using SQLite Viewer, DBeaver, or DB Browser for SQLite.
- **Docker Compose (PostgreSQL 16)**:
  - If started via `docker compose up`, LeadOS provisions an enterprise PostgreSQL 16 container.
  - Data is persisted across container restarts in the named Docker volume: `postgres_data`.

### How is the Database Stored When Hosted on Vercel?
- **Serverless Ephemeral Storage**: Vercel Serverless Functions execute in a stateless environment with a read-only root directory. For zero-config serverless testing, LeadOS automatically routes SQLite to `/tmp/leados.db` (the only writable scratch partition).
- **Production Cloud Persistence**: For permanent, multi-user persistence in production, attach any managed cloud PostgreSQL instance (such as **Neon**, **Supabase**, or **Vercel Postgres**):
  1. Create a free Postgres instance on Neon or Supabase.
  2. Set the `DATABASE_URL` environment variable in your Vercel Project Settings:
     ```env
     DATABASE_URL=postgresql+asyncpg://user:password@ep-host.aws.neon.tech/neondb
     ```
  3. LeadOS's configuration engine automatically normalizes the URL for `asyncpg`, applies connection pool recycling, and runs table schemas automatically on startup.

---

## 9. Known Limitations & Tradeoffs

1. **Website Anti-Scraping**: Public websites protected by Cloudflare Bot Management or perimeter CAPTCHAs will not yield full HTML content. In such cases, LeadOS honestly reports `status: unknown` and records the HTTP response code rather than hallucinating fake content.
2. **Deterministic Weights**: Scoring weights (30/25/20/15/10) represent product assumptions for B2B ICP fit. In a production enterprise system, weights can be calibrated per sales persona or team ICP profile.
3. **Logo Retrieval**: External logos use domain initials and neutral fallbacks to prevent third-party tracking or layout breakage when external favicon endpoints fail.
