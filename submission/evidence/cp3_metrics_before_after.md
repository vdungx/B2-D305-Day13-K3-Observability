# CP3 — Metrics trước/sau incident (thành viên C)

Challenge: `day13-k3-observability-v1` · Incident `rag_slow` · Feature bị ảnh hưởng `refund` · Ngưỡng latency 2000 ms.

## So sánh metric (nguồn `/metrics` + `data/logs.jsonl`)

| Metric | Before (baseline CP1) | During (rag_slow) | After (đã tắt, chạy lại) |
|---|---|---|---|
| Traffic | 10 | 6 (5 refund challenge + 1 smoke) | 10 |
| Latency P50 | 152 ms | 2653 ms | 152 ms |
| Latency P95 | 492 ms | 2653 ms | 600 ms |
| Latency P99 | 713 ms | 2653 ms | 600 ms |
| Error rate | 0.0% | 0.0% | 0.0% |
| Cost (tổng) | 0.0171 USD | 0.0114 USD | 0.0236 USD |
| Feature | qa/summary | **refund** | qa/summary |

## Triệu chứng

- **Latency P95 tăng ~5.4 lần**: 492 ms → **2653 ms**, vượt ngưỡng challenge **2000 ms** và tiến sát SLO P95 ≤ 3000 ms.
- **Phạm vi ảnh hưởng**: các request feature `refund` (5 request chính thức đều chậm ~2657–2665 ms).
- **Error rate = 0%**: đây là suy giảm hiệu năng (latency), không phải lỗi chức năng — phù hợp định hướng điều tra sang **trace** thay vì log lỗi.

## Evidence

- `/metrics` trong incident: `submission/evidence/cp3_metrics_incident.txt` (P50/P95/P99 = 2653 ms).
- `/metrics` sau phục hồi: `submission/evidence/cp3_metrics_after.txt` (P95 = 600 ms).
- Dashboard lúc incident: `submission/evidence/dashboard_incident.png` (panel Latency hiển thị P95 2653 ms > 2000 ms).
- Baseline: số liệu CP1 trong `submission/REPORT.md` + `submission/evidence/dashboard_main.png`.

## Bàn giao cho E (đưa vào REPORT.md)

- Dùng bảng trên làm phần "Metrics" của chuỗi Metrics → Traces → Logs: triệu chứng = latency cao (refund), trace `d8220b44…` (retrieve-context 2506 ms) khoanh vùng RAG, log `req-cb44b739` xác nhận latency 2652 ms.
