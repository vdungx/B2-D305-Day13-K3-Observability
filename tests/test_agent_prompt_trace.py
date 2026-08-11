from __future__ import annotations

from contextlib import contextmanager

from app import agent as agent_module


class ManagedPrompt:
    version = 3

    def compile(self, **variables: str) -> str:
        return (
            f"Feature={variables['feature']}\n"
            f"Docs={variables['docs']}\n"
            f"Question={variables['message']}"
        )


class RecordingLangfuseClient:
    def __init__(self) -> None:
        self.prompt = ManagedPrompt()
        self.trace_updates: list[dict] = []
        self.span_updates: list[dict] = []
        self.observations: list[RecordingObservation] = []

    def get_prompt(self, name: str, **kwargs):
        return self.prompt

    def update_current_trace(self, **kwargs) -> None:
        self.trace_updates.append(kwargs)

    def update_current_span(self, **kwargs) -> None:
        self.span_updates.append(kwargs)

    @contextmanager
    def start_as_current_observation(self, **kwargs):
        observation = RecordingObservation(kwargs)
        self.observations.append(observation)
        yield observation


class RecordingObservation:
    def __init__(self, creation: dict) -> None:
        self.creation = creation
        self.updates: list[dict] = []

    def update(self, **kwargs) -> None:
        self.updates.append(kwargs)


def test_agent_links_prompt_version_to_trace_and_generation(monkeypatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "test-public-key")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("LANGFUSE_PROMPT_NAME", "day13-chat")
    monkeypatch.setenv("LANGFUSE_PROMPT_LABEL", "production")
    client = RecordingLangfuseClient()
    monkeypatch.setattr(agent_module, "get_langfuse_client", lambda: client)

    agent = agent_module.LabAgent()
    agent_module.LabAgent.run.__wrapped__(
        agent,
        user_id="student-01",
        feature="qa",
        session_id="session-01",
        message="Explain traces",
    )

    trace_update = client.trace_updates[-1]
    trace_metadata = trace_update["metadata"]
    retrieval, generation = client.observations
    assert trace_metadata == {
        "feature": "qa",
        "model": "claude-sonnet-4-5",
        "env": "dev",
        "correlation_id": "unavailable",
        "prompt_name": "day13-chat",
        "prompt_label": "production",
        "prompt_version": "3",
        "prompt_source": "langfuse",
    }
    assert "env:dev" in trace_update["tags"]
    assert retrieval.creation["name"] == "retrieve-context"
    assert retrieval.creation["as_type"] == "retriever"
    assert generation.creation["name"] == "generate-response"
    assert generation.creation["as_type"] == "generation"
    assert generation.creation["model"] == "claude-sonnet-4-5"
    assert generation.creation["prompt"] is client.prompt
    assert generation.creation["metadata"]["prompt_version"] == "3"
    assert generation.updates[-1]["usage_details"]["prompt_tokens"] > 0


def test_agent_masks_pii_in_trace_inputs(monkeypatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "test-public-key")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "test-secret-key")
    client = RecordingLangfuseClient()
    monkeypatch.setattr(agent_module, "get_langfuse_client", lambda: client)

    agent = agent_module.LabAgent()
    agent_module.LabAgent.run.__wrapped__(
        agent,
        user_id="student-01",
        feature="qa",
        session_id="session-01",
        message="Email me at student@vinuni.edu.vn",
        correlation_id="req-12345678",
    )

    serialized_trace_data = repr(
        {
            "span_updates": client.span_updates,
            "observations": [
                {"creation": item.creation, "updates": item.updates}
                for item in client.observations
            ],
        }
    )
    assert "student@vinuni.edu.vn" not in serialized_trace_data
    assert "REDACTED_EMAIL" in serialized_trace_data
