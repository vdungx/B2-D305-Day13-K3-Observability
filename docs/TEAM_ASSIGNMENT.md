# Phân công nhóm xuyên suốt lab — CP0 đến CP3

**Nhóm:** 5 thành viên A–E  
**Nguyên tắc phối hợp:** điều tra và demo theo luồng **Metrics → Traces → Logs**. Không commit `.env`/secret/PII; không tự sửa `config/challenge.json`.

## Bảng tổng hợp

| Thành viên | Vai trò chính | CP0 — Setup & baseline | CP1 — Logging, CID, PII | CP2 — Metrics, traces, dashboard, alerts | CP3 — Challenge & nộp bài | Bàn giao cuối |
|---|---|---|---|---|---|---|
| **A** | API & Middleware | Khởi động API, kiểm tra `/health`; hỗ trợ xác nhận request/response. | Hoàn thiện middleware correlation ID, enrich context trong `/chat`, exception handler giữ `x-request-id`. | Xác nhận `/metrics` và response lỗi đúng; hỗ trợ liên kết correlation ID trace → log. | Hỗ trợ tái hiện request lỗi/chậm và đề xuất thay đổi API/middleware nếu cần. | Code API, kết quả test endpoint, mapping CID. |
| **B** | Security Engineer | Kiểm tra `.gitignore`, bảo đảm không đưa `.env`/key vào Git. | Bật PII scrubber, bổ sung regex, audit log không lộ PII. | Audit PII trong logs, trace input/output/metadata và prompt; review evidence trước nộp. | Kiểm tra evidence challenge/report không chứa PII hoặc secret. | Checklist security, log `[REDACTED_*]`, xác nhận Git sạch secret. |
| **C** | Metrics & Dashboard | Ghi baseline validator, khảo sát `/metrics` và contract dashboard. | Thêm/kiểm tra `error_rate_pct` và test công thức metrics. | Hoàn thiện dashboard 6 nhóm, `docs/dashboard-spec.md`, chạy `validate_dashboard.py`. | Đọc metric để phát hiện triệu chứng, cung cấp ảnh/số liệu trước–sau incident. | Dashboard spec/ảnh, validator hợp lệ, số liệu incident. |
| **D** | SRE & Alerts Engineer | Xem SLO mặc định, lập danh sách SLI cần theo dõi. | Chuẩn bị mapping log/metric → SLI/SLO/alert. | Chỉnh `slo.yaml`, ba alert symptom-based, ba runbook trong `docs/alerts.md`. | Dùng runbook điều phối triage; đề xuất mitigation và preventive measure. | SLO, alert rules, runbook, tóm tắt on-call. |
| **E** | QA, Chief Investigator & Langfuse | Cấu hình Langfuse; chạy load test, pytest; lưu baseline/evidence CP0. | Chạy load test/validator/pytest, xác nhận trace có correlation ID, lưu evidence CP1. | **Người vận hành Langfuse:** tạo ≥10 traces, kiểm tra prompt v1/v2 + label/rollback, chụp trace list/waterfall; gom evidence CP2. | Bật challenge, dẫn dắt Metrics → Traces → Logs; ghi trace ID/log line/root cause; hoàn thiện REPORT và demo. | Evidence, report, test cuối, demo Metrics → Traces → Logs. |

## CP0 — Setup & baseline (0:00–0:30)

| Người | Việc cụ thể | Tiêu chí xong | File/evidence |
|---|---|---|---|
| A | Chạy `uvicorn app.main:app --reload --env-file .env`; gọi `/health`. | API phản hồi `ok: true`. | Ảnh terminal hoặc health response. |
| B | Kiểm tra `.env` bị ignore; không gửi/chụp API key. | Không có secret trong Git. | Kết quả `git status --short`/review. |
| C | Gọi `/metrics`, đọc `config/dashboard.yaml`, ghi nhận dữ liệu baseline. | Hiểu 6 nhóm panel và nguồn `data/logs.jsonl`. | Ghi chú dashboard. |
| D | Đọc `config/slo.yaml` và `config/alert_rules.yaml`; liệt kê SLI/SLO ban đầu. | Có danh sách SLI cho CP2. | Ghi chú SRE. |
| E | Cấu hình Langfuse, chạy `load_test.py`, `validate_logs.py`, `pytest`; lưu score baseline vào report. | Có ≥10 JSON logs, baseline validator và pytest chạy được. | `submission/REPORT.md`, `submission/evidence/`. |

## CP1 — Structured logging, Correlation ID & PII (0:30–1:30)

