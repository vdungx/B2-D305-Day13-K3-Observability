# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: B2-D305-Day13-K3-Observability
- Repository URL: https://github.com/vdungx/B2-D305-Day13-K3-Observability
- Commit SHA cuối: Cập nhật trước khi nộp.
- Thành viên và vai trò:
  - Trần Văn Dũng - 2A202601859 - A — API & Middleware.
  - B — Security Engineer / PII scrubbing.
  - C — Metrics & Dashboard.
  - D — SRE & Alerts Engineer.
  - E — QA, Chief Investigator & Langfuse.

## 2. Kết quả kỹ thuật

- Baseline CP0: `30/100`, 126 records, 0 correlation ID hợp lệ, 32 records thiếu required/enrichment fields, 0 PII leak.
- Kết quả CP1: `100/100`, 20 records, 10 correlation IDs, 0 records thiếu required/enrichment fields, 0 PII leak.
- Test suite gần nhất: `28 passed`.
- PII leak còn lại trong log CP1: `0`.
- Dashboard contract: `6/6 panel` hợp lệ. Chưa có screenshot/runtime dashboard trong evidence.
- Số liệu runtime CP1 từ `data/logs.jsonl`:
  - Requests/responses: `10/10`, errors: `0`.
  - Latency: P50 `152 ms`, P95 khoảng `492.25 ms`, P99 khoảng `713.65 ms`.
  - Cost: `0.017145 USD`.
  - Tokens: `330 input`, `1077 output`.
  - Quality proxy trung bình: `0.88`.

Evidence: `submission/evidence/baseline_validate_logs.txt`, `submission/evidence/cp1_validate_logs.txt`, `submission/evidence/cp1_pytest.txt`, `submission/evidence/cp1_validate_dashboard.txt`.

## 3. Logging và tracing

- Evidence correlation ID và log enrichment: `submission/evidence/cp1_log_samples.jsonl` và `submission/evidence/cp1_log_sample.json`.
- Correlation ID mẫu `req-e1f076d6` xuất hiện nhất quán ở `request_received` và `response_sent`.
- Metadata API gồm `user_id_hash`, `session_id`, `feature`, `model`, `env`.
- Evidence PII redaction: `submission/evidence/cp1_pii_redacted.json`; email được thay bằng `[REDACTED_EMAIL]`, số điện thoại bằng `[REDACTED_PHONE_VN]`.
- `clear_contextvars()` được gọi đầu mỗi request để context của structlog từ request trước không bị tái sử dụng, tránh sai correlation và rò rỉ metadata.
- Trace CP3 đã audit: `d8220b4404bba7690b4285c85364ed5a`, có `process-chat-request`, `retrieve-context` (RETRIEVER) và `generate-response` (GENERATION); model/usage có mặt, không phát hiện PII leak.
- Evidence trace export/an toàn: `submission/evidence/cp3_incident_investigation.txt`. Cần bổ sung screenshot trace waterfall từ Langfuse UI trước khi nộp.

## 4. Prompt versioning

- Prompt name theo contract: `day13-chat`.
- Version/label baseline: Chưa có evidence Langfuse trong repository.
- Version/label candidate: Chưa có evidence Langfuse trong repository.
- Trace ID của mỗi version: Chưa có.
- Bằng chứng đổi label hoặc rollback: Chưa có.
- Trạng thái: cần tạo prompt v1/v2, gắn label và chụp evidence thật trên Langfuse trước khi nộp.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract.`
- Evidence dashboard contract: `submission/evidence/cp1_validate_dashboard.txt`.
- Sáu nhóm panel: latency, traffic, errors, cost, tokens và quality; nguồn dữ liệu chuẩn là `data/logs.jsonl`.
- SLO hiện tại trong `config/slo.yaml`:
  - Latency P95 ≤ `3000 ms`, target `99.5%`.
  - Error rate ≤ `2%`, target `99.0%`.
  - Daily cost ≤ `2.5 USD`, target `100%`.
  - Quality score trung bình ≥ `0.75`, target `95%`.
- Alert rules đã có trong `config/alert_rules.yaml`: `HighErrorRate`, `HighLatency`, `LowQualityScore`, đều symptom-based.
- Alert runbook `docs/alerts.md` vẫn là template; cần hoàn thiện ba mục và bổ sung screenshot dashboard runtime trước khi nộp.

## 6. Điều tra challenge

- Challenge ID: `day13-k3-observability-v1` (K3); incident `rag_slow`; feature ảnh hưởng `refund`; latency threshold `2000 ms`.
- Triệu chứng từ metrics: 5 request challenge thành công, `error_rate_pct=0.0`; latency P50=`2652 ms`, P95/P99=`3227 ms`, vượt ngưỡng `2000 ms`.
- Trace ID liên quan: `d8220b4404bba7690b4285c85364ed5a`. Tổng `process-chat-request`=`2657 ms`; `retrieve-context`=`2506 ms`; `generate-response`=`151 ms`.
- Log line/correlation ID liên quan: `req-cb44b739`; `request_received` và `response_sent` đều feature `refund`, với `latency_ms=2652`.
- Root cause: Khi `rag_slow` bật, `mock_rag.retrieve` thêm delay 2.5 giây. Metrics, waterfall trace và logs cùng correlation ID xác nhận retrieval là điểm nghẽn.
- Mitigation: Tắt `rag_slow` sau khi thu evidence; `/health` xác nhận incident đã về `false`.
- Fix action: Thêm latency budget/timeout và cache hoặc tối ưu retrieval; kiểm chứng lại P95 của feature `refund` sau fix.
- Preventive measure: Duy trì SLO P95 latency, alert symptom-based và theo dõi duration `retrieve-context` trong Langfuse.
- Evidence: `submission/evidence/cp3_incident_investigation.txt`; cần bổ sung screenshot metrics và waterfall UI trước khi nộp.

## 7. Đóng góp cá nhân

| Thành viên/vai trò | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| A — API & Middleware | Correlation ID middleware, request/response headers, request context enrichment, CID liên kết trace/log CP3 | `a8ad3e0` | Liên kết metadata xuyên suốt vòng đời request và điều tra bằng CID. |
| B — Security Engineer | PII scrubbing và kiểm tra email/điện thoại/thẻ | Cập nhật sau | Redact trước khi render JSON và ghi file. |
| C — Metrics & Dashboard | Error rate, dashboard fields và dashboard contract | Cập nhật sau | Chọn metric và threshold phục vụ điều tra. |
| D — SRE & Alerts | SLI/SLO, alert mapping và runbook | Cập nhật sau | Chuyển symptom thành condition, severity và runbook. |
| E — QA, Chief Investigator & Langfuse | Load test, validator, trace audit và evidence CP3 | Cập nhật sau | Xác minh Metrics → Traces → Logs bằng evidence cụ thể. |

## 8. Checklist còn thiếu trước khi nộp

- [ ] Điền tên nhóm, repository URL và commit SHA cuối.
- [ ] Chụp danh sách ≥10 Langfuse traces và waterfall UI.
- [ ] Tạo prompt v1/v2, label baseline/candidate/production và evidence rollback.
- [ ] Dựng dashboard runtime, chụp screenshot đủ 6 nhóm panel.
- [ ] Hoàn thiện ba runbook trong `docs/alerts.md`.
- [ ] Cập nhật commit/PR thực tế của từng thành viên.
- [ ] Chạy test/validator cuối và kiểm tra không có secret hoặc PII trong Git.
