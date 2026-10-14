# WebIntel AI Frontend

Production-oriented React interface for the WebIntel AI FastAPI service. It includes the live intelligence overview and a document workspace for exploring the indexed corpus, immutable revisions, backend-generated comparisons, and source provenance. Remaining navigation destinations are intentional placeholders for later milestones.

## Requirements

- Node.js 20.19+ or 22.12+
- npm 10+
- Python 3.12 and the existing backend dependencies
- MongoDB configured for the existing FastAPI application

## Install

From PowerShell:

```powershell
Set-Location D:\webintel-ai\frontend
npm install
Copy-Item .env.example .env.local
```

No secret is required by this frontend. Never place MongoDB, Groq, or protected backend API keys in a `VITE_*` variable: Vite embeds those values in browser assets.

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | empty | Browser-visible API origin. Empty uses same-origin `/api` requests and is recommended. |
| `WEBINTEL_API_PROXY_TARGET` | `http://127.0.0.1:8000` | Development-only Vite proxy target; it is not bundled into browser code. |

The backend currently does not install CORS middleware. Local development therefore uses Vite's `/api` proxy. For production, serve the frontend and API behind one origin or configure a narrowly scoped deployment-specific reverse proxy. The dashboard and health GET routes are public; API-key authentication is limited to crawl submission/cancellation write routes.

## Run locally

Terminal 1 — start MongoDB using the repository configuration:

```powershell
Set-Location D:\webintel-ai
docker compose up -d mongodb
```

Terminal 2 — start FastAPI:

```powershell
Set-Location D:\webintel-ai\backend
..\.venv312\Scripts\Activate.ps1
uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 3 — start Vite:

```powershell
Set-Location D:\webintel-ai\frontend
npm run dev
```

Open `http://127.0.0.1:5173`.

## Quality commands

```powershell
Set-Location D:\webintel-ai\frontend
npm run lint
npm run typecheck
npm test
npm run build
```

The production output is written to `frontend\dist`.

## API routes used

- `GET /api/v1/health/ready`
- `GET /api/v1/analytics/dashboard/summary`
- `GET /api/v1/analytics/dashboard/domains`
- `GET /api/v1/analytics/dashboard/revision-activity?start=<UTC>&end=<UTC>`
- `GET /api/v1/documents?page=<n>&page_size=<n>&q=<term>&document_type=<type>&source_domain=<domain>&tag=<tag>`
- `GET /api/v1/documents/{document_id}`
- `GET /api/v1/documents/{document_id}/sources`
- `GET /api/v1/documents/{document_id}/revisions`
- `GET /api/v1/analytics/documents/{document_id}/changes`
- `GET /api/v1/analytics/documents/{document_id}/compare?from_revision_id=<id>&to_revision_id=<id>`

Revision windows use explicit UTC midnights and the backend's exclusive `end` boundary. The UI offers 7, 14, and 30 days, all below the backend's 90-day maximum.

Document filters are synchronized to URL search parameters and executed by MongoDB through the existing API. Free-text search covers title and content. The backend currently fixes list ordering to newest `scraped_at`, then document ID; the UI labels that limitation rather than applying incomplete client-side sorting. Revision counts are not part of list responses and are therefore shown only after opening a document.

## Troubleshooting

- **Backend unavailable:** verify FastAPI is running on port 8000 and `/api/v1/health/ready` returns 200. A 503 means MongoDB is not initialized or ready.
- **Vite proxy connection refused:** confirm `WEBINTEL_API_PROXY_TARGET` points to the FastAPI origin, then restart Vite after changing `.env.local`.
- **Empty dashboard:** this is a valid state. Ingest documents with the existing backend workflows; the frontend never substitutes demo data.
- **Invalid server response:** the UI validates analytics payloads at runtime. Confirm the running backend matches this repository's dashboard service contracts.
- **Document not found:** verify the route contains the complete 64-character SHA-256 document ID and that the current document still exists in the configured database.
- **Production cross-origin failure:** use a same-origin reverse proxy. Do not enable wildcard CORS with credentials.
