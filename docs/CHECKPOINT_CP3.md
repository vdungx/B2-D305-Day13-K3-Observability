# Checkpoint CP3 — Challenge Incident Investigation

**Thời lượng:** 60 phút  
**Bắt đầu:** 2:30  
**Mục tiêu:** Điều tra incident chính thức bằng chuỗi bằng chứng **Metrics → Traces → Logs**, kết luận root cause, đề xuất mitigation/fix/prevention và hoàn thiện phần challenge trong báo cáo.

## Guardrails

- Chỉ chạy challenge sau khi Lab Coach đã release `config/challenge.json`. File hiện có trong repository là nguồn sự thật; **không tự sửa file này**.
- Không kết luận chỉ từ tên incident hoặc đọc source code. Báo cáo phải có metric, trace ID và log/correlation ID khớp với nhau.
- Không chụp hoặc commit `.env`, API key hay PII raw.
- Giữ incident bật chỉ trong lúc thu evidence; tắt lại sau khi hoàn tất.

## Bối cảnh challenge K3

| Thuộc tính | Giá trị từ `config/challenge.json` |
|---|---|
| Challenge ID | `day13-k3-observability-v1` |
| Cohort | `K3` |
| Incident được release | `rag_slow` |
| Feature ảnh hưởng | `refund` |
| Ngưỡng latency | 2000 ms |
| Số request challenge | 5 |

Thông tin trên giúp xác định phạm vi. Root cause chỉ được ghi vào report sau khi trace và log xác nhận.

## Phân công 5 thành viên

| Thành viên | Nhiệm vụ CP3 | Bàn giao |
|---|---|---|
| A — API & Middleware | Xác nhận API vẫn trả correlation ID; hỗ trợ tái hiện request bị ảnh hưởng; đối chiếu CID từ trace với dòng log. | Response/header và log reference có cùng CID. |
| B — Security | Rà soát log/trace/ảnh trước khi lưu evidence; che hoặc loại bỏ PII/secret nếu có. | Security sign-off cho evidence/report. |
| C — Metrics & Dashboard | Chụp metric cho triệu chứng, thời điểm và feature ảnh hưởng; so sánh baseline với incident. | Ảnh/số liệu latency và phạm vi ảnh hưởng. |
| D — SRE & Alerts | Dùng runbook để triage; xác định severity, mitigation tức thời, fix và preventive measure. | Timeline xử lý và action/owner. |
| E — QA, Chief Investigator & Langfuse | Chạy challenge, chọn trace bất thường, chụp waterfall, lấy trace ID/CID, dẫn dắt kết luận và cập nhật report. | Evidence Metrics → Traces → Logs, report và demo. |

## Chuẩn bị trước khi chạy

1. Hoàn thành CP1: log có correlation ID và PII scrubber đã bật.
2. Hoàn thành CP2: Langfuse keys hoạt động, dashboard/metrics đọc được, alert runbook đã có.
3. Mở hai terminal trong root repository.

Terminal 1:

```powershell
uvicorn app.main:app --reload --env-file .env
```

Terminal 2 — kiểm tra nhanh:

```powershell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/metrics | python -m json.tool
```

Nếu máy không nhận `python`, kích hoạt môi trường `.venv` đúng version trước khi chạy lệnh.

## Quy trình điều tra bắt buộc

### 1. Tạo baseline ngắn (C, E)

Trước khi bật incident, chạy một request `refund` hoặc load test bình thường và ghi nhận latency/trace làm mốc. Không xóa evidence CP1/CP2; nếu cần dữ liệu tách biệt, chụp timestamp hoặc dùng session ID challenge để lọc.

### 2. Bật incident chính thức (E)

```powershell
python scripts/inject_incident.py
```

Kiểm tra response trả `rag_slow: true`. Không dùng `--scenario` ở challenge chính thức vì tham số đó chỉ dành cho practice.

### 3. Chạy input challenge (E)

```powershell
python scripts/load_test.py --challenge --concurrency 5
```

Ghi lại terminal output và thời điểm chạy. Các request thuộc feature `refund`; kỳ vọng điều tra khi latency vượt ngưỡng 2000 ms.

### 4. Bắt đầu từ metrics (C)

```powershell
curl http://127.0.0.1:8000/metrics | python -m json.tool
```

Thu thập:

- `latency_p50`, `latency_p95`, `latency_p99` và thời điểm incident;
- traffic/request count để biết cỡ mẫu;
- `error_rate_pct`/`error_breakdown` để phân biệt chậm với lỗi;
- cost/tokens/quality nếu có thay đổi đáng kể.

