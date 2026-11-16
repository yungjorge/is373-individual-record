# Worked source-to-answer trace

[Review index](../README.md#research-review-index) · [Architecture](rag.md)

## Concrete source and representation

Original: [Gutenberg 10661](https://www.gutenberg.org/ebooks/10661), George Long's _A Selection from the Discourses of Epictetus with the Encheiridion_. Registry source `enchiridion-long`, passage `enchiridion-long:I`. The [manifest](../projects/stoic-companion/corpus/sources.json) pins checksum `7915eac7442daed1fbc461b8a281ecc315c5e619126d50d914c29c39fa3b2209`. The approved snapshot is in `corpus/snapshots.zip`.

Section I begins: “Of things some are in our power, and others are not.” This short quotation is the supporting source text; generated wording below is interpretation. The [parser](../projects/stoic-companion/backend/app/chunking.py) extracts the section, preserves its text, and records section number 1. Ingestion creates children with exact start/end offsets and deterministic IDs. The executable [trace script](../scripts/worked_trace.py) prints the actual first child and its ID rather than inventing a chunk hash.

## End-to-end example

1. Question: “What can I control according to Epictetus?”
2. Approved snapshot → `enchiridion-long` → parent section `I` → exact child span/hash.
3. Offline mode embeds/indexes the child using demo word hashes in a temporary Qdrant local index. This executes without paid APIs; a semantic run requires the separately configured real embedding provider.
4. Query embedding and retrieval return ranked children; the trace records actual retrieved parent IDs and whether section I was found. The script does not force the expected passage into the retrieved set.
5. If section I is retrieved, it supports the distinction between one's judgments/actions and external circumstances. SQL provenance resolves parent → approved source → Long translation → Gutenberg URL. This is a structured relationship lookup, not graph inference.
6. An illustrative generated answer: “Epictetus distinguishes your own judgments and actions from external conditions; focus reflection on what is yours to choose.” This wording is a planned example, not a claimed live model response.
7. Citation: Epictetus, _Encheiridion_, section I, translated by George Long, [Gutenberg 10661](https://www.gutenberg.org/ebooks/10661). The actual application attaches stored text and source metadata after checking that the chosen ID was retrieved.

Run `python scripts/worked_trace.py` with the application's dependencies installed. Its JSON artifact records executed offline retrieval separately from the illustrative answer. If section I is absent, record a retrieval failure; do not present the example as a successful generated answer. Historical semantic rankings are available in the [raw evaluation](../projects/stoic-companion/eval/live/results.json).
