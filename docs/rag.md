# Stoic RAG research and architecture

[Review index](../README.md#research-review-index)

## Problem and users

Readers exploring Stoic philosophy need answers traceable to approved translations, rather than plausible unattributed quotations. Students and reflective readers can ask questions, inspect passages and distinguish generated interpretation from the historical text. The product is educational reflection; it does not establish historical consensus or provide clinical treatment.

## Technical sources

Primary sources checked November 15, 2026 through web tools or inspected implementation. Pages with limited extraction are identified.

| Source                                                                                                                     | What it supports                                      | Decision                                                                                                                                     |
| -------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| [Lewis et al., RAG paper](https://arxiv.org/abs/2005.11401)                                                                | Retrieval supplies external evidence to generation    | Ground answers in selected passages; a retrieval score is not a truth score.                                                                 |
| [PostgreSQL full-text search](https://www.postgresql.org/docs/current/textsearch-intro.html)                               | Lexical document queries and linguistic normalization | Comparison source; actual baseline uses in-process BM25, not PostgreSQL FTS.                                                                 |
| [Sentence Transformers similarity](https://www.sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html) | Embeddings and similarity support semantic matching   | Local model alternative; existing app has demo hash vectors and hosted semantic embeddings. Hash vectors are not equivalent semantic models. |
| [Qdrant search](https://qdrant.tech/documentation/concepts/search/)                                                        | Vector retrieval API                                  | Existing Qdrant code and tests inspected; web page redirected with no extracted body, so do not claim full documentation reading.            |
| [pgvector](https://github.com/pgvector/pgvector)                                                                           | PostgreSQL vector extension alternative               | Could consolidate services; unnecessary migration for the existing app.                                                                      |
| [Neo4j graph concepts](https://neo4j.com/docs/getting-started/graph-database/)                                             | Dedicated property graph model                        | Compare for explicit relationships; no dedicated graph database is implemented.                                                              |
| [SQLite FTS5](https://www.sqlite.org/fts5.html) and [sqlite-vec](https://github.com/asg017/sqlite-vec)                     | Small single-file lexical/vector alternatives         | Relevant to Peter's budget; not the Stoic application's current vector engine.                                                               |

## Eight concepts in this project

| Concept                            | Meaning and concrete use                                                                                                                                                                                                                                                       |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| RAG                                | Retrieve external passages before generation; selected approved text becomes evidence for the answer, rather than relying on model memory.                                                                                                                                     |
| Embeddings and semantic similarity | A model maps text to numeric vectors; cosine similarity ranks related wording. Index and query must use the same model/dimensions. Demo hash vectors test mechanics, not semantic quality.                                                                                     |
| Vector database                    | Qdrant indexes child embeddings and metadata to find nearby vectors and filter sources; canonical quotations remain in SQL.                                                                                                                                                    |
| Graph database                     | Stores entities as nodes and explicit relationships as edges, with properties and traversal queries. Neo4j is a researched alternative, not installed here.                                                                                                                    |
| Entities and relationships         | Epictetus → authored → Encheiridion → translated by → George Long; this approved edition → contains → section XXV; child → belongs to → parent. These are source/provenance facts. A “theme resembles another theme” edge would require a separately supported interpretation. |
| Document ingestion/import          | Allowlist approved registry entries, verify downloaded snapshot hashes, parse source units, persist stable parents/children and offsets, embed children, and upsert vectors. Blocked editions cannot enter the index.                                                          |
| Chunking                           | Divide long sources into retrievable spans while preserving their parent and edition context. Exact offsets let the system recover text without generating quotations.                                                                                                         |
| Retrieval evaluation               | Compare returned IDs with frozen expected passages using Recall@k/MRR, then separately review citation correctness, answer support, abstention, latency and cost. Similarity scores are not accuracy.                                                                          |

Definitions are grounded in the primary references above and the linked source implementation. The following tables are AI-assisted engineering comparisons for this existing project, not newly executed benchmarks.

## Database and retrieval alternatives

| Alternative                          | Advantage                                                                                                         | Cost / limitation                                                                             | Decision                                                                                                                               |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Qdrant                               | Dedicated vector search, metadata payload filters, existing working ingestion/retrieval integration.              | Separate service and SQL/vector consistency/backup responsibilities.                          | Keep it: reviewable code and historical runs already exist; migration would not resolve the observed relevance gap.                    |
| PostgreSQL + pgvector                | Vectors and relational source data in one service; SQL filtering/joins with exact or approximate vector indexing. | Requires migration, indexing/query tuning and a new like-for-like evaluation.                 | Credible consolidation option if service overhead becomes the actual constraint; not benchmarked here.                                 |
| Vector database                      | Rank passages by numeric semantic proximity, useful for modern descriptions of old philosophical ideas.           | Does not establish factual relationships or explain multi-hop reasoning.                      | Use for candidate retrieval; verify source provenance separately in SQL.                                                               |
| Graph database                       | Traverse explicit author/work/theme/argument relationships with edge provenance.                                  | Requires curated edges, schema/query design and another operational system.                   | Current author/work/edition hierarchy is shallow and SQL already resolves it.                                                          |
| Vector retrieval with SQL provenance | Dense candidates expand to approved full passages and their source records.                                       | May miss relationships that are not expressed in passage wording.                             | Current design; “vector-only” here means no graph retrieval, not an absence of SQL metadata.                                           |
| Vector + graph retrieval             | Could traverse curated argument/theme links after vector seeding and retrieve related evidence.                   | Additional edge-quality, traversal and answer-support evaluation; inferred edges can mislead. | Proposed only. Add only if a held-out multi-hop question set demonstrates a benefit sufficient to justify curation and infrastructure. |

See [pgvector's official capabilities](https://github.com/pgvector/pgvector), [Qdrant search](https://qdrant.tech/documentation/concepts/search/), and [Neo4j's graph model](https://neo4j.com/docs/getting-started/graph-database/). No speed, cost or quality win between these databases was measured in this review.

## Chunking alternatives

| Technique                    | Benefit                                                                                                                         | Risk                                                                              | Existing-project decision                                                                                                                               |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fixed-size                   | Simple bounded baseline with predictable embedding sizes.                                                                       | Can split an argument or citation context arbitrarily.                            | Keep as a measured comparator; historical fixed/dense Recall@5 was slightly higher, so do not claim structure wins on recall.                           |
| Recursive                    | Split at paragraph/sentence boundaries, falling back to smaller spans when necessary.                                           | Text boundaries alone do not preserve edition/book/letter identity.               | Existing selectable strategy; the current implementation shares boundary logic with structure splitting. It is not an independently superior algorithm. |
| Structure-aware parent/child | Parse edition-specific books, sections, letters or headings as parents; embed bounded children and restore full parent context. | More parser/edition maintenance; overly broad parents may add irrelevant context. | Keep for provenance and readable quotations. Children target 280 tokens with bounded fallback; stored offsets preserve exact source text.               |

The [chunking implementation](../projects/stoic-companion/backend/app/chunking.py) and [chunking decision](../projects/stoic-companion/docs/CHUNKING.md) distinguish the code and historical comparison. Parent-child structure is a provenance choice with a measurable retrieval tradeoff.

## Retrieval comparison

| Strategy                       | Strength                                                                | Failure mode                                                                   | Stoic decision                                                                                                                 |
| ------------------------------ | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| Keyword / BM25                 | Exact names, rare words and transparent lexical baseline                | Modern paraphrases may not share vocabulary with old translations              | Implemented rank-bm25 baseline. Evaluate keyword-only alongside dense on frozen questions.                                     |
| Vector similarity              | Semantic paraphrases such as anxiety versus desire/fear                 | Similarity can retrieve an adjacent idea or unsupported claim; weak for counts | Implemented Qdrant cosine retrieval. Preferred live configuration is dense with reranking off, based on prior local benchmark. |
| Structured relationship lookup | Exact author→work→edition→passage provenance and filters                | Metadata cannot answer an unencoded philosophical relationship                 | Implemented SQL joins for provenance. Curated theme relationships remain a future option.                                      |
| Hybrid                         | Combines lexical and semantic candidates through reciprocal rank fusion | Fusion can demote useful dense hits; it adds latency and tuning                | Implemented optional mode, not assumed superior. Prior benchmark shows lower recall; retain as an experimental comparator.     |

The [historical November 12 report](../projects/stoic-companion/docs/RETRIEVAL_EVALUATION.md) records fixed/dense Recall@5 0.450, structure/dense 0.433, structure/hybrid 0.350 and hybrid plus lexical rerank 0.250 on 30 scenarios. These are existing artifacts, not rerun semantic results in this review. All five configurations had valid final quotation/source cards in their sampled outputs; this does not prove prose faithfulness. Only three real GPT generations per configuration were sampled. Keyword-only needs its own directly comparable measured run before claiming a win over it.

## Recommended architecture

```text
Approved registry + checksum-verified raw snapshots
  → parsers → preserved SQL parents + bounded children/offsets
  → model-specific embeddings → Qdrant vectors with source payload
Question + bounded conversational context
  → dense retrieval (optional BM25 / fusion experiment)
  → parent expansion + edition/author metadata
  → structured generated interpretation
  → validate selected IDs against retrieved evidence
  → attach verbatim stored passage + edition + section + source URL
  → Next.js citation cards and original context
```

Canonical source data is SQL plus versioned raw snapshots, not vectors. [Manifest](../projects/stoic-companion/corpus/sources.json) records edition, translator, checksum and approval status. Six approved entries cover Casaubon Meditations, Long Encheiridion and Discourses selections, and Gummere Letters 1/13/63. Higginson editorial edition and Shortness of Life remain blocked. Original notices are retained. [Source rights](../projects/stoic-companion/docs/SOURCES_AND_LICENSES.md) record territorial limits; do not expand distribution based solely on this research record.

Ingestion verifies snapshot hashes before parsing, separates Gutenberg framing from source bodies, uses stable passage IDs and deterministic vector IDs, and rejects changed parser signatures. Sentence/structure-aware children target 280 tokens while retaining parent offsets; oversized segments get bounded fallback splitting. Embedding model and namespace must agree at query/index time. Demo word-hash vectors support free offline tests; historical real inference uses 1,536-dimensional text-embedding-3-small. PostgreSQL is the Compose canonical store, SQLite the native test/demo store, Qdrant the vector index.

**Graph value:** author/work/edition/passages are shallow relationships handled clearly by SQL. A dedicated Neo4j graph could help a future curated network of arguments, themes and explicitly sourced cross-references, but automatic thematic edges would add interpretation and provenance risk. There is no demonstrated need for arbitrary deep traversal now. Ordinary SQL tables are not a dedicated graph database. The supplied November 17 assignment explicitly asks for comparison without adding a graph merely for the requirement.

Grounded generation validates a structured answer, rejects invented passage IDs and attaches exact stored quotations. The backend validates quotes against parent text. Citations carry translation and section, not guessed original chapter mappings. Prompt instructions alone cannot guarantee abstention or semantic correctness; evaluate those separately.

## Access, security and cost

Implemented source includes Auth0 RS256 verification, issuer/audience/expiry checks, ownership checks, admin import protection, rate limits and per-process budget logic. Actual Auth0 tenant login remains unconfigured. Local guest cookies are random bearer credentials with hashes/expiry; a demo session is not production identity. Imported text is untrusted prompt data. Keep provider keys server-side, sanitize errors, bound inputs, use approved-source allowlists and enforce object ownership. Public multi-worker hosting requires distributed reservations, retention policy and operational monitoring. No new billable inference or deployment is authorized by a free verification run.

Choose local offline operation for this checkpoint: zero new API or hosting spend. Existing Compose supports Docker in Ubuntu WSL2 with PostgreSQL/Qdrant/FastAPI/Next.js; November 12 runtime reports are historical, not a current service-health check. The FastAPI generator calls OpenAI Responses; the Next.js UI consumes its conversation/citation stream. No public Stoic site exists. The $10/month configuration is a planned application guard, not a provider billing guarantee; recorded per-token rates are estimates and must be checked before future paid use. A local provider-free demo suffices for reproducible QA. The original 909-child and live-generation reports are historical local evidence, not production verification.
