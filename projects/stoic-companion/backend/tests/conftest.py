import os
import tempfile
from pathlib import Path

TEST_ROOT = Path(tempfile.mkdtemp(prefix="stoic-tests-"))
os.environ["DATA_DIR"] = str(TEST_ROOT)
os.environ["DATABASE_URL"] = "sqlite:///" + str(TEST_ROOT / "test.db")
os.environ["DEMO_MODE"] = "true"
os.environ["EMBEDDING_PROVIDER"] = "demo"
os.environ["GENERATION_PROVIDER"] = "auto"
os.environ["CORPUS_VERSION"] = "v1"
os.environ["VECTOR_NAMESPACE"] = ""
os.environ["EMBEDDING_CACHE_DIR"] = str(TEST_ROOT / "embeddings")
os.environ["QDRANT_URL"] = ""

import pytest  # noqa: E402
from app.db import init_db  # noqa: E402
from app.ingestion import ingest, manifest  # noqa: E402
from app.vectors import VectorStore  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def seed():
    init_db()
    store = VectorStore()
    for item in manifest():
        if item["id"] in ("enchiridion-long", "letters-gummere-13"):
            ingest(item, store)
    store.close()
    yield


@pytest.fixture()
def client(seed):
    from app.main import app
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        c.post("/api/v1/demo-session")
        yield c
