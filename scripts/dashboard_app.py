"""Streamlit dashboard — Day 13 AI Observability.

Reads ``data/logs.jsonl`` and renders the 6 panels defined in
``config/dashboard.yaml`` (latency, traffic, errors, cost, tokens, quality).

Run:
    streamlit run scripts/dashboard_app.py
"""
from __future__ import annotations

import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import altair as alt
import pandas as pd
import streamlit as st
import yaml

from app.cli import configure_utf8_stdio

configure_utf8_stdio()

_log_path = os.getenv("LOG_PATH", "data/logs.jsonl")
LOG_PATH = Path(_log_path) if Path(_log_path).is_absolute() else REPO_ROOT / _log_path
CONFIG_PATH = REPO_ROOT / "config" / "dashboard.yaml"

with open(CONFIG_PATH, encoding="utf-8") as f:
    DASH = yaml.safe_load(f)["dashboard"]

REFRESH_SECONDS: int = DASH["refresh_seconds"]  # 30
DEFAULT_WINDOW_MIN: int = DASH["time_range_minutes"]  # 60
TITLE: str = DASH["title"]
WINDOW_OPTIONS = [15, 30, 60, 120]


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def load_logs() -> pd.DataFrame:
    """Parse data/logs.jsonl into a DataFrame with a UTC-aware ``ts`` column."""
    if not LOG_PATH.exists():
        return pd.DataFrame()
    df = pd.read_json(LOG_PATH, lines=True)
    if df.empty or "ts" not in df.columns:
        return pd.DataFrame()
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    return df


def percentile_nearest_rank(values: pd.Series, p: int) -> float:
    """Nearest-rank percentile, consistent with app.metrics.percentile."""
    vals = values.dropna().sort_values().to_numpy()
    if len(vals) == 0:
        return 0.0
    idx = max(0, min(len(vals) - 1, round((p / 100) * len(vals) + 0.5) - 1))
    return float(vals[idx])


def rule(value: float, y_field: str = "y") -> alt.Chart:
    """Red dashed horizontal reference line (threshold/SLO)."""
    return (
        alt.Chart(pd.DataFrame({y_field: [value]}))
        .mark_rule(color="red", strokeDash=[4, 4])
        .encode(y=alt.Y(f"{y_field}:Q"))
    )


def _resp(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["event"] == "response_sent"]


def panel_latency(df: pd.DataFrame) -> None:
    st.subheader("Latency percentiles · ms")
    st.caption("source: response_sent.latency_ms")
    vals = _resp(df)["latency_ms"]
    p50 = percentile_nearest_rank(vals, 50)
    p95 = percentile_nearest_rank(vals, 95)
    p99 = percentile_nearest_rank(vals, 99)
    bars = pd.DataFrame(
        {"percentile": ["p50", "p95", "p99"], "latency_ms": [p50, p95, p99]}
    )
    chart = alt.Chart(bars).mark_bar().encode(
        x="percentile:N", y="latency_ms:Q", tooltip=["percentile", "latency_ms"]
    ) + rule(3000, "latency_ms")
    st.altair_chart(chart, width="stretch")
    st.caption(f"SLO: P95 ≤ 3000 ms (hiện tại {p95:.0f} ms)")


def panel_traffic(df: pd.DataFrame) -> None:
    st.subheader("Request traffic · req/min")
    st.caption("source: request_received")
    rec = df[df["event"] == "request_received"]
    n = len(rec)
    span_min = max((df["ts"].max() - df["ts"].min()).total_seconds() / 60.0, 1 / 60)
    rate = n / span_min
    st.metric("Requests", n)
    st.metric("Avg rate", f"{rate:.1f} / min")
    per_min = rec.set_index("ts").resample("1min").size().reset_index(name="count")
    chart = alt.Chart(per_min).mark_line(point=True).encode(
        x="ts:T", y="count:Q", tooltip=["ts", "count"]
    ) + rule(1, "count")
    st.altair_chart(chart, width="stretch")
    st.caption("Threshold: ≥ 1 req/min (baseline)")


def panel_errors(df: pd.DataFrame) -> None:
    st.subheader("Error rate and breakdown · %")
    st.caption("source: request_received + request_failed.error_type")
    received = df[df["event"] == "request_received"]
    failed = df[df["event"] == "request_failed"]
    denom = len(received)
    err_rate = (len(failed) / denom * 100) if denom > 0 else 0.0
    st.metric("Error rate", f"{err_rate:.1f}%")
    if not failed.empty and "error_type" in failed.columns:
        breakdown = failed["error_type"].value_counts().reset_index()
        breakdown.columns = ["error_type", "count"]
    else:
        breakdown = pd.DataFrame(columns=["error_type", "count"])
    st.dataframe(breakdown, width="stretch")
    d = pd.DataFrame({"label": ["error_rate"], "pct": [err_rate]})
    chart = alt.Chart(d).mark_bar().encode(x="label:N", y="pct:Q") + rule(2, "pct")
    st.altair_chart(chart, width="stretch")
    st.caption("SLO: ≤ 2% · alert > 5% trong 3 phút")


