# WebIntel AI Frontend

Production-oriented React interface for the WebIntel AI FastAPI service. It includes the live intelligence overview, document and provenance exploration, hybrid evidence search, a grounded RAG assistant, deterministic topic intelligence, and source-observation monitoring. Settings remains an intentional placeholder for a later milestone.

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
- `POST /api/v1/search`
- `POST /api/v1/ask`
- `GET /api/v1/analytics/topics`
- `GET /api/v1/analytics/topics/domains`
- `GET /api/v1/analytics/topics/trends`
- `GET /api/v1/analytics/monitoring/overview`
- `GET /api/v1/analytics/monitoring/documents`
- `GET /api/v1/analytics/monitoring/domains`

Revision windows use explicit UTC midnights and the backend's exclusive `end` boundary. The UI offers 7, 14, and 30 days, all below the backend's 90-day maximum.

Document filters are synchronized to URL search parameters and executed by MongoDB through the existing API. Free-text search covers title and content. The backend currently fixes list ordering to newest `scraped_at`, then document ID; the UI labels that limitation rather than applying incomplete client-side sorting. Revision counts are not part of list responses and are therefore shown only after opening a document.

Intelligence Search synchronizes the submitted query, retrieval mode, result limit, document type, and exact source domain with the URL. The backend supports `keyword` (BM25), `semantic` (embedding cosine similarity), and `hybrid` (reciprocal-rank fusion) retrieval. Scores are displayed as mode-specific ranking signals and are never converted into confidence percentages or compared across modes.

The AI Assistant submits one independent question per `POST /api/v1/ask` request. Visible turns are kept in React memory only and are neither persisted nor sent as conversation history. Answer claims, citation identifiers, quotations, document links, abstention reasons, and model metadata are displayed only from the validated backend response. The browser uses a 70-second request window to accommodate the backend provider timeout and supports cancellation and exact-request retry.

Topic Intelligence reports deterministic unigram or unigram-plus-bigram document frequency. Revision trends compare the latest available revision per document in two ordered, non-overlapping UTC windows with an overall horizon of at most 366 days. An empty baseline is called out explicitly; lexical change is not presented as semantic classification or evidence of public popularity.

Source Monitoring classifies the age of recorded observations using a shared fixed `as_of` timestamp and configurable `fresh_hours` / `stale_hours` thresholds. The document endpoint is a bounded list (`limit` 1–100), not a paginated or user-sortable API. Provenance coverage refers only to indexed documents and does not establish crawl events, content freshness, complete website coverage, or current source availability.

## Troubleshooting

- **Backend unavailable:** verify FastAPI is running on port 8000 and `/api/v1/health/ready` returns 200. A 503 means MongoDB is not initialized or ready.
- **Vite proxy connection refused:** confirm `WEBINTEL_API_PROXY_TARGET` points to the FastAPI origin, then restart Vite after changing `.env.local`.
- **Empty dashboard:** this is a valid state. Ingest documents with the existing backend workflows; the frontend never substitutes demo data.
- **Invalid server response:** the UI validates analytics payloads at runtime. Confirm the running backend matches this repository's dashboard service contracts.
- **Document not found:** verify the route contains the complete 64-character SHA-256 document ID and that the current document still exists in the configured database.
- **Search unavailable:** verify MongoDB is ready and the configured embedding model can initialize. The first semantic or hybrid request may take longer while the local model loads.
- **No search matches:** ensure document chunks were indexed with the backend's current embedding configuration; search intentionally ignores mismatched index configurations.
- **Assistant abstained:** this is an intentional grounded outcome when retrieval or citation validation cannot support an answer. Broaden the retrieval controls or inspect the linked search results.
- **Language-model provider unavailable:** verify the backend's Groq configuration and provider connectivity. The frontend does not contain or require the provider secret.
- **Topic window rejected:** use explicit UTC dates satisfying `before_start < before_end <= after_start < after_end`; the combined horizon cannot exceed 366 days.
- **Monitoring thresholds rejected:** use whole hours satisfying `1 <= fresh_hours < stale_hours <= 87600` and a timezone-aware evaluation timestamp.
- **Production cross-origin failure:** use a same-origin reverse proxy. Do not enable wildcard CORS with credentials.
