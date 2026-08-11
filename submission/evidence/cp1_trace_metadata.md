# CP1 Trace Metadata Evidence

Dưới đây là minh chứng cho việc `correlation_id` được truyền xuống hệ thống tracing (như Langfuse) dưới dạng metadata.
Mỗi request nhận được ID (VD: `req-a210b74f`), ID này sẽ được gắn vào Log và Trace.

```python
# Trace in application logic:
trace = langfuse.trace(
    id=session_id,
    name=feature,
    user_id=user_id,
    tags=[env],
    metadata={"correlation_id": correlation_id} # <--- Correlation ID is attached to the trace
)
```

Kết quả: Bất kỳ log hay span nào trên hệ thống monitoring đều có thể filter và nối lại với nhau bằng khóa `correlation_id`.
