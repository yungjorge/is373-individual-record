# Verification results

[Review index](../README.md#research-review-index)

Checks executed for this record on November 15, 2026 (Eastern). Historical reports inside the preserved application remain dated November 12 and must not be read as new executions.

| Check                                          | Actual result                                                                                                                                                                                                                  |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Authenticated identity and repository creation | Local GitHub credentials and connector both identify `yungjorge`; created public `is373-individual-record`.                                                                                                                    |
| Backend unit/integration suite                 | 52 passed locally, Python 3.13, 5.68 seconds. One Starlette/httpx deprecation warning. Existing virtual-environment dependencies used against the copied source, without loading original credentials.                         |
| Backend Ruff                                   | Passed against preserved backend source.                                                                                                                                                                                       |
| Frontend dependency install                    | `npm ci --no-audit --no-fund` installed 122 packages from lockfile. This command does not itself constitute a vulnerability audit.                                                                                             |
| Frontend production build                      | `npm run build` passed, Next.js 15.5.29; compilation, type checks and prerendering succeeded.                                                                                                                                  |
| Worked trace                                   | Executed offline with isolated temporary SQLite/Qdrant and demo vectors; 52 source units, 66 chunks validated; Encheiridion I retrieved first. [Actual JSON](checks/worked-trace.json). Generated answer remains illustrative. |
| Partner feedback publication                   | [Issue #1](https://github.com/pb392/is373-individual-record/issues/1) created through authenticated CLI, fetched back through connector; author `yungjorge`, open, full expected body present.                                 |
| Partner document inspection                    | README review index, both S3 notes, career and technical sections read at commit `378ce760`; related CI and app source inspected. No partner RAG implementation tests claimed.                                                 |
| Incoming review                                | No genuine issue found in Jorge's newly created repository. No incoming issue closed.                                                                                                                                          |

Additional completed checks:

- `python scripts/check_docs.py`: 31 Markdown files and 93 local destinations passed, including heading anchors and the README review index.
- Prettier 3.6.2 formatted the research Markdown; the CI job checks the same files.
- Offline browser suite: **4 Playwright tests passed in 36.0 seconds**, desktop and mobile Chromium. The suite exercises reflections, citations, bookmarks, persistence/deletion and missing-evidence behavior. No paid inference was used. The copied `docs/screenshots/desktop.png` and `mobile.png` were refreshed by this real run; historical live screenshots in `docs/evidence` remain distinct.
- Full offline ingestion: 567 units and 909 children across six approved sources; both blocked candidates were rejected as intended.
- External GET observations: 29 distinct linked URLs checked. Existing portfolio returned HTTP 200. Canvas redirected to NJIT login; Epic P2 returned 403. All other requested URLs returned 200, which does not establish their semantic content or current vacancy status. [Raw observations](checks/external-links.json).
- Secret-pattern scan of the publishable text found no provider/GitHub tokens or private-key blocks. Runtime databases, credentials and dependency directories are excluded from Git.

CI publication results are added after pushing. No new paid-provider evaluation, Auth0 tenant login, public Stoic deployment or Canvas submission was executed.

## Reproduction

From repository root run `python scripts/check_docs.py`; with application dependencies installed, run `python scripts/worked_trace.py`. From `projects/stoic-companion`, run `pytest -q` and `ruff check backend`. From its `frontend`, run `npm ci`, `npm run lint`, `npm run build` and the offline Playwright suite after ingesting the approved corpus. CI mirrors these checks with Python 3.12 and Node 22.

## Evidence limits

The code snapshot was copied from Jorge's existing local project. Historical live-generation and infrastructure reports were preserved for review; their metrics were not regenerated here. The demo trace verifies indexing/provenance/retrieval mechanics, not real semantic embeddings or LLM answer faithfulness. Auth0 remains unconfigured; production operations and broad retrieval quality gates remain open. Current RAG Recall@5 is below the proposed 0.80 acceptance target.

The three employer descriptions were examined through web tools; City Lit is an available January description with unconfirmed vacancy status. Peter's P1 redirects to a generic error board; Epic extraction was limited; Fan Content Policy fetch failed. These limitations are recorded in the peer review. HTTP status alone is never treated as verification of job requirements or copyright permission.
