from __future__ import annotations

import os
import time
from dataclasses import dataclass
from functools import wraps
from typing import Callable, TypeVar

from . import metrics
from .mock_llm import FakeLLM
from .mock_rag import retrieve
from .pii import hash_user_id, scrub_text, summarize_text
from .prompt_management import resolve_prompt
from .tracing import (
    get_langfuse_client,
    propagate_attributes,
    tracing_enabled,
)


F = TypeVar("F", bound=Callable)


def _trace_agent_run(func: F) -> F:
    """Trace one request as a pipeline span without capturing raw arguments."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        client = get_langfuse_client()
        with client.start_as_current_span(
            name="process-chat-request",
        ):
            return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


@dataclass
class AgentResult:
    answer: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float


class LabAgent:
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model
        self.llm = FakeLLM(model=model)

    @_trace_agent_run
    def run(
        self,
        user_id: str,
        feature: str,
        session_id: str,
        message: str,
        correlation_id: str | None = None,
    ) -> AgentResult:
        started = time.perf_counter()
        langfuse_client = get_langfuse_client()
        app_env = os.getenv("APP_ENV", "dev")
        trace_tags = ["lab", feature, self.model, f"env:{app_env}"]
        trace_metadata = {
            "feature": feature,
            "model": self.model,
            "env": app_env,
            "correlation_id": correlation_id or "unavailable",
        }

        # Apply request dimensions before child observations are created so users,
        # sessions, tags, and metadata remain queryable across the whole trace.
        with propagate_attributes(
            user_id=hash_user_id(user_id),
            session_id=session_id,
            tags=trace_tags,
            metadata=trace_metadata,
        ):
            # Capture meaningful but sanitized root I/O instead of raw function args.
            langfuse_client.update_current_span(
                input={"feature": feature, "message": scrub_text(message)},
                metadata=trace_metadata,
            )

            with langfuse_client.start_as_current_observation(
                name="retrieve-context",
                as_type="retriever",
                input={"query": scrub_text(message)},
                metadata={"feature": feature, "source": "mock-corpus"},
            ) as retrieval_observation:
                docs = retrieve(message)
                retrieval_observation.update(
                    output={
                        "document_count": len(docs),
                        "documents": [scrub_text(doc) for doc in docs],
                    }
                )

            prompt = resolve_prompt(
                langfuse_client,
                feature=feature,
                docs=docs,
                message=message,
                enabled=tracing_enabled(),
            )
            generation_metadata = {
                "doc_count": len(docs),
                "query_preview": summarize_text(message),
                "prompt_name": prompt.name,
                "prompt_label": prompt.label,
                "prompt_version": prompt.version,
                "prompt_source": prompt.source,
                "prompt_fetch_error": prompt.fetch_error,
            }

            with langfuse_client.start_as_current_generation(
                name="generate-response",
                model=self.model,
                input={"prompt": scrub_text(prompt.text)},
                metadata=generation_metadata,
                prompt=prompt.managed_prompt,
            ) as generation_observation:
                response = self.llm.generate(prompt.text)
                cost_usd = self._estimate_cost(
                    response.usage.input_tokens,
                    response.usage.output_tokens,
                )
                generation_observation.update(
                    output={"answer": scrub_text(response.text)},
                    usage_details={
                        "prompt_tokens": response.usage.input_tokens,
                        "completion_tokens": response.usage.output_tokens,
                    },
                    cost_details={"total": cost_usd},
                )

            quality_score = self._heuristic_quality(message, response.text, docs)
            latency_ms = int((time.perf_counter() - started) * 1000)

            prompt_metadata = {
                "prompt_name": prompt.name,
                "prompt_label": prompt.label,
                "prompt_version": prompt.version,
                "prompt_source": prompt.source,
            }
            # v3 keeps trace-level attributes here; request attributes above are also
            # propagated to every child observation for filtering and dashboards.
            langfuse_client.update_current_trace(
                name="chat-response",
                user_id=hash_user_id(user_id),
                session_id=session_id,
                tags=trace_tags,
                metadata={**trace_metadata, **prompt_metadata},
            )
            langfuse_client.update_current_span(
                output={
                    "answer": scrub_text(response.text),
                    "quality_score": quality_score,
                },
                metadata=prompt_metadata,
            )

        metrics.record_request(
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            quality_score=quality_score,
        )

        return AgentResult(
            answer=response.text,
            latency_ms=latency_ms,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            cost_usd=cost_usd,
            quality_score=quality_score,
        )

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        input_cost = (tokens_in / 1_000_000) * 3
        output_cost = (tokens_out / 1_000_000) * 15
        return round(input_cost + output_cost, 6)

    def _heuristic_quality(self, question: str, answer: str, docs: list[str]) -> float:
        score = 0.5
        if docs:
            score += 0.2
        if len(answer) > 40:
            score += 0.1
        if question.lower().split()[0:1] and any(token in answer.lower() for token in question.lower().split()[:3]):
            score += 0.1
        if "[REDACTED" in answer:
            score -= 0.2
        return round(max(0.0, min(1.0, score)), 2)
