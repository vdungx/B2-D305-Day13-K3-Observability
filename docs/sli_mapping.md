# SLI to Log/Metrics Mapping (CP1 -> CP2)

Tài liệu này định nghĩa cách ánh xạ (mapping) giữa các Service Level Indicators (SLI) và các trường (fields) có sẵn trong hệ thống Logging / Metrics mà nhóm đã hoàn thành trong CP1. Bảng này sẽ được sử dụng để thiết lập Dashboard và Alert Rules trong CP2.

## Bảng Mapping Chi Tiết

| SLI (Indicator) | Mục tiêu (SLO) | Nguồn dữ liệu (Log/Metric Field) | Mô tả / Cách tính |
|---|---|---|---|
| **Latency** (Độ trễ) | P95 < 3000ms | - Metrics: `/metrics` trả về `latency_p95`<br>- Logs: field `latency_ms` trong event `response_sent` | Sử dụng endpoint `/metrics` để theo dõi real-time. Logs có thể dùng để vẽ biểu đồ phân tán (scatter plot) từng request một. |
| **Error Rate** (Tỷ lệ lỗi) | < 2% | - Metrics: `/metrics` trả về `error_rate_pct`<br>- Logs: tính dựa trên event `error` hoặc status code != 200 | Tỷ lệ phần trăm giữa tổng số request lỗi và tổng số request. Endpoint `/metrics` đã tổng hợp sẵn giá trị này. |
| **Cost** (Chi phí) | < $2.5 / ngày | - Metrics: `/metrics` trả về `total_cost_usd`<br>- Logs: field `cost_usd` | Chi phí tính trên từng request dựa vào số token tiêu thụ. SRE có thể thiết lập alert khi `total_cost_usd` vượt quá ngưỡng hàng ngày. |
| **Quality** (Chất lượng) | Trung bình > 0.75 | - Metrics: `/metrics` trả về `quality_avg`<br>- Logs: field `quality_score` | Điểm chất lượng trung bình của mô hình LLM, lấy trực tiếp từ field `quality_avg`. Nếu giảm dưới 0.75 hoặc 0.6 sẽ kích hoạt cảnh báo suy thoái (degradation). |

## Chuẩn bị cho CP2
- SRE sẽ lấy các config từ `config/slo.yaml` và `config/alert_rules.yaml` để thiết lập cảnh báo thực tế (Prometheus/Grafana hoặc công cụ giám sát tương tự).
- Đảm bảo endpoint `/metrics` liên tục hoạt động (Uptime > 99.9%) để hệ thống cảnh báo có thể cào (scrape) dữ liệu.
