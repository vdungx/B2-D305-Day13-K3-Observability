from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import logging_config
from app.incidents import disable, enable
from app.main import app


def _chat_payload(*, user_id: str = "student-01", session_id: str = "session-01") -> dict:
    return {
        "user_id": user_id,
        "session_id": session_id,
        "feature": "qa",
        "message": "Explain observability",
    }


def test_chat_propagates_supplied_correlation_id_and_enriches_logs(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json=_chat_payload(),
            headers={"x-request-id": "req-client01"},
        )

    assert response.status_code == 200
    assert response.json()["correlation_id"] == "req-client01"
    assert response.headers["x-request-id"] == "req-client01"
    assert re.fullmatch(r"\d+\.\d", response.headers["x-response-time-ms"])

    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    request_event = next(event for event in events if event["event"] == "request_received")
    assert request_event["correlation_id"] == "req-client01"
    assert request_event["user_id_hash"]
    assert request_event["session_id"] == "session-01"
    assert request_event["feature"] == "qa"
    assert request_event["model"] == "claude-sonnet-4-5"
    assert request_event["env"] == "dev"


def test_middleware_generates_id_and_keeps_it_on_failed_chat_response(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)
    enable("tool_fail")
    try:
        with TestClient(app) as client:
            response = client.post("/chat", json=_chat_payload())
    finally:
        disable("tool_fail")

    assert response.status_code == 500
    assert re.fullmatch(r"req-[0-9a-f]{8}", response.headers["x-request-id"])
    assert re.fullmatch(r"\d+\.\d", response.headers["x-response-time-ms"])
