# Checkpoint CP2 — Metrics, Traces, Dashboard & Alerts

**Thời lượng:** 60 phút  
**Bắt đầu:** 1:30  
**Mục tiêu:** Theo dõi API AI qua metrics, traces Langfuse, dashboard, SLO và alert có runbook xử lý.

## Phân công nhóm 5 người

| Thành viên | Vai trò | Công việc CP2 | Bàn giao |
|---|---|---|---|
| A | API & Middleware | Xác nhận `/metrics` phản ánh request thành công và lỗi; kiểm tra response lỗi vẫn có correlation ID; hỗ trợ đối chiếu correlation ID từ trace sang log khi điều tra. | Kết quả kiểm tra API/metrics và mapping trace → log. |
| B | Security Engineer | Audit PII trong `data/logs.jsonl`, trace metadata/input/output và prompt; xác nhận không commit `.env` hay Langfuse keys. | Checklist bảo mật và bằng chứng không lộ PII. |
| C | Metrics & Dashboard | Hoàn thiện `error_rate_pct`; viết dashboard đủ sáu nhóm chỉ số theo contract. | `app/metrics.py`, `docs/dashboard-spec.md`, dashboard/evidence. |
| D | SRE & Alerts Engineer | Chốt SLO, ba alert symptom-based và runbook đầy đủ. | `config/slo.yaml`, `config/alert_rules.yaml`, `docs/alerts.md`. |
| E | QA & Chief Investigator / Langfuse | Là người duy nhất vận hành Langfuse: tạo ≥10 traces, kiểm tra waterfall, chụp evidence, chạy kiểm thử cuối và tổng hợp báo cáo. | Evidence trace/waterfall; kết quả test và nội dung CP2 trong `submission/REPORT.md`. |

## Phần A — Traces Langfuse (E chủ trì)

1. Kiểm tra `.env` có `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`; không gửi key vào chat hoặc commit Git.
2. Khởi động API với `.env`, sau đó chạy load test để tạo ít nhất 10 requests/traces.
3. Trên Langfuse, xác nhận mỗi trace có user ID đã hash, session ID, tags `lab`, feature, model và metadata `correlation_id`.
4. Mở một trace và kiểm tra waterfall theo cấu trúc:

```text
process-chat-request (SPAN)
├── retrieve-context (RETRIEVER)
└── generate-response (GENERATION)
```

Không thêm decorator trùng lặp vào `mock_rag.py` hoặc `mock_llm.py`: ứng dụng đã tạo sub-span rõ ràng cho RAG và LLM.

5. Nếu trace báo prompt `day13-chat` fallback, tạo prompt text `day13-chat` với label `production` trong Langfuse để trace dùng managed prompt.

## Phần B — Dashboard (C chủ trì)

Nguồn chuẩn của dashboard là `data/logs.jsonl` theo [dashboard contract](../config/dashboard.yaml). Endpoint `/metrics` hữu ích để kiểm tra nhanh runtime nhưng không thay thế contract dashboard.

| Nhóm | Panel đề xuất | Nguồn / trường | Đơn vị | SLO / threshold |
|---|---|---|---|---|
| Latency | Line P50/P95/P99 | `response_sent.latency_ms` | ms | P95 ≤ 3000 ms |
| Traffic | Request rate theo phút | `request_received` | req/min | Hiển thị baseline, không alert khi traffic thấp |
| Error | Error rate và bảng breakdown | `request_failed.error_type` | % | ≤ 2% SLO; alert > 5%/3 phút |
| Cost | Cost theo thời gian và tổng | `response_sent.cost_usd` | USD | ≤ $2.50/ngày |
| Tokens | Tổng input/output tokens | `response_sent.tokens_in/tokens_out` | tokens | Theo dõi xu hướng/capacity |
| Quality | Quality proxy trung bình | `response_sent.quality_score` | 0–1 | ≥ 0.75 |

Yêu cầu trình bày:

- Khoảng thời gian mặc định: 60 phút; refresh 15–30 giây nếu công cụ hỗ trợ.
- Mỗi panel ghi rõ tên, đơn vị, nguồn, truy vấn/metric và threshold/SLO line.
- Chỉ giữ 6–8 panel ở màn hình chính; ưu tiên tổng quan trước, breakdown sau.
- Chạy `python scripts/validate_dashboard.py` trước khi chụp evidence.