| Người | Việc cụ thể | Tiêu chí xong | File chính |
|---|---|---|---|
| A | `clear_contextvars()`; nhận/tạo `req-<8hex>`; bind context; response headers; enrich `user_id_hash`, `session_id`, `feature`, `model`, `env`; giữ CID khi lỗi. | Header, log và response dùng cùng CID; test middleware pass. | `app/middleware.py`, `app/main.py`. |
| B | Bật `scrub_event`, scrub mọi string/nested dict; thêm pattern PII cần thiết. | Email/điện thoại/số thẻ không raw; có `[REDACTED_*]`. | `app/logging_config.py`, `app/pii.py`. |
| C | Tính `error_rate_pct = errors / (success + errors) × 100`; bổ sung regression tests. | 0% khi trống, 25% với 3 success/1 error, 100% khi toàn lỗi. | `app/metrics.py`, `tests/test_metrics.py`. |
| D | Xác nhận các fields metrics/log đã đủ cho SLO/alert CP2. | Mapping SLI → field có thể dùng. | Ghi chú chuẩn bị CP2. |
| E | Chạy load test sau khi xóa log baseline; chạy validator, pytest; kiểm tra CID xuất hiện trong trace metadata. | `validate_logs.py` ≥80/100; evidence CP1 đầy đủ. | `submission/evidence/`, `submission/REPORT.md`. |

## CP2 — Metrics, traces, dashboard & alerts (1:30–2:30)

| Người | Việc cụ thể | Tiêu chí xong | File/evidence |
|---|---|---|---|
| A | Kiểm thử `/metrics` sau success/error; kiểm tra CID của response lỗi và hỗ trợ E truy log từ trace. | Có quy trình trace CID → log. | Test/kết quả kiểm tra API. |
| B | Kiểm tra logs, trace, prompt không lộ PII; không commit `.env`. | Audit pass trước khi chụp/nộp evidence. | Checklist security. |
| C | Thiết kế 6 panel: latency, traffic, error, cost, tokens, quality; ghi đơn vị, 60 phút mặc định, refresh và SLO line. | `validate_dashboard.py` hợp lệ; dashboard/spec đủ 6 nhóm. | `docs/dashboard-spec.md`, dashboard evidence. |
| D | Chốt SLO; điền high latency, elevated error rate, cost exceeded; viết runbook có 3 bước đầu tiên. | 3 alert `symptom-based`, 3 runbook đủ field. | `config/slo.yaml`, `config/alert_rules.yaml`, `docs/alerts.md`. |
| E | Tạo ≥10 traces; kiểm tra user hash/session/tags/CID; tạo prompt v1/v2, đổi label hoặc rollback; chụp trace list, waterfall và prompt evidence. | Trace/waterfall + prompt-version evidence thật trên Langfuse. | `submission/evidence/`, `submission/REPORT.md`. |

## CP3 — Challenge chính thức (2:30–3:30)

| Người | Việc cụ thể | Tiêu chí xong | File/evidence |
|---|---|---|---|
| A | Hỗ trợ tái hiện request theo feature bị ảnh hưởng; xác nhận correlation ID và hành vi API. | Có request/response đại diện để truy vết. | Terminal output/log reference. |
| B | Đảm bảo log dùng để chứng minh root cause đã redact PII; review report challenge. | Evidence an toàn để nộp. | Security review. |
| C | Đọc dashboard/metrics để nêu **triệu chứng**: latency, error hoặc cost bất thường và phạm vi ảnh hưởng. | Có số liệu metric/ảnh dashboard làm điểm bắt đầu. | Evidence metric. |
| D | Dùng alert runbook điều phối triage; viết mitigation tạm thời và phòng ngừa dài hạn. | Có action owner, mitigation, prevention. | `docs/alerts.md`/REPORT. |
| E | Chỉ sau khi Lab Coach release: chạy `python scripts/inject_incident.py` và `python scripts/load_test.py --challenge --concurrency 5`; mở trace bất thường, lấy trace ID/CID, đối chiếu log, kết luận root cause. | Kết luận dựa trên đủ 3 lớp Metrics → Traces → Logs. | Evidence challenge, `submission/REPORT.md`. |

**Lưu ý CP3:** Challenge K3 hiện là `rag_slow`, feature `refund`, ngưỡng latency 2000 ms. Không sửa `config/challenge.json`; dùng file làm nguồn sự thật của input chính thức.

## Hoàn tất & nộp bài (3:30–4:00)

| Người | Việc chốt | Điều kiện bàn giao |
|---|---|---|
| A | Review code API/middleware và test liên quan. | Không regression correlation ID/error response. |
| B | Quét secret/PII trước commit. | `.env`, `.venv`, cache và log nhạy cảm không vào Git. |
| C | Xác nhận dashboard contract và ảnh dashboard có time range, unit, threshold. | Có evidence 6/6 panel. |
| D | Xác nhận alert rules/runbook liên kết đúng. | Ba alert và ba runbook hoàn chỉnh. |
| E | Điền `submission/REPORT.md`, gắn đường dẫn evidence tương đối, chạy test/validator cuối, chuẩn bị demo. | Có repo URL, commit SHA, evidence và demo flow. |

## Checklist tổng hợp trước khi push/nộp

- [ ] `python -m pytest -q` pass toàn bộ.
- [ ] `python scripts/validate_logs.py` đạt ít nhất 80/100 sau CP1.
- [ ] `python scripts/validate_dashboard.py` hợp lệ 6/6 panel.
- [ ] Có ≥10 traces, waterfall, hai prompt version và evidence label/rollback.
- [ ] Có log correlation ID và PII redaction.
- [ ] Có evidence challenge: metric, trace ID và log line.
- [ ] `submission/REPORT.md` dẫn đến tất cả evidence.
- [ ] `git status --short` không có `.env`, `.venv`, cache hoặc secret/PII.
