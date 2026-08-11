from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio

MESSAGE = "Explain why metrics traces and logs work together"


def send(client, agent_module, label: str, session_id: str) -> None:
    os.environ["LANGFUSE_PROMPT_LABEL"] = label
    payload = {
        "user_id": "u_prompt_demo",
        "session_id": session_id,
        "feature": "qa",
        "message": MESSAGE,
    }
    r = client.post("/chat", json=payload)
    print(f"[{r.status_code}] label={label} session={session_id} correlation_id={r.json().get('correlation_id')}")


def main() -> None:
    configure_utf8_stdio()
    load_dotenv(REPO_ROOT / ".env")

    from fastapi.testclient import TestClient

    from app.main import app
    from app import agent as agent_module

    with TestClient(app) as client:
        send(client, agent_module, "baseline", "s_prompt_baseline")
        send(client, agent_module, "candidate", "s_prompt_candidate")

    os.environ["LANGFUSE_PROMPT_LABEL"] = "production"


if __name__ == "__main__":
    main()
