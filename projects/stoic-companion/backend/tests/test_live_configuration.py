from unittest.mock import Mock

import pytest
from app.config import Settings, settings
from app.generation import Answer, Explanation


def test_live_generation_with_guest_access_does_not_require_auth0():
    config = Settings(
        _env_file=None,
        demo_mode=True,
        generation_provider="openai",
        embedding_provider="openai",
        openai_api_key="test-only",
    )
    config.validate_runtime()
    assert not config.use_demo_generation


def test_live_generation_without_key_fails_closed():
    config = Settings(_env_file=None, demo_mode=True, generation_provider="openai", openai_api_key="")
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        config.validate_runtime()


def test_guest_access_disabled_still_requires_auth0():
    config = Settings(
        _env_file=None,
        demo_mode=False,
        generation_provider="openai",
        embedding_provider="openai",
        openai_api_key="test-only",
        auth0_domain="",
        auth0_audience="",
    )
    with pytest.raises(ValueError, match="AUTH0_DOMAIN"):
        config.validate_runtime()


def test_local_guest_can_receive_real_provider_result(client, monkeypatch):
    monkeypatch.setattr(settings, "generation_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "test-only")

    def live_result(message, history, evidence):
        pid = evidence[0]["passage_id"]
        return Answer(
            summary="Focus on the action you can influence.",
            selected_passage_ids=[pid],
            explanations=[Explanation(passage_id=pid, interpretation="Examine your judgment of the outcome.")],
            practical_applications=["Write one next step."],
            reflection_question=None,
        ), {"model": "mock-live", "input_tokens": 100, "output_tokens": 30, "estimated_cost": 0.001}

    monkeypatch.setattr("app.main.generate", live_result)
    health = client.get("/api/v1/health").json()
    assert health["demo_mode"] and health["generation_provider"] == "openai"
    cid = client.post("/api/v1/conversations").json()["id"]
    response = client.post(
        f"/api/v1/conversations/{cid}/messages", json={"message": "I worry about events outside my power."}
    )
    assert "event: result" in response.text and '"mode": "openai"' in response.text


def test_server_indexes_repaired_when_collection_already_exists(monkeypatch):
    from app.vectors import VectorStore

    monkeypatch.setattr(settings, "qdrant_url", "http://localhost:6333")
    client = Mock()
    client.collection_exists.return_value = True
    client.get_collection.return_value = Mock(
        payload_schema={"author": Mock()}, config=Mock(params=Mock(vectors=Mock(size=1536)))
    )
    store = VectorStore.__new__(VectorStore)
    store.client = client
    store.collection = "test"
    store.ensure(1536)
    assert client.create_payload_index.call_count == 4
    assert all(call.kwargs["wait"] for call in client.create_payload_index.call_args_list)


def test_benchmark_reference_ids_exist_in_approved_source_units():
    import json

    from app.config import ROOT
    from app.ingestion import download, manifest, units

    known = {
        f"{item['id']}:{reference}"
        for item in manifest()
        if item["ingestion_status"] == "approved"
        for reference, _, _ in units(item, download(item))
    }
    cases = json.loads((ROOT / "eval/questions.json").read_text(encoding="utf8"))
    assert len(cases) >= 30
    assert all(case["acceptable_passages"] for case in cases)
    assert {pid for case in cases for pid in case["acceptable_passages"]} <= known


def test_live_generation_repair_is_bounded_and_accounts_both_calls(monkeypatch):
    from unittest.mock import patch

    from app.generation import GenerationFailure, generate

    monkeypatch.setattr(settings, "generation_provider", "openai")
    evidence = [
        {
            "passage_id": "trusted",
            "quote_text": "Original text.",
            "surrounding_passage": "Original text.",
            "metadata": {},
        }
    ]
    good = Answer(
        summary="Focus on an action you can choose.",
        selected_passage_ids=["trusted"],
        explanations=[Explanation(passage_id="trusted", interpretation="Consider your own judgment.")],
        practical_applications=["Write one next step."],
        reflection_question=None,
    )
    bad = good.model_copy(update={"summary": "Seneca said this is easy."})
    client = Mock()
    client.responses.parse.side_effect = [
        Mock(output_parsed=bad, usage=Mock(input_tokens=100, output_tokens=20)),
        Mock(output_parsed=good, usage=Mock(input_tokens=100, output_tokens=20)),
    ]
    with patch("app.generation.OpenAI", return_value=client):
        answer, usage = generate("What next?", [], evidence)
    assert answer == good and usage["input_tokens"] == 200 and usage["output_tokens"] == 40
    assert client.responses.parse.call_count == 2
    client.responses.parse.side_effect = None
    client.responses.parse.return_value = Mock(output_parsed=bad, usage=Mock(input_tokens=100, output_tokens=20))
    with patch("app.generation.OpenAI", return_value=client), pytest.raises(GenerationFailure) as exc:
        generate("What next?", [], evidence)
    assert exc.value.usage["input_tokens"] == 200
