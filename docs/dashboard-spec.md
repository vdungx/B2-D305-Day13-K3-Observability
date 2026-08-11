# Yêu cầu dashboard

Contract có thể kiểm tra bằng máy nằm tại `config/dashboard.yaml`. Hướng dẫn dựng và kiểm tra runtime nằm tại [DASHBOARD_SETUP.md](DASHBOARD_SETUP.md).

Dashboard chính cần đủ 6 nhóm thông tin:

1. Latency P50/P95/P99.
2. Traffic: request count hoặc QPS.
3. Error rate và breakdown theo loại lỗi.
4. Cost theo thời gian.
5. Tổng token input/output.
6. Quality proxy.

Tiêu chuẩn trình bày:

- Khoảng thời gian mặc định: 1 giờ.
- Tự refresh mỗi 15–30 giây nếu công cụ hỗ trợ.
- Có threshold hoặc SLO line.
- Ghi rõ đơn vị.
- Chỉ giữ 6–8 panel quan trọng ở lớp chính.
- Screenshot phải nhìn được tên panel và khoảng thời gian.

Kiểm tra contract trước khi chụp evidence:

```bash
python scripts/validate_dashboard.py
```

## Mapping 6 panel (triển khai Streamlit: `scripts/dashboard_app.py`)

Nguồn chuẩn: `data/logs.jsonl`. Trường `query` trong `config/dashboard.yaml` là pseudocode; bảng dưới là phép tính thực tế bằng pandas. `/metrics` chỉ dùng để kiểm tra nhanh runtime, **không** là nguồn dashboard.

| id | Title | Source (event + field) | Aggregation | Unit | Time range | Threshold / SLO line |
|---|---|---|---|---|---|---|
| latency | Latency percentiles | `response_sent.latency_ms` | P50 / P95 / P99 | ms | 60 phút | P95 ≤ 3000 |
| traffic | Request traffic | `request_received` | count, rate/phút | req/min | 60 phút | ≥ 1 (baseline) |
| errors | Error rate and breakdown | `request_received` + `request_failed.error_type` | error_rate_pct, breakdown theo type | % | 60 phút | ≤ 2 (SLO); alert > 5%/3 phút |
| cost | Cost over time | `response_sent.cost_usd` | sum/phút + tổng | USD | 60 phút | tổng ≤ 2.50 |
| tokens | Input and output tokens | `response_sent.tokens_in` / `tokens_out` | sum từng field | tokens | 60 phút | ≤ 50000 |
| quality | Quality proxy | `response_sent.quality_score` | mean | 0–1 | 60 phút | ≥ 0.75 |

- Refresh: 30 giây (`refresh_seconds` trong `config/dashboard.yaml`), auto-refresh bằng `st.fragment(run_every=30)`.
- Mỗi panel hiển thị tiêu đề kèm đơn vị, caption nguồn (`source: <event>.<field>`) và threshold/SLO line (Altair `mark_rule` màu đỏ nét đứt).
- Header chính hiển thị `Window: start → end UTC · source: data/logs.jsonl · refresh Ns` để ảnh chụp chứng minh time range.
