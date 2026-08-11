# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

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

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`:
- Evidence dashboard:
- SLO đã chọn và lý do:
- Alert rules và runbook:

## 6. Điều tra challenge

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| | | | |
