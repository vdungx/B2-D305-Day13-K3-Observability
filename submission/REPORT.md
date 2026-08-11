# Báo cáo Day 13 — AI Observability

## 1. Thông tin nhóm

- Tên nhóm: B2-D305-Day13-K3-Observability.
- Repository URL: https://github.com/vdungx/B2-D305-Day13-K3-Observability
- Commit SHA cuối: Cập nhật sau khi commit evidence/report cuối.
- Vai trò: A — API & Middleware; B — Security/PII; C — Metrics & Dashboard; D — SRE & Alerts; E — QA, Chief Investigator & Langfuse.

## 2. Kết quả tổng quan

**Hệ thống đã đạt baseline observability kỹ thuật:** log validator `100/100`, dashboard contract `6/6` và pytest `29 passed`. Sau CP1, log không còn PII raw, có correlation ID và request context đầy đủ. CP2 đã tạo/audit trace Langfuse, dashboard runtime và SLO/alert; CP3 đã tái hiện và điều tra incident `rag_slow` bằng chuỗi Metrics → Traces → Logs.

| Hạng mục | Kết quả đã xác minh | Evidence |
|---|---:|---|
| CP0 baseline logs | 30/100 | `baseline_validate_logs.txt` |
| CP1 logs sạch | 100/100; 115 records, 41 CID, 0 PII leak | `rerun_final_checks.txt` |
| Test suite | 29 passed | `rerun_final_checks.txt` |
| Dashboard contract | 6/6 panel | `rerun_final_checks.txt` |
| CP2 trace audit | Hợp lệ; PII/model/usage đầy đủ | `rerun_cp2_traces.txt` |
| CP3 latency P95 | 3093 ms, vượt 2000 ms | `rerun_cp3_investigation.txt` |

## 3. CP0–CP1 — Logging an toàn và truy vết request

Baseline CP0 có JSON logs nhưng không đủ context để nối các sự kiện theo request. Kết quả rerun hiện tại là 115 log records hợp lệ, không thiếu required/enrichment fields, có 41 correlation IDs và không phát hiện PII raw.

- Middleware gọi `clear_contextvars()` ở đầu request để context structlog của request cũ không thể rò sang request mới.
- `x-request-id` được giữ xuyên response, log và trace; `x-response-time-ms` hỗ trợ đo latency phía API.
- `request_received` có `user_id_hash`, `session_id`, `feature`, `model`, `env`; email/điện thoại được redact trước JSON render.
- Ví dụ evidence correlation/redaction: `cp1_log_samples.jsonl`, `cp1_log_sample.json`, `cp1_pii_redacted.json`.

## 4. CP2 — Metrics, dashboard, traces và alert

### Runtime metrics và dashboard

Batch 10 request sạch sau CP1 cho P50 `151 ms`, P95 `541 ms`, error rate `0%`, tổng cost `$0.0241`, 330 input tokens, 1542 output tokens và quality `0.88`. Dashboard dùng nguồn chuẩn `data/logs.jsonl` và có sáu nhóm: latency, traffic, error, cost, tokens, quality. Contract validator xác nhận 6/6 panel; ảnh runtime hiện có tại `submission/evidence/dashboard_main.png`.

SLO hiện tại: P95 latency ≤3000 ms, error rate ≤2%, daily cost ≤$2.50 và quality ≥0.75. Ba alert symptom-based (`high_latency_p95`, `elevated_error_rate`, `cost_budget_exceeded`) và runbook Metrics → Traces → Logs đã hoàn thiện tại `config/alert_rules.yaml` và `docs/alerts.md`.

### Langfuse và prompt versioning

Trace `20330fe031365635c8c8e71ad4f8d985` audit hợp lệ: hierarchy gồm `process-chat-request`, `retrieve-context` kiểu RETRIEVER và `generate-response` kiểu GENERATION; model, usage và PII scrubbing đều đạt.

Prompt managed `day13-chat` đã có:

- v5, labels `baseline` và `production`; trace baseline `fa2e3ce889cf8e02fbf88b27e78f3c16` xác nhận label baseline/version 5.
- v6, label `candidate`; trace candidate `abe4ad2a87575df9fb21c216019787ca` xác nhận label candidate/version 6.

**Khoảng trống cần xử lý trên UI trước nộp:** chuyển label `production` sang candidate, rollback về baseline và lưu ảnh prompt list, hai waterfall cùng ảnh before/after label. Không ghi nhận là đã rollback khi chưa có UI evidence.

Evidence kỹ thuật: `rerun_cp2_traces.txt`, `dashboard_main.png`, `dashboard_validator.txt`.

## 5. CP3 — Điều tra official challenge

Challenge K3 là `day13-k3-observability-v1`: incident `rag_slow`, ảnh hưởng feature `refund`, ngưỡng latency 2000 ms.

**Triệu chứng:** năm request official đều thành công (`error_rate=0%`) nhưng latency P50 là 2652 ms, P95/P99 là 3093 ms — vượt SLO/threshold.

**Khoanh vùng:** trace `1eed0ec2e064e737fa7bb64d07f397ad` của request CID `req-51ed77cc` có tổng duration 2653 ms. Trong waterfall, `retrieve-context` chiếm 2501 ms, trong khi `generate-response` chỉ 151 ms.

**Chứng minh và hành động:** logs `request_received`/`response_sent` cùng CID ghi feature refund và latency 2652 ms. Khi `rag_slow` bật, `mock_rag.retrieve` thêm delay khoảng 2.5 giây; do đó retrieval là root cause. Incident đã được tắt sau khi thu evidence và `/health` xác nhận `rag_slow=false`.

- Mitigation: tắt incident/fallback retrieval bất thường.
- Fix: thêm timeout/latency budget, cache hoặc tối ưu retriever; xác minh lại P95 của refund sau fix.
- Prevention: giữ alert P95 symptom-based và theo dõi duration `retrieve-context` trong Langfuse.

Evidence: `rerun_cp3_investigation.txt`.

## 6. Đóng góp cá nhân

| Thành viên/vai trò | Phần việc | Commit/PR cần gắn trước nộp |
|---|---|---|
| A — API & Middleware | Correlation ID, request context, error headers, trace-to-log mapping | `a8ad3e0`, `89c4254`, `76dd973` — chưa có PR |
| B — Security Engineer | PII regex/scrubbing và audit evidence | `7a57bfb` — chưa có PR |
| C — Metrics & Dashboard | Error rate, dashboard contract/runtime | `ded378b`, `d6dfc5f` — chưa có PR |
| D — SRE & Alerts | SLO, alert rules, runbooks | `411683e`, `76a8096` — chưa có PR |
| E — QA/Investigator/Langfuse | Load test, trace/prompt audit, challenge evidence | `a0d57bc` — chưa có PR |

## 7. Checklist trước khi nộp

- [x] `validate_logs.py` đạt 100/100.
- [x] `validate_dashboard.py` hợp lệ 6/6.
- [x] `pytest` pass 29 tests.
- [x] Có correlation ID, PII redaction, trace audit và investigation CP3.
- [ ] Chụp danh sách ≥10 traces và waterfall trên Langfuse UI.
- [ ] Chụp prompt v5/v6 và thao tác production → candidate → baseline trên UI.
- [ ] Bổ sung ảnh dashboard thấy đủ sáu panel nếu ảnh hiện tại chưa bao quát toàn bộ.
- [ ] Điền commit/PR của B–E và final SHA trước nộp.
- [ ] Kiểm tra `git status --short` không có `.env`, cache, `.venv` hoặc PII raw.