## Phần C — SLO, alerts và runbook (D chủ trì)

Chốt SLO nhóm trong `config/slo.yaml`:

| SLI | Objective | Target |
|---|---:|---:|
| `latency_p95_ms` | < 3000 ms | 99.5% |
| `error_rate_pct` | < 2% | 99.0% |
| `daily_cost_usd` | < $2.50/ngày | 100% |
| `quality_score_avg` | ≥ 0.75 | 95.0% |

Điền đúng ba alert trong `config/alert_rules.yaml`:

1. `high_latency_p95`: warning — `latency_p95 > 3000ms for 5 minutes`.
2. `elevated_error_rate`: critical — `error_rate_pct > 5 for 3 minutes`.
3. `cost_budget_exceeded`: warning — `daily_cost_usd > 2.5`.

Mỗi mục trong `docs/alerts.md` phải có: tên, severity, SLI/SLO, điều kiện, tác động người dùng, ba bước kiểm tra đầu tiên, mitigation tạm thời và owner.

Ba bước điều tra đầu tiên nên theo thứ tự **metrics → traces → logs**:

1. Xác nhận metric và phạm vi ảnh hưởng theo feature/thời điểm.
2. Mở trace đại diện, xác định span bất thường.
3. Dùng `correlation_id` của trace để lọc log, xác định nguyên nhân cụ thể.

## Trình tự phối hợp

```text
C: metrics + dashboard spec ─┐
D: SLO + alerts + runbook ───┼──> E: load test → Langfuse → evidence → test cuối
A: API/correlation kiểm tra ─┤
B: audit PII ────────────────┘
```

Gợi ý chia thời gian:

| Thời gian | Hoạt động |
|---:|---|
| 0–10 phút | C kiểm tra metrics; D chốt SLO; E xác nhận Langfuse; A/B rà API và PII. |
| 10–30 phút | C hoàn thiện dashboard spec; D hoàn thiện rules/runbook. |
| 30–45 phút | E chạy load test, kiểm tra ≥10 traces và chụp trace list/waterfall. |
| 45–60 phút | C/D validate tài liệu; A/B audit; E gom evidence và chạy test cuối. |

## Lệnh kiểm tra

Terminal 1:

```powershell
uvicorn app.main:app --reload --env-file .env
```

Terminal 2:

```powershell
python scripts/load_test.py
curl http://localhost:8000/metrics | python -m json.tool
python scripts/validate_dashboard.py
python -m pytest -q
```

Nếu máy không nhận lệnh `python`, dùng Python trong môi trường đã kích hoạt hoặc tạo lại `.venv` với đúng dependency trước khi chạy.

## Tiêu chí nghiệm thu CP2

- Langfuse hiển thị ít nhất 10 traces.
- Có screenshot danh sách traces và waterfall thấy span cha/con, thời gian thực thi.
- `docs/dashboard-spec.md` hoặc dashboard thực tế mô tả đầy đủ sáu nhóm chỉ số, nguồn, đơn vị, time range và SLO line.
- `config/alert_rules.yaml` có ba alert hợp lệ, đều `type: symptom-based`.
- `docs/alerts.md` có ba runbook hoàn chỉnh.
- `python -m pytest -q` pass hoàn toàn.

## Evidence cần lưu

Lưu vào `submission/evidence/`:

- Ảnh danh sách ≥10 Langfuse traces.
- Ảnh waterfall một trace có `process-chat-request`, `retrieve-context`, `generate-response`.
- Ảnh dashboard hoặc dashboard spec hoàn thiện.
- Kết quả `validate_dashboard.py` và pytest nếu yêu cầu nộp evidence.

Ghi trạng thái CP2 và đường dẫn evidence vào `submission/REPORT.md`.

## Câu hỏi phản biện

Alert nên dựa trên **triệu chứng người dùng thấy** như chậm, lỗi, chi phí vượt ngân sách thay vì tên hàm hoặc lỗi implementation. Triệu chứng ổn định hơn khi code được refactor, phản ánh đúng tác động dịch vụ và hướng on-call đến kiểm tra metrics → traces → logs thay vì đoán trước nguyên nhân.
