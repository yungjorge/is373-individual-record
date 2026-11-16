# API v1

Interactive OpenAPI is served at `/docs`. The same-origin Next.js proxy forwards `/api/v1/*` to Python. JSON requests use `Content-Type: application/json`. Authenticated calls use an Auth0 API access token in `Authorization: Bearer …`; demo calls use an HttpOnly guest cookie.

| Method | Route | Behavior |
|---|---|---|
| GET | `/api/v1/health` | Mode and process health |
| GET | `/api/v1/ready` | SQL corpus and vector dimension readiness |
| POST | `/api/v1/demo-session` | Create/reuse 24-hour guest, demo only |
| POST | `/api/v1/conversations` | Create owned conversation |
| GET | `/api/v1/conversations` | Latest 100 owned conversations |
| GET | `/api/v1/conversations/{id}` | Owned message history |
| DELETE | `/api/v1/conversations/{id}` | Delete owned conversation/messages |
| POST | `/api/v1/conversations/{id}/messages` | SSE grounded answer |
| GET | `/api/v1/sources?q=&author=&work=&offset=` | Catalog, blocked candidates, paged passages |
| GET | `/api/v1/sources/{id}` | Approved registry detail |
| GET | `/api/v1/passages/{id}` | Trusted source text and metadata |
| GET | `/api/v1/bookmarks` | Owned bookmarks |
| POST/DELETE | `/api/v1/bookmarks/{passage_id}` | Idempotent save/remove |
| POST | `/api/v1/debug/retrieve` | Demo-only retrieval details, guest/auth required |
| POST | `/api/v1/admin/ingest/{work}` | Separate admin bearer token; disabled when unset |

Message body: `{"message":"I am anxious about tomorrow.","author":null,"work":null}`. Maximum 6,000 characters, blank messages rejected. Filter values match manifest author/work. Unknown filters yield no evidence.

SSE frame types: `status` (progress), `delta` (validated summary text), `result` (validated summary/explanations/applications/question/citations), `done`, or sanitized `error`. The client must not interpret a connection close as success without a result. Failed generation saves neither half of the exchange. A successful complete result is persisted before emission, so a client disconnect may leave a completed exchange in history.

The result contains source IDs and metadata assembled by Python. Debug includes only the current user's query/context-derived rewrite, public source candidates, scores, timing and non-secret model usage. It is disabled outside demo mode. Admin authority is not granted by a frontend role or user ID.

HTTP errors use `{"error":{"code":404,"message":"Conversation not found"}}`. FastAPI request validation uses its standard 422 detail structure. Ownership failures return 404 to avoid disclosing another user's IDs; invalid JWT is 401; disabled admin/debug access is 403; concurrent replies are 409; limits are 429. Streaming errors arrive as SSE after HTTP headers have been sent.
