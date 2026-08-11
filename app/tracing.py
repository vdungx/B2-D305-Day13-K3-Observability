from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any

try:
    from langfuse import get_client, observe

    LANGFUSE_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - chỉ dùng khi chưa cài requirements
    LANGFUSE_SDK_AVAILABLE = False

    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func

        return decorator

    class _DummyClient:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_span(self, **kwargs: Any) -> None:
            return None

        def update_current_generation(self, **kwargs: Any) -> None:
            return None

        @contextmanager
        def start_as_current_span(self, **kwargs: Any):
            yield _DummyObservation()

        @contextmanager
        def start_as_current_generation(self, **kwargs: Any):
            yield _DummyObservation()

        def flush(self) -> None:
            return None

    class _DummyObservation:
        def update(self, **kwargs: Any) -> None:
            return None

    def get_client():
        return _DummyClient()


def get_langfuse_client():
    return get_client()


@contextmanager
def propagate_attributes(**attributes: Any):
    """Apply request-level attributes (user_id/session_id/tags/metadata) to the current trace.

    langfuse 3.2.1 has no top-level propagate_attributes; update_current_trace achieves the
    same and child observations inherit trace-level attributes. Only touches the trace when
    one is actually open so unit tests never send stray traces.
    """
    try:
        client = get_client()
        has_trace_id = getattr(client, "get_current_trace_id", None)
        if has_trace_id and client.get_current_trace_id() is not None:
            client.update_current_trace(**attributes)
    except Exception:
        pass
    yield


def tracing_enabled() -> bool:
    return LANGFUSE_SDK_AVAILABLE and bool(
        os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
    )


def flush_traces() -> None:
    """Flush queued observations during graceful application shutdown."""
    if tracing_enabled():
        get_langfuse_client().flush()
