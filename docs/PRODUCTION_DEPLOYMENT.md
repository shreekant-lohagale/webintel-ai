# Production deployment

## Recommended topology

Use a static frontend host or CDN, a persistent Python service, and managed MongoDB. Route the public domain's `/api/*` to the backend while all other paths serve the Vite bundle. This same-origin model avoids browser-held backend credentials and does not require permissive CORS.

```text
Browser -> HTTPS/CDN/reverse proxy -> React assets
                                 \-> /api/* -> persistent FastAPI service -> managed MongoDB
                                                                     \-> Groq API
                                                                     \-> model cache
```

Vercel is suitable for the static frontend if its `/api/*` rewrite targets an already deployed public HTTPS backend. Never rewrite to `localhost`. The FastAPI service should run on a container/VM platform with sufficient memory for sentence-transformers, startup time for model initialization, persistent outbound HTTPS, and a writable temporary area. Do not treat a developer's Docker MongoDB volume as hosted storage.

## Runtime requirements

- Terminate TLS at the edge and restrict backend ingress to the edge/private network where the provider supports it.
- Store MongoDB, Groq, and crawl API credentials in a managed secret store; rotate them after suspected exposure.
- Use managed MongoDB with authentication, TLS, backups, restore testing, restricted network access, and capacity alerts.
- Pin `WEBINTEL_EMBEDDING_REVISION` to a reviewed immutable model commit. Pre-cache it in the image or a persistent model cache to avoid cold-start downloads.
- The supplied backend image runs one Uvicorn worker because crawl coordination and rate limits are process-local. Before scaling horizontally, move rate limits and job coordination semantics to shared infrastructure and load-test them.
- The base image supports non-browser crawls. Install Playwright's pinned Chromium runtime in a derived image before allowing `browser=true` jobs.
- Use `GET /api/v1/health/live` for liveness and `GET /api/v1/health/ready` for readiness. Do not send traffic until readiness succeeds.
- Keep `WEBINTEL_API_DEBUG=false` and `WEBINTEL_API_DOCS_ENABLED=false` publicly.

## Routing and caching

Build with `npm ci` and `npm run build`, publish `frontend/dist`, enable SPA fallback to `/index.html`, cache hashed `/assets/*` immutably, and do not cache `index.html`. [`deploy/nginx.conf.example`](../deploy/nginx.conf.example) demonstrates the routing and response headers. Adapt trusted-proxy settings to the actual provider; never trust forwarded client-IP headers from arbitrary internet clients.

## Required production controls before release

1. Put the application behind server-side user authentication (OIDC/session cookies are the minimal conventional architecture).
2. Authorize access to document/search/analytics data by tenant or user policy.
3. Apply a shared rate limiter to inference and crawling, keyed by authenticated principal, with daily budgets and provider-spend alerts.
4. Protect state-changing routes with CSRF defenses if cookie authentication is used.
5. Decide whether indexed content is legally and operationally appropriate for public exposure.
6. Restrict crawling to an approved hostname allowlist and add DNS/IP egress enforcement to block private/link-local destinations at the network layer.
7. Forward structured logs and request IDs to centralized storage without prompts, document content, secrets, or credentials.

## Monitoring and operations

Alert on readiness failures, HTTP 5xx/429 rates, latency, queue depth/age, crawl failures, MongoDB capacity/connection saturation, model initialization failures, and Groq errors/spend. Record deploy/build identifiers. Establish backup retention and a restore drill. Provider sizing and prices remain pending verification because no provider/account region was selected.

## Troubleshooting

- Frontend loads but API calls fail: confirm `/api/*` routes to the HTTPS backend and the backend is ready.
- Semantic search is slow on first request: verify the embedding model is pre-cached and the service has enough memory/CPU.
- Browser crawl fails in the container: install the Playwright Chromium runtime and system dependencies in the deployment image.
- All clients appear rate-limited together: the backend is probably seeing the proxy IP; configure a trusted proxy chain and key production limits by authenticated user.
- Readiness is 503: verify MongoDB TLS/network access, credentials, and database selection without returning the URI to the browser.

## Readiness checklist

- [x] Static production build and SPA fallback guidance
- [x] Same-origin API routing and health endpoints
- [x] Secret-free environment template
- [x] Debug/docs production switches and baseline security headers
- [x] Non-root backend container artifact
- [ ] Server-side end-user authentication and authorization
- [ ] Distributed inference/crawl limits, budgets, and alerts
- [ ] Managed MongoDB, backups, and restore test
- [ ] Pinned/pre-cached embedding model and measured resource sizing
- [ ] Browser runtime image, if browser crawls are enabled
- [ ] Provider-specific staging deployment, load test, and manual accessibility/browser sign-off

No infrastructure has been purchased or deployed by this repository change.
