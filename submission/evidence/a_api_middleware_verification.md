# A — API & Middleware verification

## CP0 — API availability

- `/health` returned `ok: true` with Langfuse tracing enabled.

## CP1 — Correlation ID and request context

- `CorrelationIdMiddleware` clears prior structlog context, accepts a caller-provided `x-request-id` or creates `req-<8 hex>`.
- Successful and failed `/chat` responses include `x-request-id` and `x-response-time-ms`.
- Request context binds `user_id_hash`, `session_id`, `feature`, `model`, and `env` before `request_received` is logged.
- Regression coverage: `tests/test_correlation_middleware.py`.

## CP2 — API metrics and trace correlation

- `/metrics` exposes error-rate data; regression coverage verifies 0%, mixed success/error, and 100% error cases.
- The agent receives the request correlation ID and writes it into trace metadata, enabling trace-to-log lookup.

## CP3 — Incident trace-to-log proof

- Challenge request: correlation ID `req-cb44b739`, feature `refund`, response latency `2652 ms`.
- Trace `d8220b4404bba7690b4285c85364ed5a` has the same request context and shows `retrieve-context` as the bottleneck.
- The matching `request_received` and `response_sent` logs prove the link between API request, trace, and log evidence.

## Error-path load test

- `scripts/load_test.py` now prioritizes `x-request-id` from a response header, so a 500 response remains traceable even if its JSON body has no `correlation_id`.
- Regression coverage: `tests/test_load_test.py`.
