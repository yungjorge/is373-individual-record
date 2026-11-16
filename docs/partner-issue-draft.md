# Add provenance and freshness cases to the planned RAG acceptance checks

**Reviewer:** Jorge Sanchez, AI-assisted peer review. Personal walkthrough confirmation remains pending; these findings come from repository inspection.

**Observation:** The Plan clearly labels the trace as illustrative and recognizes stale “last event” evidence. However, the five acceptance checks in §2.8 do not test recency, missing decklists or conflicting sources. The §2.6 `popularity_rank=1` example also converts the order of an own-knowledge note into a numeric relationship without counts or a documented ranking basis.

**Evidence:** Reviewed commit `378ce760face9e46d515e0a37f13b952770d20f7`:

- [README §2.6, lines 149–170](https://github.com/pb392/is373-individual-record/blob/378ce760face9e46d515e0a37f13b952770d20f7/README.md#L149-L170): `PLAYED_AT{popularity_rank}` and the Fish→Columbus answer, followed by the recency warning.
- [S3-note-01](https://github.com/pb392/is373-individual-record/blob/378ce760face9e46d515e0a37f13b952770d20f7/docs/notes/S3-note-01-meta-overview.md): metadata states the results rely on your knowledge and S2 had not yet posted them. This is useful context, but does not independently establish measured popularity.
- [README §2.7–2.8, lines 174–192](https://github.com/pb392/is373-individual-record/blob/378ce760face9e46d515e0a37f13b952770d20f7/README.md#L174-L192): Q5 tests an absent ban list; the checks do not cover an unavailable decklist, an empty import, a newer event or conflicting assertions about the same result.

**Why it matters:** A chunk and structured row extracted from the same note can agree while repeating one unverified assertion. Selecting the newest imported date can still answer incorrectly if a newer event has not been imported. These are design risks to cover before Build, not failed tests of an unbuilt application.

**Recommended improvement:** Add a compact assertion/provenance example with source ID, source version, event date, imported/checked date and verification status. Keep author analysis distinct from externally confirmed results. Remove the numeric popularity rank or label its basis and provisional status. Expand the planned acceptance table with fixture inputs and expected answer/citation behavior for stale, missing and conflicting evidence.

**Acceptance criteria:**

- [ ] Every sample placement/rank/quantity identifies its supporting source and whether it is author knowledge, externally verified or unknown; unsupported popularity ranks are removed or explicitly provisional.
- [ ] A planned test with Columbus plus a newer event requires the latest supported answer and an “as of / latest imported” coverage date.
- [ ] A planned empty-source or missing-decklist case requires explicit insufficient evidence; an unknown card quantity is not returned as zero.
- [ ] A planned conflicting-source case preserves both source/version citations and discloses disagreement or a documented precedence rule.
- [ ] These remain marked planned until execution, and the documented fixtures/expected outputs let another reviewer reproduce them at Build.

**Positive feedback:** The review index, explicit Plan status, C++ gap and lightweight SQL/vector decision make the project easy to assess honestly. The existing recency warning is exactly the right insight to turn into a verifiable acceptance case.
