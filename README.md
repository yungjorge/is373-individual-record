# IS373 Individual Record — Jorge Sanchez

NJIT UCID **jrs239** · B.S. Web & Information Systems · Review 1 — Plan.

## Start here

My selected career direction is business systems and enterprise applications: connecting business needs with useful automation, integrations and reporting. The portfolio is aimed at an enterprise applications hiring manager. Stoic Companion lets readers describe a difficult situation and explore guidance supported by passages from approved Stoic translations.

The main decisions are an evidence-first portfolio layout and keeping the existing Qdrant retrieval system with structure-aware chunks that link back to complete passages. A graph database has no demonstrated benefit for the current shallow source relationships. Still unfinished: stronger retrieval results, independent review of generated interpretations, a configured Auth0 tenant, and public Stoic hosting. The app has historical local live-model evidence and free regression checks; it has no public deployment.

# 1. Portfolio + career research

**Decision:** target business systems / enterprise applications engineering. BI/data analytics engineering is the adjacent alternative. The choice fits the supplied analyst background and employer demand for integrations, automation and maintainable applications; it is a student/AI interpretation, not an employer endorsement or proof of eligibility.

- [Three original employer postings, responsibilities, qualifications and technologies](docs/career.md#original-employer-postings): Version 1, City Lit and Amazon MGM Studios. City Lit is a historical January job description; a current vacancy is unconfirmed.
- [Two career directions, selection rationale and target reader](docs/career.md#career-comparison).
- [Employer responsibility → specific project evidence and skill gaps](docs/evidence.md). Professional experience is owner-supplied; public code and tests are separately inspectable.
- [Audience, featured work, page outline, two layouts and layout decision](docs/portfolio.md). Select evidence-first now; a professional workflow case needs disclosure permission.
- Existing [portfolio website](https://104-248-208-29.nip.io) and [portfolio repository](https://github.com/yungjorge/is373-practical-test). Current reachability and historical deployment evidence are distinguished in [verification](docs/verification.md).

**Next:** personally confirm employment/degree wording and job eligibility, obtain permission for a sanitized business case, and test whether a new reader can identify the audience and find one responsibility-to-artifact link.

# 2. RAG app + technical research

**Stoic Companion:** a Next.js/FastAPI conversational application with approved Marcus Aurelius, Epictetus and Seneca translations. PostgreSQL stores canonical text in Compose, Qdrant stores embeddings, and OpenAI provides real embeddings and Responses generation when configured. The free offline mode is separately labeled. [Reviewable existing source](projects/stoic-companion/README.md) is preserved here; the original project is not rebuilt.

- [Eight concepts, alternatives, architecture, authentication and resource limits](docs/rag.md). Keep Qdrant and structure-aware parent/child chunks; retain dense retrieval as the current measured baseline. Graph retrieval remains a researched alternative.
- [Approved source registry](projects/stoic-companion/corpus/sources.json) and [translations, original URLs, rights and import policy](projects/stoic-companion/docs/SOURCES_AND_LICENSES.md).
- [Complete source-to-answer trace](docs/trace.md#historical-promotion-question): the saved real promotion conversation is historical November 12 evidence; the isolated free trace is a separate reproducible check.
- [Five observable user stories](docs/evaluation.md#five-observable-user-stories), each with persona, function, value and acceptance criteria; [retrieval evaluation and outstanding gates](docs/evaluation.md#acceptance-gates).
- [Actual checks and limitations](docs/verification.md), [AI disclosure](docs/ai-disclosure.md), and [ready-to-copy Canvas entry](docs/submission.md#canvas-text-entry).

**Next:** improve and independently evaluate retrieval and prose support, test insufficient-evidence behavior with reviewed real outputs, configure Auth0 before member deployment, and test the summary with a new reader. No graph implementation or paid rerun is needed for this Plan record.

## Research Review Index

| Read in order                                | Evidence                                                                                                                                 |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Requirements and deadline limits             | [Checklist and discovery](docs/requirements.md)                                                                                          |
| Three original employer postings             | [Career research](docs/career.md#original-employer-postings)                                                                             |
| Two career directions and target reader      | [Career comparison](docs/career.md#career-comparison)                                                                                    |
| Responsibilities, evidence and skill gaps    | [Project evidence](docs/evidence.md)                                                                                                     |
| Two portfolio layouts, selection and content | [Portfolio direction](docs/portfolio.md)                                                                                                 |
| Primary technical references                 | [Technical sources](docs/rag.md#technical-sources)                                                                                       |
| RAG architecture and retrieval comparison    | [RAG research](docs/rag.md)                                                                                                              |
| Approved editions and blocked candidates     | [Source manifest](projects/stoic-companion/corpus/sources.json) · [Rights record](projects/stoic-companion/docs/SOURCES_AND_LICENSES.md) |
| Source → chunk → answer → citation           | [Worked retrieval trace](docs/trace.md)                                                                                                  |
| Evaluation questions and acceptance criteria | [Evaluation](docs/evaluation.md)                                                                                                         |
| Actual checks and limitations                | [Verification results](docs/verification.md)                                                                                             |
| AI use and personal verification             | [Disclosure](docs/ai-disclosure.md)                                                                                                      |
| Submission and outstanding work              | [Submission checklist](docs/submission.md)                                                                                               |

**Assignment:** Review 1 - Plan - Individual Portfolio + Individual RAG App; 100 points; one Canvas text entry with the two sections above. The user supplied November 17, 2026, 1:00 PM Eastern as the deadline. This update was prepared after that time and is not backdated. Canvas submission is still the student's action.

**Status vocabulary:** planned; implemented (source inspected); locally tested (executed and dated); CI-tested (linked successful run); production-verified (dated hosted evidence). Historical November 12/15 checks are not November 17 reruns. No public Stoic deployment or human validation of AI findings is claimed.
