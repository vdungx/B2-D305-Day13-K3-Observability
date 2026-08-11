from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio
from app.pii import PII_PATTERNS
from app.tracing import get_langfuse_client, tracing_enabled


def _type_name(observation: object) -> str:
    return str(getattr(observation, "type", "unknown")).split(".")[-1].upper()


def main() -> int:
    configure_utf8_stdio()
    load_dotenv(REPO_ROOT / ".env")

    parser = argparse.ArgumentParser(
        description="Audit một Langfuse trace mà không in input, output hoặc secrets."
    )
    parser.add_argument("--session-id", required=True)
    args = parser.parse_args()

    if not tracing_enabled():
        print("KHÔNG HỢP LỆ: Langfuse credentials chưa được cấu hình.")
        return 1

    client = get_langfuse_client()
    traces = client.api.trace.list(session_id=args.session_id, limit=10).data
    if not traces:
        print(f"KHÔNG HỢP LỆ: Không tìm thấy trace cho session {args.session_id}.")
        return 1

    trace = max(traces, key=lambda item: item.timestamp)
    observations = client.api.observations.get_many(
        trace_id=trace.id,
        limit=50,
    ).data
    # Scan user-controlled trace payloads only. Internal observation/trace IDs
    # may be numeric and can otherwise look like a credit-card test number.
    serialized = "\n".join(
        f"{getattr(item, 'input', None)!r}\n{getattr(item, 'output', None)!r}"
        for item in observations
    )
    pii_types = sorted(
        name
        for name, pattern in PII_PATTERNS.items()
        if re.search(pattern, serialized)
    )

    by_id = {item.id: item for item in observations}
    roots = [item for item in observations if item.parent_observation_id is None]
    root_ids = {item.id for item in roots}
    types = {_type_name(item) for item in observations}
    generations = [item for item in observations if _type_name(item) == "GENERATION"]
    children_nested_under_root = all(
        item.parent_observation_id in root_ids
        for item in observations
        if item.parent_observation_id is not None
    )
    generation_has_model = all(
        bool(
            getattr(item, "provided_model_name", None)
            or getattr(item, "model", None)
        )
        for item in generations
    )
    generation_has_usage = all(
        bool(getattr(item, "usage_details", None)) for item in generations
    )

    print(f"Trace ID: {trace.id}")
    print(f"Trace name: {trace.name}")
    print(f"Observations: {len(observations)}")
    for item in sorted(observations, key=lambda value: value.start_time):
        parent = item.parent_observation_id or "root"
        parent_name = getattr(by_id.get(item.parent_observation_id), "name", parent)
        print(f"- {_type_name(item)} {item.name} | parent={parent_name}")
    print(f"PII leaks: {pii_types or 'none'}")
    print(f"Redaction marker present: {'[REDACTED_' in serialized}")
    print(f"Generation model present: {generation_has_model}")
    print(f"Generation usage present: {generation_has_usage}")

    valid = (
        len(roots) == 1
        and {"SPAN", "RETRIEVER", "GENERATION"}.issubset(types)
        and children_nested_under_root
        and bool(generations)
        and generation_has_model
        and generation_has_usage
        and not pii_types
    )
    print("HỢP LỆ" if valid else "KHÔNG HỢP LỆ")
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
