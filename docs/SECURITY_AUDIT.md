# Security audit

Audit date: 2026-10-14. Scope: repository configuration, frontend API boundary, FastAPI routes, crawling, retrieval/RAG, dependencies, and deployment assumptions.

## Critical / deployment blocker

- **Unauthenticated inference:** `/api/v1/ask` can incur provider cost and there is no end-user identity or authorization model. A local IP sliding-window limiter was added as defense in depth, but it is neither durable nor distributed. Public deployment is blocked until a server-side identity layer, shared per-principal limits, quotas/budgets, and cost alerts exist. A frontend shared password/API key is explicitly rejected.

## High

- **Public corpus surface:** document, search, dashboard, topic, and monitoring reads are unauthenticated. This may expose indexed content and metadata. Product owners must define public/private data policy and implement authorization before release.
- **Process-local controls:** crawl and inference limit state resets on restart and is not shared between replicas. The embedded crawl worker also needs staging/load validation before horizontal scaling.
- **Crawler network boundary:** input validation requires HTTPS/standard ports and an administrator allowlist (with an exact local-development exception), but application hostname checks alone are not a complete SSRF boundary. Production should enforce DNS/IP resolution and egress policy that rejects loopback, private, link-local, and metadata-service addresses, including redirects and DNS rebinding.

## Medium

- **Transitive Transformers advisories:** the declared embedding stack currently resolves to `transformers` 4.57.6, for which `pip-audit` reports model/checkpoint-loading vulnerabilities. The affected Trainer, X-CLIP, causal-LM, LightGlue, tokenizer-save, and custom-generate paths are not used by WebIntel's fixed sentence-embedding flow, but the broad transitive range remains unsuitable for an unreviewed model supply chain. Pin a reviewed model commit, prohibit user-selected model paths/repos, and validate a compatible patched Transformers line before public release.
- **Reproducibility:** several Python dependency ranges are intentionally broad and the default embedding revision is `main`. Lock reviewed application dependencies for reproducible builds and pin the model revision to an immutable commit.
- **Proxy identity:** IP limiting uses `request.client.host`. It is safe from spoofed forwarding headers at the app layer, but may collapse traffic to one proxy address. Configure only a trusted proxy chain and prefer authenticated principal IDs.
- **Readiness metadata:** the readiness response includes the logical database name. It does not reveal credentials, and the Settings UI deliberately omits it, but removing that field in a future version would reduce disclosure.

## Low / informational

- CORS is intentionally absent because the supported production topology is same-origin. Adding broad CORS would weaken this boundary.
- Provider exceptions are converted to generic errors, indexed evidence is marked untrusted in the RAG prompt, and returned quotations/citation identifiers are backend-verified.
- No raw HTML rendering was found. External source links are URL-validated and use `noreferrer`.
- Crawl write routes use constant-time API-key comparison and per-key limits. An empty crawl API key remains a localhost-development behavior and must not be used on a reachable production service.

## Implemented in this milestone

- Security response headers and configurable OpenAPI/Swagger exposure.
- Inference rate-limit backstop with a 429 response and regression coverage.
- Updated `sentence-transformers` to 5.6.0, which fixes CVE-2026-68770's local-model trust bypass; transitive advisories remain documented above.
- Secret-safe Settings diagnostics and explicit production access warning.
- Same-origin reverse-proxy example, non-root backend image, expanded safe environment template, and deployment guidance.
- Route-level frontend splitting, mobile-dialog keyboard containment, skip navigation, status live regions, and deterministic chart tests.

Automated checks do not constitute penetration testing or WCAG certification. Provider controls, TLS, headers at the real edge, authentication flows, backup restores, and crawler egress must be verified in staging.

## Dependency scan results

- `npm audit` inspected 428 frontend dependencies and reported no known advisories at audit time.
- `pip check` reported a consistent Python environment.
- `pip-audit` found and drove the `sentence-transformers` 5.6.0 update. The remaining reported application advisories are in transitive `transformers` 4.57.6 and are described under Medium findings; they were not hidden with ignore flags. The project virtual environment's `pip` was separately updated to 26.2.1 to clear installer advisories.
