# CP2 Security Checklist — Role B (Security Engineer)

Phạm vi: audit PII trong logs/trace/prompt, xác nhận Git sạch secret, review evidence trước khi nộp.

## 1. Git / secret hygiene

- `git status --short` sạch, không có file chưa track chứa secret.
- `.env` không nằm trong `git ls-files` (được `.gitignore` chặn).
- Không có `secret`/`key` file nào bị track ngoài code.
- `data/logs.jsonl` và `data/audit.jsonl` đều bị `.gitignore` (không commit log runtime có thể chứa PII trước khi redact).

Kết quả: **PASS**.

## 2. PII trong logs (`data/logs.jsonl`)

- `python scripts/validate_logs.py` → `Potential PII leaks detected: 0`, hạng mục `PII scrubbing` **PASSED**.
- Spot-check độc lập bằng regex email/SĐT VN/số thẻ trực tiếp trên `data/logs.jsonl`: không tìm thấy giá trị raw nào ngoài các marker `[REDACTED_*]`.
- Số lượng marker `[REDACTED_*]` xuất hiện: 6 — xác nhận bộ scrubber đang hoạt động trên traffic thật, không chỉ là không có input nhạy cảm.

Kết quả: **PASS**.

Lưu ý ngoài phạm vi security (không tự sửa): `validate_logs.py` báo tổng điểm 50/100 do 20 record thiếu required fields/enrichment — đây là log tồn đọng từ nhiều lần chạy thử nghiệm khác nhau trong ngày, thuộc phạm vi enrichment của Role A. Đề xuất Role E xoá `data/logs.jsonl` và chạy lại `load_test.py` một lần sạch trước khi chụp evidence cuối, để điểm phản ánh đúng trạng thái CP1/CP2.

## 3. PII trong trace (Langfuse input/output/metadata)

Audit bằng `scripts/audit_langfuse_trace.py` (so khớp input/output của mọi observation với `PII_PATTERNS` trong `app/pii.py`) trên các session:

| Session | PII leaks | Ghi chú |
|---|---|---|
| s01–s06 (load test) | none | `s01`, `s05` có redaction marker (query gốc chứa PII test) |
| s_prompt_baseline | none | trace hợp lệ đầy đủ (SPAN/RETRIEVER/GENERATION) |
| s_prompt_candidate | none | trace hợp lệ đầy đủ |

Kết quả: **PASS** — không có input/output/metadata nào lộ PII dạng raw trên toàn bộ trace đã kiểm tra.

Lưu ý ngoài phạm vi security: một số trace từ load test (s02–s04, s06) bị script báo `KHÔNG HỢP LỆ` không phải vì PII mà vì observation `retrieve-context` đôi khi được ghi nhận dưới type `SPAN` thay vì `RETRIEVER` — nghi do race condition khi chạy nhiều request đồng thời qua OTel exporter. Đây là vấn đề cấu trúc trace (Role E), không phải PII leak.

## 4. PII trong prompt

- Prompt `day13-chat` (v1 và v2) chỉ chứa placeholder `{{feature}}`, `{{docs}}`, `{{message}}` — không có dữ liệu người dùng hard-code trong template.
- `app/agent.py` dùng `scrub_text()` trước khi đưa `message`/`docs`/`answer` vào bất kỳ trường `input`/`output` nào gửi lên Langfuse (xác nhận qua đọc code, khớp với kết quả audit mục 3).

Kết quả: **PASS**.

## 5. Review evidence trước khi chụp/nộp

- Phát hiện và sửa: `submission/REPORT.md` có merge-conflict markers (`<<<<<<<`/`=======`/`>>>>>>>`) bị commit thẳng vào nội dung (commit `e5e0a2a Merge conflict`) — đã merge lại nội dung hai bên và xác nhận `git grep` không còn marker nào trong repo.
- Chưa có evidence trace waterfall/screenshot Langfuse thực tế trong `submission/evidence/` — cần Role E bổ sung trước khi nộp.
- Chưa có ảnh dashboard runtime — cần Role C bổ sung.

## Kết luận

Không phát hiện PII hoặc secret bị lộ trong logs, traces hoặc prompt tại thời điểm audit CP2. Repo Git sạch secret. Đã sửa một lỗi report bị hỏng do merge conflict chưa resolve. Các điểm còn thiếu (enrichment score, trace type, screenshot) đã được note lại cho đúng người phụ trách, không tự ý sửa ngoài phạm vi Security.
