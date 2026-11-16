import hashlib
import json
import math
import re
import uuid
from importlib.metadata import version
from pathlib import Path

from openai import OpenAI
from qdrant_client import QdrantClient, models

from .chunking import normalize
from .config import settings

STOPWORDS = set(
    "a an the and or of in on at to for from with by as is are was were be been being it its this that these those not no but if then than so do does did have has had can could would should will shall may might must you your yours yourself we our ours us they their them he she his her him me my mine myself who whom what which when where why how all any some each every very more most much such also only own about into up out over under through upon there here am".split()
)


def words(text):
    return [w for w in re.findall(r"[a-z]{2,}", text.lower()) if w not in STOPWORDS]


def expand_query(text):
    """Small editorial vocabulary bridge; appended terms are search aids, never source text."""
    groups = [
        (r"\b(control|anxious|anxiety|worry|worries)\b", "power opinion desire fear"),
        (r"\b(compare|comparing|comparison|worthless|jealous|envy)\b", "better wealth honor envy"),
        (r"\b(promotion|invited|invitation|honor|honors|career)\b", "honour preference supper price"),
        (r"\b(procrastinat\w*|discipline|abandon\w*|goals)\b", "procrastination progress practice undertaking"),
        (r"\b(criticis\w*|insult\w*|anger|temper|revenge)\b", "abuse insult judgment anger"),
        (r"\b(died|dying|grief|lost|loss|death|mortality)\b", "death grief friend loss"),
        (r"\b(approval|praise|validation|like me)\b", "praise please external opinion"),
    ]
    additions = [terms for pattern, terms in groups if re.search(pattern, text, re.I)]
    return text + (" " + " ".join(additions) if additions else "")


def demo_embedding(text):
    """Deterministic signed word hashing, NOT OpenAI or a semantic model."""
    vector = [0.0] * 384
    for word in words(text):
        h = hashlib.sha256(word.encode()).digest()
        vector[int.from_bytes(h[:4], "big") % len(vector)] += 1 if h[4] % 2 else -1
    norm = math.sqrt(sum(x * x for x in vector)) or 1
    return [x / norm for x in vector]


class Embeddings:
    def __init__(self):
        self.model = "demo-hash-v2" if settings.embedding_provider == "demo" else settings.embedding_model
        self.cache = (settings.embedding_cache_dir or settings.data_dir / "embeddings") / self.model.replace("/", "_")
        self.cache.mkdir(parents=True, exist_ok=True)

    def embed(self, texts):
        paths = [self.cache / (hashlib.sha256(normalize(t).encode()).hexdigest() + ".json") for t in texts]
        values = [json.loads(p.read_text()) if p.exists() else None for p in paths]
        missing = [i for i, v in enumerate(values) if v is None]
        for start in range(0, len(missing), 64):
            batch = missing[start : start + 64]
            if settings.embedding_provider == "demo":
                vectors = [demo_embedding(texts[i]) for i in batch]
            else:
                result = OpenAI(api_key=settings.openai_api_key, timeout=60, max_retries=2).embeddings.create(
                    model=self.model, input=[texts[i] for i in batch]
                )
                vectors = [d.embedding for d in sorted(result.data, key=lambda d: d.index)]
                from .db import Session, Usage

                with Session() as db:
                    db.add(
                        Usage(
                            user_id="system:embeddings",
                            model=self.model,
                            input_tokens=result.usage.total_tokens,
                            estimated_cost=result.usage.total_tokens * settings.embedding_usd_per_million / 1e6,
                        )
                    )
                    db.commit()
            for i, v in zip(batch, vectors, strict=True):
                values[i] = v
                temp = paths[i].with_name(paths[i].name + "." + uuid.uuid4().hex + ".tmp")
                temp.write_text(json.dumps(v))
                temp.replace(paths[i])
        if values and (len({len(v) for v in values}) != 1 or not all(math.isfinite(x) for v in values for x in v)):
            raise ValueError("Embedding dimension/value mismatch")
        return values


class VectorStore:
    def __init__(self, path: Path | None = None):
        self.client = (
            QdrantClient(url=settings.qdrant_url, timeout=60)
            if settings.qdrant_url and path is None
            else QdrantClient(
                path=str(path or settings.data_dir / ("qdrant-" + ".".join(version("qdrant-client").split(".")[:2])))
            )
        )
        model = "demo-hash-v2" if settings.embedding_provider == "demo" else settings.embedding_model
        identity = f"{model}:{settings.chunk_strategy}:{settings.corpus_version}"
        if settings.vector_namespace:
            identity += ":" + settings.vector_namespace
        self.collection = "stoic_" + hashlib.sha256(identity.encode()).hexdigest()[:16]

    def ensure(self, dim):
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                self.collection, vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE)
            )
        # Repair missing indexes after an interrupted collection provisioning run.
        if settings.qdrant_url:
            schema = self.client.get_collection(self.collection).payload_schema
            for key in ("author", "work", "document_id", "parent_id", "corpus_version"):
                if key not in schema:
                    self.client.create_payload_index(self.collection, key, models.PayloadSchemaType.KEYWORD, wait=True)
        actual = self.client.get_collection(self.collection).config.params.vectors.size
        if actual != dim:
            raise ValueError(f"Collection dimension {actual} differs from model dimension {dim}")

    def upsert(self, chunks, embeddings):
        if not chunks:
            return
        self.ensure(len(embeddings[0]))
        for start in range(0, len(chunks), 64):
            self.client.upsert(
                self.collection,
                points=[
                    models.PointStruct(
                        id=c.id,
                        vector=v,
                        payload={
                            **c.metadata_json,
                            "chunk_id": c.id,
                            "parent_id": c.parent_id,
                            "quote_text": c.quote_text,
                        },
                    )
                    for c, v in zip(chunks[start : start + 64], embeddings[start : start + 64], strict=True)
                ],
                wait=True,
            )

    def search(self, vector, author=None, work=None, limit=30):
        self.ensure(len(vector))
        conditions = [
            models.FieldCondition(key=k, match=models.MatchValue(value=v))
            for k, v in [("author", author), ("work", work)]
            if v
        ]
        return self.client.query_points(
            self.collection,
            query=vector,
            query_filter=models.Filter(must=conditions) if conditions else None,
            limit=limit,
        ).points

    def close(self):
        self.client.close()
