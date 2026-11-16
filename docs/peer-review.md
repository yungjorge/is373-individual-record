# AI-assisted review of Peter Balasis

[Review index](../README.md#research-review-index)

Reviewer: Jorge Sanchez, AI-assisted peer review. Prepared November 15, 2026. Jorge's personal confirmation is pending; automated observations below must not be attributed to a completed human walkthrough.

Scope: [pb392/is373-individual-record](https://github.com/pb392/is373-individual-record), commit [`378ce760`](https://github.com/pb392/is373-individual-record/tree/378ce760face9e46d515e0a37f13b952770d20f7). Read the README review index first, followed its career and RAG sequence, then inspected both S3 notes and related repository code. This is a planning record: illustrative retrieval and expected answers are not implemented-feature test results.

## Career question 1 — trace one portfolio decision

Decision: put an evidence-first project card for the CI/CD pipeline on the portfolio. P2, the [Epic Content Architecture tools internship](https://www.epicgames.com/site/careers/jobs/6200355004?lang=en-US), is described in README §1.1 as building tools for content packaging/distribution and resolving internal workflow bugs. Peter maps that to [is373_ci_cd](https://github.com/pb392/is373_ci_cd), where the inspected [CI workflow](https://github.com/pb392/is373_ci_cd/blob/main/.github/workflows/ci.yml) builds/tests/publishes/deploys and uses browser checks. That supports release discipline and developer workflow skills. The mapping is **partial** for the specific C++/Unreal tools responsibility: Python/Docker deployment does not demonstrate engine-tool implementation. The README already admits that limit, which is a strength. Source inspection supports the mechanism; this review did not rerun his CI or certify the hosted environment.

## Career question 2 — employer facts versus hypotheses

README §1.1 labels employer responsibilities as paraphrases and gives source links, eligibility and dates. §1.3 explicitly labels the belief that a studio values student service/pipeline work as a hypothesis; §1.5 similarly labels evidence-first recruiter scanning as unmeasured. These distinctions are unusually clear. The responsibility map's “observed in CI + hosted” remains Peter's dated claim until linked runs/host are independently checked. Employer postings change: the P1 link redirected to the general 2K board with `error=true` during this review; the former associate listing could not be reconfirmed. Epic P2 returned no readable body and P3 could not be fetched through the web tool. Retain the dated research, mark current verification status and save a permissible short factual summary/job ID rather than asserting all are still open.

## Career question 3 — is the services/tools direction realistic?

Yes as a provisional adjacent direction, with a substantial C++ condition. Both selected Epic examples and the gameplay example emphasize C++. Existing CI/CD code demonstrates testing/release skills; [my-app-studio](https://github.com/pb392/my-app-studio) contains account/auth/role infrastructure, SQL role storage and server feature routers. Those are transferable service/security concepts. They do not establish Peter's authorship of every template feature or C++ competence. README §1.3 candidly corrects the initial assumption that tools work would mainly mean Python/CI. Keep “student building game services and tools” positioning, describe transferable evidence accurately, and add a small C++ tool with reproducible tests. A Unity/C# prototype alone would not close Epic's explicit C++ gap. Confirm P2's location before grouping all postings as known in-person locations: the table itself says its location is not stated.

## RAG question 4 — trace S3-note-01

Original: [meta note](https://github.com/pb392/is373-individual-record/blob/378ce760face9e46d515e0a37f13b952770d20f7/docs/notes/S3-note-01-meta-overview.md), written November 13 about the November 7–8 Columbus Open. Its metadata explicitly says S2 results were not yet posted and the content is Peter's own knowledge. README §2.6 splits it into `#1` played archetypes, `#2` topping/winner and `#3` boss analysis. Query “Who won the last big tournament?” hypothetically retrieves `#2`; SQL lookup Fish→TOPPED_AT{1st}→T-COLUMBUS-OPEN agrees; proposed answer cites S3-note-01. [S3-note-02](https://github.com/pb392/is373-individual-record/blob/378ce760face9e46d515e0a37f13b952770d20f7/docs/notes/S3-note-02-archetype-bosses.md) separately supports Hades Sloth and Dio Duggy→Neandersloth relationships.

The conceptual trace is understandable, but not yet reproducible as an executed pipeline. No chunking/import code, SQL schema, embedding model, fixture or actual retrieval scores exist in this record. That is appropriate to Plan when clearly labeled. More importantly, note 01's list order is converted into `popularity_rank=1` without numeric counts or a ranking method. Treat it as a provisional author claim or remove the numeric rank until evidence exists. Agreement between a chunk and a row extracted from the same note is not independent corroboration. Cite the note as author knowledge, with missing external verification visible. Add exact chunk text/version/offsets and a small SQL fixture at Build so another reader can reproduce the same trace.

## RAG question 5 — missing or stale evidence

| Failure                                                     | Current protection                                   | Missing observable check                                                                                                                                   |
| ----------------------------------------------------------- | ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| “Last tournament” remains Columbus after a newer event      | README §2.6 explicitly recognizes dates/recency      | Insert newer event; answer must cite that event or say newest known/imported, with coverage date. Dates alone do not prove all recent events are imported. |
| S2 decklist absent                                          | Source manifest and next steps admit missing results | Count question must abstain; unknown quantity must never become zero or be inferred from archetype.                                                        |
| No S1/S2 import                                             | Q5 tests unrelated absent ban-list evidence          | Empty-corpus and source-specific missing-import tests; Q5 alone does not exercise a missing known source.                                                  |
| Source conflict or correction                               | Row source IDs are planned                           | Two disagreeing dated assertions must retain both provenance records and disclose conflict; no silent winner overwrite.                                    |
| Unsupported popularity rank and subjective “hardest” bosses | S3 notes identify own knowledge                      | Separate measured placements/counts from opinion; Q7 must attribute “hardest” to the note and avoid universal factual claims.                              |

Q1–Q8 and §2.8 cover useful facts, paraphrase, relations, missing evidence, links, idempotence and authorization. They omit explicit stale/conflicting/missing-decklist scenarios. Q3 “most” requires a declared population/denominator, and Q4's `[card]` placeholder needs a specific imported card/quantity. Complete expected answers before claiming a measured evaluation. The official Worlds page was reachable and identifies Mike Thomas/Trishula and a Celestleo decklist; that supports Worlds, not Columbus. TopElestrals tournament page was reachable, but this review did not independently establish Columbus results or counts.

## RAG question 6 — why hybrid?

The architecture fits two distinct data shapes. Keyword FTS5 is a transparent baseline for exact card names; vector search can connect paraphrases to strategy notes; SQL joins give exact deck/card quantities, shared cards and archetype/boss relationships. SQL is a sensible lightweight representation of a shallow graph-shaped domain, and the README correctly distinguishes it from Neo4j. Vectors alone cannot reliably count deck cards. Keyword-only may miss aliases such as Dio/Dionysus unless normalized.

Reliability remains conditional on imported source completeness, canonical aliases, permission scope, dates and conflict handling. Add an `archetype_bosses` relation to the listed schema: the trace uses Boss and USES_BOSS, but §2.5's table list mentions only Tournament/Deck/Archetype/Card/Element/deck_cards. Store provenance on relationship assertions, not merely entity rows. Run keyword-only, vector-only and combined modes against the same frozen questions, reporting exact counts and full expected relationship sets. The 1 GB constraint gives a reasonable planning rationale for SQLite and hosted embeddings; actual capacity and API pricing still need measurement. Hybrid is justified as a hypothesis by query types, not proven superior by the illustrative trace.

## Additional observations and strengths

Strengths: review index gives a clear route; status vocabulary prevents fake test claims; C++ gap is explicit; Neo4j is not confused with SQL; source permissions and host limits are surfaced; S3 notes carry authorship/date/unofficial notices.

Navigation: local note links resolve. One giant README is readable for Plan, but exact heading links and compact cross-links back from notes would improve review. Permissions are self-reported; `docs/permissions/` is a planned path, not an existing evidence directory. Do not publish personal DMs; preserve redacted scope/date/owner confirmation when available. Fan Content Policy could not be re-fetched by the web tool (redirect/fetch error), so its detailed interpretation remains unconfirmed here. The AI disclosure leaves the Fan Policy box unchecked while §2.4 says read; reconcile the record. Likewise use one accurate source for eligibility rather than implying P2 location is confirmed. No running RAG site or accessibility result was invented.

## Published feedback

The highest-value issue asks for provenance and stale/missing/conflicting-evidence acceptance cases. Exact published URL and verification are recorded in [the exchange log](review-exchange.md). No partner files were edited and no partner issue was closed. Smaller posting/disclosure/schema observations remain here to avoid flooding Peter with overlapping issues.

## Personal confirmation required

Jorge should open the issue and cited passages, confirm that the feedback matches his understanding, and perform his own uncoached walkthrough. Peter must supply his actual review of Jorge's work. Neither action is claimed by this AI-assisted record.