def panel_cost(df: pd.DataFrame) -> None:
    st.subheader("Cost over time · USD")
    st.caption("source: response_sent.cost_usd")
    resp = _resp(df)
    total = resp["cost_usd"].sum()
    st.metric("Total", f"${total:.4f}")
    per_min = resp.set_index("ts").resample("1min")["cost_usd"].sum().reset_index()
    chart = alt.Chart(per_min).mark_line(point=True).encode(
        x="ts:T", y="cost_usd:Q", tooltip=["ts", "cost_usd"]
    ) + rule(2.5, "cost_usd")
    st.altair_chart(chart, width="stretch")
    st.caption("SLO: tổng ≤ $2.50/ngày")


def panel_tokens(df: pd.DataFrame) -> None:
    st.subheader("Input and output tokens · tokens")
    st.caption("source: response_sent.tokens_in/tokens_out")
    resp = _resp(df)
    tin = resp["tokens_in"].sum()
    tout = resp["tokens_out"].sum()
    d = pd.DataFrame({"field": ["tokens_in", "tokens_out"], "tokens": [tin, tout]})
    chart = alt.Chart(d).mark_bar().encode(
        x="field:N", y="tokens:Q", tooltip=["field", "tokens"]
    ) + rule(50000, "tokens")
    st.altair_chart(chart, width="stretch")
    st.caption(f"Threshold: tổng ≤ 50000 tokens (in={tin}, out={tout})")


def panel_quality(df: pd.DataFrame) -> None:
    st.subheader("Quality proxy · 0–1")
    st.caption("source: response_sent.quality_score")
    q = _resp(df)["quality_score"].mean()
    q = 0.0 if pd.isna(q) else float(q)
    st.metric("Mean quality", f"{q:.2f}")
    st.progress(min(max(q, 0.0), 1.0))
    d = pd.DataFrame({"label": ["quality"], "score": [q]})
    chart = alt.Chart(d).mark_bar().encode(
        x="label:N", y=alt.Y("score:Q", scale=alt.Scale(domain=[0, 1]))
    ) + rule(0.75, "score")
    st.altair_chart(chart, width="stretch")
    st.caption("SLO: ≥ 0.75")


@st.fragment(run_every=REFRESH_SECONDS)
def render_dashboard(window_min: int) -> None:
    data = load_logs()
    if data.empty:
        st.info("Không tìm thấy data/logs.jsonl. Chạy API rồi scripts/load_test.py trước.")
        return
    now = pd.Timestamp.now(tz="UTC")
    cutoff = now - pd.Timedelta(minutes=window_min)
    df = data[data["ts"] >= cutoff].copy()
    if df.empty:
        st.info(f"Chưa có dữ liệu trong {window_min} phút gần nhất. Chạy server + load_test.")
        return

    start = df["ts"].min()
    end = df["ts"].max()
    st.title(TITLE)
    st.caption(
        f"Window: {start:%Y-%m-%d %H:%M} UTC → {end:%Y-%m-%d %H:%M} UTC "
        f"· source: data/logs.jsonl · refresh {REFRESH_SECONDS}s"
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        panel_latency(df)
    with c2:
        panel_traffic(df)
    with c3:
        panel_errors(df)
    c4, c5, c6 = st.columns(3)
    with c4:
        panel_cost(df)
    with c5:
        panel_tokens(df)
    with c6:
        panel_quality(df)


def main() -> None:
    st.set_page_config(page_title=TITLE, layout="wide")
    st.sidebar.title("Dashboard")
    idx = WINDOW_OPTIONS.index(DEFAULT_WINDOW_MIN) if DEFAULT_WINDOW_MIN in WINDOW_OPTIONS else 2
    window_min = st.sidebar.selectbox("Time window (minutes)", WINDOW_OPTIONS, index=idx)
    st.sidebar.caption(f"Auto-refresh: mỗi {REFRESH_SECONDS}s")
    if st.sidebar.button("🔄 Làm mới ngay"):
        st.cache_data.clear()
        st.rerun()
    render_dashboard(window_min)


if __name__ == "__main__":
    main()