Kết luận ở bước này chỉ là **triệu chứng**, ví dụ: “latency P95 của luồng refund vượt 2000 ms”; chưa gọi đây là root cause.

### 5. Khoanh vùng bằng trace (E, A)

Trong Langfuse, lọc traces theo thời gian challenge, tag `refund` hoặc session ID `k3-challenge-*`. Mở một trace latency cao và chụp waterfall.

Kiểm tra các yêu cầu trace:

```text
chat-response
└── process-chat-request
    ├── retrieve-context
    └── generate-response
```

Ghi lại:

- Trace ID;
- tổng duration;
- duration của `retrieve-context` và `generate-response`;
- user hash/session ID/tag/metadata `correlation_id`;
- prompt name/label/version nếu trace hiển thị.

Span có duration cao nhất là vị trí cần điều tra tiếp, không tự động đồng nghĩa với nguyên nhân mã nguồn.

### 6. Chứng minh bằng logs (A, E, B)

Lấy `correlation_id` từ trace metadata, sau đó lọc log:

```powershell
Select-String -Path data/logs.jsonl -Pattern '<correlation-id>'
```

Đối chiếu tối thiểu các event `request_received` và `response_sent` (hoặc `request_failed` nếu có):

- cùng correlation ID;
- feature/session/model/environment đúng request challenge;
- latency hoặc error phù hợp với metric và trace;
- payload đã redact PII.

Nếu load-test output không hiện CID với một HTTP 500, ưu tiên header `x-request-id` của response hoặc tìm request theo timestamp/session ID; không tự gán CID thủ công.

### 7. Kết luận và hành động (D, E)

Viết kết luận theo mẫu:

| Mục | Nội dung cần ghi |
|---|---|
| Triệu chứng | Metric nào xấu, giá trị/threshold, khoảng thời gian, feature ảnh hưởng. |
| Vị trí | Trace ID; span nào chậm/lỗi và duration của nó. |
| Root cause | Chỉ nêu khi log và trace cùng xác nhận. |
| Mitigation tạm thời | Cách giảm ảnh hưởng ngay, có owner. |
| Fix action | Thay đổi kỹ thuật được đề xuất, owner và tiêu chí kiểm chứng. |
| Preventive measure | Alert/SLO/test/capacity control để phát hiện hoặc ngăn tái diễn. |

Với challenge `rag_slow`, một hướng giả thuyết hợp lý là retrieval chậm. Vẫn phải dùng waterfall và CID/log để chứng minh trước khi ghi đó là root cause chính thức.

### 8. Tắt incident và kiểm tra hậu xử lý (E, A)

```powershell
python scripts/inject_incident.py --disable
curl http://127.0.0.1:8000/health
```

Chạy một request `refund` sau khi tắt để xác nhận latency trở lại bình thường. Lưu evidence trước/sau nếu có thời gian.

## Evidence cần lưu

Lưu trong `submission/evidence/` với tên dễ truy vết, ví dụ:

| Tên gợi ý | Nội dung |
|---|---|
| `cp3_metrics_incident.png` | Dashboard hoặc `/metrics` thể hiện triệu chứng. |
| `cp3_trace_waterfall.png` | Waterfall trace bất thường, thấy các span và duration. |
| `cp3_trace_details.txt` | Trace ID, session ID, correlation ID, duration đã ghi lại. |
| `cp3_log_correlation.txt` | Các dòng log cùng CID đã được redact. |
| `cp3_recovery.png` | Evidence tắt incident hoặc latency hồi phục (nếu có). |

Không lưu raw log có PII. Dẫn các đường dẫn tương đối này vào `submission/REPORT.md`, mục 6.

## Tiêu chí nghiệm thu CP3

- [ ] Incident chính thức được bật/tắt bằng script, không sửa `config/challenge.json`.
- [ ] Có metric chứng minh triệu chứng và phạm vi ảnh hưởng.
- [ ] Có Langfuse trace ID + waterfall để khoanh vùng span bất thường.
- [ ] Có correlation ID nối trace với log line liên quan.
- [ ] Root cause được kết luận bằng đủ Metrics → Traces → Logs.
- [ ] Có mitigation, fix action và preventive measure có owner.
- [ ] Report/evidence không lộ PII hoặc secret.
- [ ] Chạy `python -m pytest -q` pass trước khi nộp.

## Kịch bản demo 3 phút

1. C mở dashboard/`/metrics`: “Refund latency vượt SLO.”
2. E mở trace: “`retrieve-context` chiếm phần lớn thời gian request.”
3. A/E mở log bằng correlation ID: “Đây là đúng request refund đã quan sát.”
4. D chốt root cause, mitigation/fix/prevention; B xác nhận evidence không lộ dữ liệu nhạy cảm.
