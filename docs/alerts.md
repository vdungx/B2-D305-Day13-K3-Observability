# Alert Runbooks

Tài liệu này chứa các hướng dẫn xử lý sự cố (runbook) cho 3 loại cảnh báo chính của hệ thống. Khi nhận được cảnh báo, on-call engineer cần tuân thủ các bước điều tra từ tổng quan đến chi tiết (Metrics -> Traces -> Logs).

---

## 1. high_latency_p95
- **Severity:** `warning`
- **SLI/SLO bị vi phạm:** `latency_p95_ms` (Mục tiêu: < 3000ms)
- **Điều kiện (Condition):** `latency_p95 > 3000ms for 5 minutes`
- **Tác động người dùng (User Impact):** Người dùng phải chờ đợi lâu hơn bình thường để nhận câu trả lời từ AI (chat completion chậm), gây giảm trải nghiệm.
- **3 bước điều tra đầu tiên:**
  1. **Metrics:** Kiểm tra Dashboard xem độ trễ tăng đột biến ở toàn bộ hệ thống hay chỉ ở một LLM provider/feature cụ thể (vd: tính năng `summary` hay `qa`).
  2. **Traces:** Truy cập Langfuse, lọc các traces có latency > 3000ms. Xem biểu đồ thác (waterfall) để tìm span nào chiếm nhiều thời gian nhất (ví dụ: `retrieve-context` hay `generate-response`).
  3. **Logs:** Copy `correlation_id` của trace bị chậm, tra cứu trong file logs/Kibana để xem có cảnh báo (warning/error) nào từ database timeout hoặc third-party API rate limit không.
- **Mitigation (Khắc phục tạm thời):** Tắt tạm thời tính năng bị chậm bằng cách gọi endpoint `/incidents/{name}/enable` (nếu có fallback), hoặc rollback version của prompt nếu lỗi do prompt mới quá phức tạp.
- **Owner:** SRE Team

---

## 2. elevated_error_rate
- **Severity:** `critical`
- **SLI/SLO bị vi phạm:** `error_rate_pct` (Mục tiêu: < 2%)
- **Điều kiện (Condition):** `error_rate_pct > 5 for 3 minutes`
- **Tác động người dùng (User Impact):** Người dùng gặp lỗi 500 khi chat, không nhận được phản hồi. Làm gián đoạn hoàn toàn luồng nghiệp vụ.
- **3 bước điều tra đầu tiên:**
  1. **Metrics:** Xem panel Error Breakdown trên Dashboard để biết loại lỗi nào (ví dụ: `ConnectTimeout`, `RateLimitError`) đang chiếm đa số.
  2. **Traces:** Lọc các trace bị đánh dấu `error` trên Langfuse. Kiểm tra xem bước nào văng lỗi (RAG fail hay LLM fail).
  3. **Logs:** Lấy `correlation_id` và tìm dòng log `request_failed` tương ứng để đọc chi tiết `payload.detail` và stack trace.
- **Mitigation (Khắc phục tạm thời):** Nếu LLM provider bị sập, chuyển traffic sang mô hình dự phòng (ví dụ chuyển từ Claude sang GPT-3.5). Nếu do RAG database, thử restart connection pool.
- **Owner:** SRE Team

---

## 3. cost_budget_exceeded
- **Severity:** `warning`
- **SLI/SLO bị vi phạm:** `daily_cost_usd` (Mục tiêu: < $2.50/ngày)
- **Điều kiện (Condition):** `daily_cost_usd > 2.5`
- **Tác động người dùng (User Impact):** Người dùng không bị ảnh hưởng trực tiếp, nhưng công ty đang chịu tổn thất tài chính và có rủi ro cạn ngân sách chạy API.
- **3 bước điều tra đầu tiên:**
  1. **Metrics:** Kiểm tra biểu đồ Token Usage/Cost để xem sự gia tăng là do lượng traffic tăng đột biến (DDoS/Spam) hay do số tokens/request tăng.
  2. **Traces:** Lọc các trace có lượng tokens/cost cao nhất. Xem metadata của trace xem người dùng (`user_id_hash`) nào đang gửi request, hoặc prompt version nào ngốn token.
  3. **Logs:** Truy vấn log với bộ lọc `cost_usd > 0.05` để lấy ra danh sách các request cụ thể và xem nội dung preview.
- **Mitigation (Khắc phục tạm thời):** Block tạm thời user bị nghi ngờ spam, hoặc áp dụng Rate Limit. Nếu do prompt mới sinh ra quá nhiều tokens, rollback prompt.
- **Owner:** SRE Team
