# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: `B2-D305`
- Repository URL: [B2-D305-Day13-K3-Observability](https://github.com/vdungx/B2-D305-Day13-K3-Observability)
- Commit SHA cuối: [`9bbe562`](https://github.com/vdungx/B2-D305-Day13-K3-Observability/commit/9bbe562)
- Thành viên và vai trò:
  - Trần Văn Dũng — `2A202601859` — A: API & Middleware
  - Đàm Lê Minh Quân — `2A202601451` — B: Security/PII
  - Nguyễn Viết Huy — `2A202601081` — C: Metrics & Dashboard
  - Lê Văn Đông — `2A202601851` — D: SRE & Alerts
  - Đào Đức Mạnh — `2A202601833` — E: QA, Chief Investigator & Langfuse

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: CP0 baseline `30/100`, kết quả cuối `100/100`; 115 records, 41 correlation IDs, không thiếu field và không phát hiện PII. `pytest`: `29 passed`. Xem [rerun_final_checks.txt](evidence/rerun_final_checks.txt) và [cp1_pytest.txt](evidence/cp1_pytest.txt).
- Tổng số traces: 10 runtime traces trong [cp2_trace_list_export.txt](evidence/cp2_trace_list_export.txt); tổng evidence có 13 trace ID khác nhau gồm 10 runtime, baseline, candidate và CP3 challenge.
- Số PII leak còn lại: `0`.
- Link/đường dẫn dashboard: chạy `streamlit run scripts/dashboard_app.py`; ảnh [dashboard_main.png](evidence/dashboard_main.png) và [dashboard_incident.png](evidence/dashboard_incident.png) bao phủ đủ sáu panel.

## 3. Logging và tracing

- Evidence correlation ID: CP2 có `req-e434eabe` trong [cp1_log_samples.jsonl](evidence/cp1_log_samples.jsonl) và [cp2_trace_list_export.txt](evidence/cp2_trace_list_export.txt); CP3 có `req-51ed77cc` trong [rerun_cp3_investigation.txt](evidence/rerun_cp3_investigation.txt).
- Evidence PII redaction: [cp1_pii_redacted.json](evidence/cp1_pii_redacted.json) và kết quả validator trong [rerun_final_checks.txt](evidence/rerun_final_checks.txt) (`0` leak).
- Evidence trace waterfall: [cp2_waterfall_export.txt](evidence/cp2_waterfall_export.txt), [langfuse_waterfall_cp2.png](evidence/langfuse_waterfall_cp2.png) và [langfuse_waterfall_cp3.png](evidence/langfuse_waterfall_cp3.png).
- Giải thích một span đáng chú ý: trong CP3, span `retrieve-context` kiểu `RETRIEVER` mất `2501 ms` trên tổng trace `2653 ms`, còn `generate-response` mất `151 ms`; đây là span xác định nguyên nhân latency.

## 4. Prompt versioning

- Prompt name: `day13-chat`.
- Version/label baseline: v5 / `baseline`; baseline trace xác nhận `prompt_version=5`, `prompt_label=baseline`.
- Version/label candidate: v6 / `candidate`; candidate trace xác nhận `prompt_version=6`, `prompt_label=candidate`.
- Trace ID của mỗi version: baseline `fa2e3ce889cf8e02fbf88b27e78f3c16`; candidate `abe4ad2a87575df9fb21c216019787ca`; runtime production v3 `20330fe031365635c8c8e71ad4f8d985`. Chi tiết ở [cp2_waterfall_export.txt](evidence/cp2_waterfall_export.txt) và [rerun_cp2_traces.txt](evidence/rerun_cp2_traces.txt).
- Bằng chứng đổi label hoặc rollback: ảnh Langfuse UI [langfuse_prompt.png](evidence/langfuse_prompt.png), ảnh trace list [langfuse_trace_list.png](evidence/langfuse_trace_list.png) và commit [`a3a86de`](https://github.com/vdungx/B2-D305-Day13-K3-Observability/commit/a3a86de) ghi nhận thao tác production → candidate → baseline.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: hợp lệ `6/6` panel, xem [dashboard_validator.txt](evidence/dashboard_validator.txt).
- Evidence dashboard: [dashboard_incident.png](evidence/dashboard_incident.png) (Latency/Traffic/Error) và [dashboard_main.png](evidence/dashboard_main.png) (Cost/Tokens/Quality). Runtime batch 10 request đạt P50 `151 ms`, P95 `541 ms`, error rate `0%`, total cost `$0.0241`, 330 input tokens, 1542 output tokens và quality `0.88`.
- SLO đã chọn và lý do: P95 latency ≤ `3000 ms`, error rate ≤ `2%`, daily cost ≤ `$2.50`, quality ≥ `0.75`; các ngưỡng bao phủ độ trễ, độ tin cậy, ngân sách và chất lượng đầu ra.
- Alert rules và runbook: [`config/alert_rules.yaml`](../config/alert_rules.yaml) có `high_latency_p95`, `elevated_error_rate`, `cost_budget_exceeded`; runbook tại [`docs/alerts.md`](../docs/alerts.md) hướng dẫn điều tra Metrics → Traces → Logs.

## 6. Điều tra challenge

- Challenge ID: `day13-k3-observability-v1`; incident `rag_slow`; feature bị ảnh hưởng `refund`; threshold `2000 ms`.
- Triệu chứng từ metrics: 5/5 request thành công (`error_rate=0%`) nhưng P50 `2652 ms`, P95/P99 `3093 ms`, vượt threshold.
- Trace ID liên quan: `1eed0ec2e064e737fa7bb64d07f397ad`, tổng duration `2653 ms`.
- Log line/correlation ID liên quan: `request_received` và `response_sent`, correlation ID `req-51ed77cc`, feature `refund`, response latency `2652 ms`; xem [rerun_cp3_investigation.txt](evidence/rerun_cp3_investigation.txt).
- Root cause: khi `rag_slow` bật, `mock_rag.retrieve` thêm khoảng `2.5 s`; waterfall xác nhận `retrieve-context` là phần chiếm thời gian chính.
- Fix action: đã tắt incident và xác nhận `/health` trả `rag_slow=false`; mitigation là fallback retrieval. Fix lâu dài cần timeout/latency budget, cache hoặc tối ưu retriever rồi xác minh lại P95.
- Preventive measure: giữ alert P95 và theo dõi duration `retrieve-context` trong Langfuse; dùng runbook Metrics → Traces → Logs để điều tra theo correlation ID. Evidence waterfall tại [langfuse_waterfall_cp3.png](evidence/langfuse_waterfall_cp3.png).

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Trần Văn Dũng — A (`2A202601859`) | API middleware, correlation ID, trace-to-log mapping, CP3 evidence và Langfuse UI evidence | [`a8ad3e0`](https://github.com/vdungx/B2-D305-Day13-K3-Observability/commit/a8ad3e0), [`89c4254`](https://github.com/vdungx/B2-D305-Day13-K3-Observability/commit/89c4254), [`76dd973`](https://github.com/vdungx/B2-D305-Day13-K3-Observability/commit/76dd973), [`d4cc870`](https://github.com/vdungx/B2-D305-Day13-K3-Observability/commit/d4cc870), [`a3a86de`](https://github.com/vdungx/B2-D305-Day13-K3-Observability/commit/a3a86de), [`f208da4`](https://github.com/vdungx/B2-D305-Day13-K3-Observability/commit/f208da4), [`8098fb5`](https://github.com/vdungx/B2-D305-Day13-K3-Observability/commit/8098fb5) | Nối Metrics → Traces → Logs và quản lý prompt labels. |
| Đàm Lê Minh Quân — B (`2A202601451`) | PII regex/scrubbing và security audit | [`7a57bfb`](https://github.com/vdungx/B2-D305-Day13-K3-Observability/commit/7a57bfb) | Redact PII trước khi ghi log và kiểm chứng không còn leak. |
| Nguyễn Viết Huy — C (`2A202601081`) | Error rate, dashboard contract/runtime và CP3 metrics | [`ded378b`](https://github.com/vdungx/B2-D305-Day13-K3-Observability/commit/ded378b), [`d6dfc5f`](https://github.com/vdungx/B2-D305-Day13-K3-Observability/commit/d6dfc5f) | Thiết kế metric có thể dẫn đường cho điều tra sự cố. |
| Lê Văn Đông — D (`2A202601851`) | SLO, alert rules và runbook SRE | [`411683e`](https://github.com/vdungx/B2-D305-Day13-K3-Observability/commit/411683e), [`76a8096`](https://github.com/vdungx/B2-D305-Day13-K3-Observability/commit/76a8096) | Viết alert theo symptom và điều tra theo runbook. |
| Đào Đức Mạnh — E (`2A202601833`) | QA, load test, trace/prompt audit, challenge evidence và report | [`a0d57bc`](https://github.com/vdungx/B2-D305-Day13-K3-Observability/commit/a0d57bc), [`1b43fc5`](https://github.com/vdungx/B2-D305-Day13-K3-Observability/commit/1b43fc5), [`1e4df3f`](https://github.com/vdungx/B2-D305-Day13-K3-Observability/commit/1e4df3f) | Kiểm chứng evidence end-to-end và chuẩn hóa báo cáo. |
