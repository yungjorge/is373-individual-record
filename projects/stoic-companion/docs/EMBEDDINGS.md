# Embeddings and cost

Live mode uses the OpenAI Python SDK and defaults to `text-embedding-3-small`. The vector dimension is measured from the actual embedding response, and an existing Qdrant collection must agree. The code never assumes 1,536 dimensions. Model and chunk strategy contribute to the collection namespace. Do not reuse a SQL corpus under a different chunk signature.

Texts are whitespace-normalized for search and SHA-256 keyed under a model-specific disk cache. Only misses are sent in batches of 64; repeat ingestion still upserts deterministic points but does not repeat provider embedding calls. Cached vectors are checked for consistent dimensions and finite values. A model version change should get a new explicit model/cache namespace.

The credential-free provider is `demo-hash-v2`: signed SHA-256 word hashing into a normalized 384-dimensional vector, with a versioned English stopword filter. It is deterministic, cheap and useful for functional tests; it is **not** a trained semantic embedding model and should not be used to assess OpenAI retrieval quality. A production-mode startup rejects demo embeddings.

Embedding and generation usage records contain model, tokens and estimated cost, never credentials. Price multipliers are configurable estimates, not a current-price guarantee. The local monthly guard includes recorded embedding usage, uses a conservative generation reserve, and serializes generation within one worker. Offline calls record zero API cost. Use provider account-level controls as the authoritative cap. Query embeddings may incur a small charge before the generation budget guard; ingestion is deliberately an operator-managed cost. See deployment limits before scaling.
