# WebIntel AI

WebIntel AI is a React/FastAPI workspace for crawled-document exploration, immutable revision history, hybrid retrieval, evidence-grounded RAG, topic analysis, and source monitoring.

## Architecture

- `frontend/`: React 19, Vite, strict TypeScript, Tailwind, TanStack Query, Recharts.
- `backend/`: FastAPI, PyMongo async client, Scrapy/Playwright crawling, sentence-transformers retrieval, and server-side Groq access.
- MongoDB is the durable store for documents, revisions, provenance, vectors, and crawl jobs.
- The browser calls same-origin `/api/*`. Vite proxies that path locally; production must route it through a trusted reverse proxy to the persistent backend.

## Windows development setup

From PowerShell in `D:\webintel-ai`:

```powershell
Copy-Item .env.example .env
py -3.12 -m venv .venv312
.\.venv312\Scripts\python.exe -m pip install -r backend\requirements.txt
Set-Location backend
..\.venv312\Scripts\python.exe -m uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000
```

In a second PowerShell window:

```powershell
Set-Location D:\webintel-ai\frontend
npm ci
npm run dev
```

The default `.env.example` expects a local authenticated MongoDB on `127.0.0.1:27017`. One development-only way to start it is:

```powershell
docker run --name webintel-mongo -p 127.0.0.1:27017:27017 -e MONGO_INITDB_ROOT_USERNAME=webintel_dev -e MONGO_INITDB_ROOT_PASSWORD=webintel_local_only -v webintel-mongo-data:/data/db -d mongo:8
```

Set `GROQ_API_KEY` only in the root `.env` or a production secret manager. Never create a `VITE_*` secret. Set `WEBINTEL_ALLOWED_HOSTS` to a comma-separated crawl allowlist and set a strong `WEBINTEL_API_KEY` before permitting crawl submissions outside localhost.

## Checks and builds

```powershell
Set-Location D:\webintel-ai\frontend
npm run lint
npm run typecheck
npm test -- --run
npm run build

Set-Location D:\webintel-ai\backend
..\.venv312\Scripts\python.exe -m pytest tests
```

With both development servers running and Playwright Chromium installed, run the read-only viewport smoke check with:

```powershell
$env:WEBINTEL_SMOKE_URL = 'http://127.0.0.1:5173/'
Set-Location D:\webintel-ai\backend
..\.venv312\Scripts\python.exe scripts\browser_smoke.py
Remove-Item Env:WEBINTEL_SMOKE_URL
```

MongoDB integration tests are opt-in and use the configured database:

```powershell
$env:WEBINTEL_RUN_MONGO_TESTS = '1'
Set-Location D:\webintel-ai\backend
..\.venv312\Scripts\python.exe -m pytest tests
Remove-Item Env:WEBINTEL_RUN_MONGO_TESTS
```

The static production frontend build is `frontend/dist`. A backend container image can be built with:

```powershell
docker build -t webintel-api:local .\backend
```

The container artifact does not pre-download the embedding model or Playwright browser binaries. Bake/cache the pinned embedding revision and extend the image with the required Chromium runtime before enabling browser-based crawl jobs.

## Configuration

See [.env.example](.env.example). Important production values include `MONGODB_URI`, `MONGODB_DATABASE`, `GROQ_API_KEY`, `WEBINTEL_API_KEY`, `WEBINTEL_ALLOWED_HOSTS`, `WEBINTEL_API_DEBUG=false`, `WEBINTEL_API_DOCS_ENABLED=false`, `WEBINTEL_EMBEDDING_MODEL`, a pinned `WEBINTEL_EMBEDDING_REVISION`, and the workload/rate-limit settings.

`WEBINTEL_API_PROXY_TARGET` is only for Vite development. Hosted traffic should remain same-origin through `/api`; do not point hosted code at localhost. `WEBINTEL_BUILD_ID` is non-sensitive metadata compiled into the frontend.

## Security and release status

Production release is currently **blocked** because end-user authentication and durable distributed inference abuse controls are not implemented. The current IP limiter is a useful single-process backstop, not a public authorization boundary. Public document and analytics access also requires an explicit product/privacy decision.

See [Production deployment](docs/PRODUCTION_DEPLOYMENT.md) and [Security audit](docs/SECURITY_AUDIT.md) for the proposed architecture, readiness checklist, monitoring, limitations, and troubleshooting.
