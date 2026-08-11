# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: Chưa cập nhật.
- Repository URL: Chưa cập nhật.
- Commit SHA cuối: Chưa cập nhật.
- Thành viên và vai trò CP1:
  - A — API & Middleware.
  - B — Security Engineer / PII scrubbing.
  - C — Metrics & Dashboard.
  - D — SRE & Alerts Engineer.
  - E — QA & Chief Investigator.

## 2. Kết quả kỹ thuật

<<<<<<< HEAD
- Baseline CP0: `30/100`, 126 records, 0 correlation ID hợp lệ, 32 records thiếu required/enrichment fields, 0 PII leak.
- Kết quả CP1: `100/100`, 20 records, 10 correlation IDs, 0 records thiếu required fields, 0 records thiếu enrichment, 0 PII leak.
- Test suite CP1: `28 passed`.
- Tổng số traces Langfuse: Chưa có evidence trace ID trong repo; không ghi nhận số trace để tránh khai báo sai.
- PII leak còn lại trong log CP1: `0`.
- Dashboard contract: `6/6 panel` hợp lệ. Chưa có screenshot/runtime dashboard trong evidence.
- Số liệu runtime từ `data/logs.jsonl`:
  - Requests/responses: `10/10`, errors: `0`.
  - Latency: P50 `152 ms`, P95 khoảng `492.25 ms`, P99 khoảng `713.65 ms`.
  - Cost: `0.017145 USD`.
  - Tokens: `330 input`, `1077 output`.
  - Quality proxy trung bình: `0.88`.

Evidence: `submission/evidence/baseline_validate_logs.txt`, `submission/evidence/cp1_validate_logs.txt`, `submission/evidence/cp1_pytest.txt`.

## 3. Logging và tracing

- Evidence correlation ID và log enrichment: `submission/evidence/cp1_log_samples.jsonl`.
- Correlation ID mẫu `req-e1f076d6` xuất hiện nhất quán ở `request_received` và `response_sent`.
- Metadata API gồm `user_id_hash`, `session_id`, `feature`, `model`, `env`.
- Evidence PII redaction: email được thay bằng `[REDACTED_EMAIL]`, số điện thoại bằng `[REDACTED_PHONE_VN]`; validator phát hiện 0 PII leak.
- Evidence trace waterfall: Chưa có trong repo; cần bổ sung screenshot/export từ Langfuse.
- Span đáng chú ý từ log: request `req-e1f076d6` có response latency `769 ms`, cao hơn phần lớn response `152–154 ms`; đây là tín hiệu cần mở trace tương ứng để điều tra sâu hơn, chưa đủ để kết luận root cause.
=======
- Điểm `validate_logs.py`: 
  - **30/100 (baseline CP0)** — Thiếu correlation ID hợp lệ và enrichment fields.
  - **100/100 (CP1)** — Đã có Correlation ID (req-*), đủ enrichment fields và lọc PII thành công. Khác biệt cốt lõi là CP1 cho phép nhóm gom nhóm log bằng `correlation_id`, việc dùng `clear_contextvars()` trước mỗi request cũng ngăn ngừa lọt lộ metadata của request cũ qua request mới (thường hay gặp do structlog/FastAPI tái sử dụng worker task).
- Tổng số traces:
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID: Xem tại `submission/evidence/cp1_log_sample.json` và `cp1_trace_metadata.md`
- Evidence PII redaction: Xem tại `submission/evidence/cp1_pii_redacted.json`
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:
>>>>>>> 83f8358267389a03f83107dbdf74764953036f58

## 4. Prompt versioning

- Prompt name theo contract: `day13-chat`.
- Version/label baseline: Chưa có evidence Langfuse.
- Version/label candidate: Chưa có evidence Langfuse.
- Trace ID của mỗi version: Chưa có.
- Bằng chứng đổi label hoặc rollback: Chưa có.
- Trạng thái: phần prompt versioning chưa được xác minh trong report vì chưa có screenshot/trace managed prompt.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract.`
- Evidence dashboard contract: `submission/evidence/cp1_validate_dashboard.txt`.
- Sáu nhóm panel: latency, traffic, errors, cost, tokens và quality; nguồn dữ liệu chuẩn là `data/logs.jsonl`.
- SLO đang khai báo trong `config/slo.yaml`:
  - Latency P95 ≤ `3000 ms`, target `99.5%`.
  - Error rate ≤ `2%`, target `99.0%`.
  - Daily cost ≤ `2.5 USD`.
  - Quality score trung bình ≥ `0.75`, target `95%`.
- Kết quả baseline CP1 so với SLO: latency P95 khoảng `492.25 ms`, error rate `0%`, cost `0.017145 USD`, quality `0.88`; đều nằm trong các ngưỡng hiện tại.
- Evidence dashboard runtime/screenshot: Chưa có.
- Alert rules và runbook: `config/alert_rules.yaml` vẫn còn các giá trị `TODO`; `docs/alerts.md` mới là template. Cần hoàn thiện trước khi nộp chính thức.

## 6. Điều tra challenge

- Challenge ID: Chưa có challenge chính thức được release trong `config/challenge.json`.
- Triệu chứng từ metrics: Chưa chạy official challenge. Trong baseline CP1, có một request chậm nổi bật ở `769 ms`, nhưng chưa phải incident chính thức.
- Trace ID liên quan: Chưa có.
- Log line/correlation ID liên quan: `req-e1f076d6`, event `response_sent`, latency `769 ms`.
- Root cause: Chưa thể kết luận chỉ từ log; cần trace/span và input/incident metadata.
- Fix action: Chưa áp dụng cho challenge chính thức.
- Preventive measure: Khi challenge được release, thực hiện đúng luồng Metrics → Trace → Logs, ghi lại metric, trace ID, correlation ID và log line trước khi kết luận.

## 7. Đóng góp cá nhân

| Thành viên/vai trò | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| A — API & Middleware | Correlation ID middleware, request/response headers, request context enrichment | Chưa cập nhật | Liên kết request metadata xuyên suốt vòng đời request |
| B — Security Engineer | PII scrubbing và kiểm tra email/điện thoại/thẻ | Chưa cập nhật | Redact trước khi render JSON và ghi file |
| C — Metrics & Dashboard | Error rate, dashboard fields và dashboard contract | Chưa cập nhật | Chọn metric và threshold có thể dùng để điều tra |
| D — SRE & Alerts | Chuẩn bị SLI/SLO và alert mapping | Chưa cập nhật | Chuyển symptom thành condition, severity và runbook |
| E — QA & Chief Investigator | Load test tích hợp, validator, pytest, kiểm tra correlation ID/PII và đóng gói evidence | Chưa cập nhật | Xác minh luồng Metrics → Traces → Logs bằng evidence cụ thể |

## 8. Checklist còn thiếu trước khi nộp

- Bổ sung tên nhóm, repository URL, commit SHA và commit/PR của từng thành viên.
- Tạo tối thiểu 10 trace Langfuse và evidence trace waterfall.
- Tạo prompt v1/v2, label baseline/candidate/production và evidence rollback.
- Dựng dashboard runtime, chụp screenshot đủ 6 nhóm panel.
- Hoàn thiện `config/alert_rules.yaml` và runbook.
- Chờ Lab Coach release challenge chính thức rồi thực hiện điều tra và cập nhật mục 6.
