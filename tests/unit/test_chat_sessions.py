"""Persistencia isolada das conversas do Pergunte as IAs."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from copamind.api.routes.chat import _CHAT_MODEL_GROUPS
from copamind.data.repositories import DuckDBRepository


def test_chat_session_memory_and_reset_are_isolated(seeded_repo: DuckDBRepository) -> None:
    now = datetime.now(UTC)
    before_matches = seeded_repo.count("matches")
    seeded_repo.create_chat_session("chat:test", now)
    seeded_repo.insert_chat_message(
        message_id="msg:q", session_id="chat:test", batch_id="batch:1",
        role="user", content="Quem e favorito?", status="completed", created_at=now,
        metadata={"use_memory": False},
    )
    seeded_repo.insert_chat_batch(
        "batch:1", "chat:test", "msg:q", ["model-a", "model-b"], False, now
    )
    seeded_repo.update_chat_memory("chat:test", "Resumo compilado", now)

    session = seeded_repo.get_chat_session("chat:test")
    batch = seeded_repo.get_chat_batch("batch:1")
    assert session is not None and session["memory_summary"] == "Resumo compilado"
    assert batch is not None and batch["selected_models"] == ["model-a", "model-b"]
    assert batch["use_memory"] is False

    assert seeded_repo.delete_chat_session("chat:test") == 1
    assert seeded_repo.get_chat_session("chat:test") is None
    assert seeded_repo.count("matches") == before_matches


def test_chat_news_belongs_to_session_and_is_editable(seeded_repo: DuckDBRepository) -> None:
    now = datetime.now(UTC)
    seeded_repo.create_chat_session("chat:news", now)
    seeded_repo.insert_chat_news(
        news_id="news:1", session_id="chat:news", source_url="https://example.com/a",
        source="example.com", title="Original", summary="Resumo", published_at=None,
        entities=["Brasil"], created_at=now,
    )
    seeded_repo.update_chat_news("news:1", "chat:news", "Editado", "Resumo editado")
    news = seeded_repo.list_chat_news("chat:news")
    assert news[0]["title"] == "Editado"
    assert news[0]["summary"] == "Resumo editado"
    assert news[0]["entities"] == ["Brasil"]


def test_chat_session_api_lifecycle_is_independent(data_client: TestClient) -> None:
    created = data_client.post("/chat/sessions")
    assert created.status_code == 201
    session_id = created.json()["session"]["session_id"]

    loaded = data_client.get(f"/chat/sessions/{session_id}")
    assert loaded.status_code == 200
    assert loaded.json()["messages"] == []

    deleted = data_client.delete(f"/chat/sessions/{session_id}")
    assert deleted.status_code == 200
    assert data_client.get(f"/chat/sessions/{session_id}").status_code == 404


def test_all_project_chat_models_have_performance_group() -> None:
    counts: dict[str, int] = {}
    for group_id, _label, _order in _CHAT_MODEL_GROUPS.values():
        counts[group_id] = counts.get(group_id, 0) + 1
    assert counts == {
        "very_slow": 6,
        "large_moe": 7,
        "slow": 3,
        "limit": 2,
        "good": 2,
        "fast": 7,
    }
