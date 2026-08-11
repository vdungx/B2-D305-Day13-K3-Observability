# Checkpoint CP1 — Structured Logging, Correlation ID & PII

**Thời lượng:** 60 phút  
**Bắt đầu:** 0:30  
**Mục tiêu:** Hoàn thiện correlation ID, log enrichment, PII scrubbing và error rate để log có thể dùng cho điều tra incident.

## Phân công 5 thành viên

| Thành viên | Vai trò | Công việc CP1 | File phụ trách | Bàn giao |
|---|---|---|---|---|
| A | API & Middleware | Xóa context cũ, tạo/nhận correlation ID, bind vào structlog, thêm response headers; enrich request context trong `/chat`; tùy chọn thêm exception handler. | `app/middleware.py`, `app/main.py` | Response có `x-request-id`, `x-response-time-ms`; log API có metadata đầy đủ. |
| B | Security Engineer | Bật PII scrubber; scrub toàn bộ string/nested payload trước khi render JSON; mở rộng regex PII và tests. | `app/logging_config.py`, `app/pii.py`, tests PII | Không còn PII raw; log có `[REDACTED_*]`. |
| C | Metrics & Dashboard | Thêm `error_rate_pct` vào `/metrics`; kiểm tra cách đếm success/error và thêm test. | `app/metrics.py`, tests metrics | `/metrics` trả `error_rate_pct` chính xác. |
| D | SRE & Alerts Engineer | Review field log/metrics mới; chuẩn bị mapping SLI/SLO/alert cho CP2. | Ghi chú nội bộ, chuẩn bị `config/slo.yaml` và `config/alert_rules.yaml` cho CP2 | Bảng SLI → metric/log field dùng được ở CP2. |
| E | QA & Chief Investigator | Xác nhận correlation ID xuất hiện trong trace metadata; chạy load test, validator, pytest; lưu evidence; so sánh CP0/CP1. | `submission/evidence/`, `submission/REPORT.md` | Validator ≥80/100, ảnh log/trace và tóm tắt CP0 vs CP1. |

## Công việc kỹ thuật

### A — Middleware và log context

1. Trong `CorrelationIdMiddleware.dispatch()`:
   - Gọi `clear_contextvars()` trước mỗi request.
   - Dùng `x-request-id` từ header hoặc sinh `req-<8 ký tự hex>`.
   - Gọi `bind_contextvars(correlation_id=correlation_id)`.
   - Lưu ID vào `request.state.correlation_id`.
   - Thêm `x-request-id` và `x-response-time-ms` vào response.
2. Trong `chat()`, bind các field trước `request_received`:
   - `user_id_hash`
   - `session_id`
   - `feature`
   - `model`
   - `env`
3. Phần mở rộng: response lỗi vẫn trả `x-request-id`.

### B — PII scrubbing

1. Đăng ký `scrub_event` sau `TimeStamper` và trước `JsonlFileProcessor`.
2. Scrub mọi giá trị string trong event dict, gồm payload/nested dictionary.
3. Kiểm tra tối thiểu email, số điện thoại Việt Nam, CCCD và thẻ tín dụng.
4. Không log raw `user_id`; chỉ dùng `user_id_hash`.

### C — Error rate

Tính tỷ lệ lỗi trong `snapshot()`:

```text
error_rate_pct = total_errors / (successful_requests + total_errors) * 100
```

Giá trị phải bằng `0.0` nếu chưa có request.

### E — Liên kết trace và log

`correlation_id` phải được truyền từ middleware qua `main.py` vào agent và xuất hiện trong Langfuse trace metadata. Không cần đọc contextvars trực tiếp nếu ID đã được truyền qua tham số.

## Thứ tự phối hợp

```text
A: Middleware + enrichment
        ├── B: PII scrubbing (song song)
        └── C: Error rate (song song)
                  ↓
          E: load test → validator → pytest → evidence
                  ↓
          D: dùng fields đã xác nhận để chuẩn bị CP2
```

## Quy trình kiểm tra

Sau khi evidence CP0 đã được lưu, E xóa log cũ và tạo dữ liệu CP1 mới:

```powershell
Remove-Item -Path data/logs.jsonl -ErrorAction SilentlyContinue
uvicorn app.main:app --reload --env-file .env
python scripts/load_test.py
python scripts/validate_logs.py
python -m pytest -q
```

Kiểm tra thủ công PII:

```powershell
Select-String -Path data/logs.jsonl -Pattern '@|4111'
Select-String -Path data/logs.jsonl -Pattern 'REDACTED'
```

## Tiêu chí nghiệm thu

- `data/logs.jsonl` có log JSON hợp lệ.
- `correlation_id` không còn là `MISSING` và có dạng `req-<8 hex>`.
- Response header, log và trace metadata dùng cùng correlation ID.
- `request_received` có `user_id_hash`, `session_id`, `feature`, `model`, `env`.
- Email, số điện thoại, CCCD và thẻ không xuất hiện nguyên văn.
- `python scripts/validate_logs.py` đạt ít nhất **80/100**.
- `python -m pytest -q` pass hoàn toàn.

## Evidence cần lưu

Lưu vào `submission/evidence/`:

- Ảnh hoặc file kết quả `validate_logs.py`.
- Một log có correlation ID và metadata request.
- Một log có `[REDACTED_*]`.
- Trace có metadata `correlation_id`.

Ghi lại score CP1 trong `submission/REPORT.md`; giữ score CP0 làm baseline, không thay thế.

## Câu hỏi phản biện

**Khác biệt CP0 và CP1:** CP0 có JSON log nhưng thiếu correlation ID/enrichment nên không thể nối các sự kiện thuộc cùng request. CP1 cho phép nối log với trace theo correlation ID, lọc theo metadata và vẫn bảo vệ PII.

**Vì sao phải gọi `clear_contextvars()`?** Structlog giữ context theo request/task. Nếu context cũ không được xóa, metadata của request trước có thể xuất hiện trong request sau khi worker hoặc task được tái sử dụng, gây sai evidence và rò rỉ dữ liệu.
