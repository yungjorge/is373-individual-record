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

- `python scripts/check_docs.py`: 31 Markdown files; all local destinations passed, including heading anchors and the README review index.
- Prettier 3.6.2 formatted the research Markdown; the CI job checks the same files.
- Offline browser suite: **4 Playwright tests passed in 36.0 seconds**, desktop and mobile Chromium. The suite exercises reflections, citations, bookmarks, persistence/deletion, source-library search and author filtering. No paid inference was used. The copied `docs/screenshots/desktop.png` and `mobile.png` were refreshed by this real run; historical live screenshots in `docs/evidence` remain distinct.
- Full offline ingestion: 567 units and 909 children across six approved sources; both blocked candidates were rejected as intended.
- External GET observations: 29 distinct linked URLs checked. Existing portfolio returned HTTP 200. Canvas redirected to NJIT login; Epic P2 returned 403. All other requested URLs returned 200, which does not establish their semantic content or current vacancy status. [Raw observations](checks/external-links.json).
- Secret-pattern scan of the publishable text found no provider/GitHub tokens or private-key blocks. Runtime databases, credentials and dependency directories are excluded from Git.

## GitHub publication and CI

Initial source/research commit [`5a0001f`](https://github.com/yungjorge/is373-individual-record/commit/5a0001f5692aa01f7394d30d6f662a4983bf3ecf) was pushed to `main`. [GitHub Actions run 43797939960](https://github.com/yungjorge/is373-individual-record/actions/runs/43797939960) completed successfully: documentation, backend and frontend jobs all passed, including offline Chromium desktop/mobile tests. The frontend job took 1 minute 46 seconds; backend 35 seconds. This establishes CI-tested status for the preserved source, not production deployment.

A real Chromium browser loaded the public GitHub repository with HTTP 200, found the README title and Research Review Index table, and followed Career research to the intended document/anchor. [Browser observations](checks/github-browser.json) and [actual README capture](checks/github-readme.png) preserve that check. The capture was also visually inspected; no rendering failure was found in the index.

The [verification follow-up PR #1](https://github.com/yungjorge/is373-individual-record/pull/1) pins Ubuntu 24.04 and current action release commit SHAs to remove the initial run's Node 20/moving-runner warnings. Release tags/SHAs were read directly from GitHub's official action repositories. Its GitHub checks and merge timeline provide the final publication status; only merge after successful checks.

No new paid-provider evaluation, Auth0 tenant login, public Stoic deployment or Canvas submission was executed.

## November 17 Review 1 update

The supplied assignment was inspected alongside the existing record, portfolio source, Git history, merged PR #1 and open issues. The existing public record/source snapshot is reused; neither application is rebuilt. [PR #1](https://github.com/yungjorge/is373-individual-record/pull/1) was already merged at `c5c72d0`; its [main-branch CI run 43798707544](https://github.com/yungjorge/is373-individual-record/actions/runs/43798707544) succeeded before this revision. That historical success is not attributed to the new documentation commit.

Fresh checks executed November 17:

| Check                         | Observed result and limit                                                                                                                                                                                                                                                                                                                                                                           |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend regression            | `pytest -q`: **52 passed in 6.41 seconds**, one Starlette/TestClient deprecation warning, using the existing Python environment against the preserved source. Provider-boundary tests use controlled responses; this was not a new paid GPT/embedding run.                                                                                                                                          |
| Isolated source/quote replay  | `python scripts/worked_trace.py` succeeded: Long Encheiridion imported as **52 units / 66 children**, all 66 spans/checksums validated, section I retrieved first using demo vectors. The saved promotion candidate ID maps to section XXV, offsets **0–866**, with exact child/parent span, saved quotation and full surrounding-passage identity checks. [Actual JSON](checks/worked-trace.json). |
| Documentation navigation      | Local file/heading destinations checked with `scripts/check_docs.py`; required README sections, five story rows and source-trace links inspected. Prettier 3.6.2 checks the same research Markdown as CI.                                                                                                                                                                                           |
| Current external availability | At **18:26 UTC / 1:26 PM Eastern**, production and QA portfolio URLs and all three original employer descriptions returned **HTTP 200** with standard TLS verification. [Dated observations](checks/review1-nov17.json). Reachability does not prove hiring status, employer requirements, full UI function or student experience.                                                                  |
| Incoming review               | GitHub issue #2 was genuinely authored by `pb392`, remains open, and requests a four-point plain-language summary. The new README implements that suggestion. Peter's independent comprehension recheck, any follow-up comment and closure remain pending.                                                                                                                                          |
| Assignment and submission     | Exact two headings and five observable stories added to this existing record; ready-to-copy two-section text is in [submission](submission.md#canvas-text-entry). No Canvas submission, deadline extension or on-time completion is claimed.                                                                                                                                                        |

No new browser suite, frontend build, deployment, Docker installation, real Auth0 login or paid-model benchmark was needed for these documentation changes. November 12/15 live/browser/build results above remain historical. This update was prepared after the user-supplied November 17, 1 PM Eastern deadline.

## Reproduction

From repository root run `python scripts/check_docs.py`; with application dependencies installed, run `python scripts/worked_trace.py`. From `projects/stoic-companion`, run `pytest -q` and `ruff check backend`. From its `frontend`, run `npm ci`, `npm run lint`, `npm run build` and the offline Playwright suite after ingesting the approved corpus. CI mirrors these checks with Python 3.12 and Node 22.

## Evidence limits

The code snapshot was copied from Jorge's existing local project. Historical live-generation and infrastructure reports were preserved for review; their metrics were not regenerated here. The demo trace verifies indexing/provenance/retrieval mechanics, not real semantic embeddings or LLM answer faithfulness. Auth0 remains unconfigured; production operations and broad retrieval quality gates remain open. Current RAG Recall@5 is below the proposed 0.80 acceptance target.

The three employer descriptions were examined through web tools; City Lit is an available January description with unconfirmed vacancy status. Peter's P1 redirects to a generic error board; Epic extraction was limited; Fan Content Policy fetch failed. These limitations are recorded in the peer review. HTTP status alone is never treated as verification of job requirements or copyright permission.
