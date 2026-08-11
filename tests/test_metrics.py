import pytest

import app.metrics as metrics
from app.metrics import record_error, record_request, snapshot


@pytest.fixture(autouse=True)
def reset_metrics():
    metrics.TRAFFIC = 0
    metrics.ERRORS.clear()
    metrics.REQUEST_LATENCIES.clear()
    metrics.REQUEST_COSTS.clear()
    metrics.REQUEST_TOKENS_IN.clear()
    metrics.REQUEST_TOKENS_OUT.clear()
    metrics.QUALITY_SCORES.clear()


def test_percentile_basic() -> None:
    assert metrics.percentile([100, 200, 300, 400], 50) >= 100


def test_error_rate_zero_when_no_requests() -> None:
    assert snapshot()["error_rate_pct"] == 0.0


def test_error_rate_mixed_success_and_error() -> None:
    for _ in range(3):
        record_request(latency_ms=100, cost_usd=0.01, tokens_in=20, tokens_out=80, quality_score=0.8)
    record_error("RuntimeError")
    snap = snapshot()
    assert snap["traffic"] == 3
    assert snap["error_rate_pct"] == 25.0          # 1/(3+1)*100
    assert snap["error_breakdown"] == {"RuntimeError": 1}


def test_error_rate_all_failures() -> None:
    record_error("RuntimeError")
    record_error("TimeoutError")
    assert snapshot()["error_rate_pct"] == 100.0
