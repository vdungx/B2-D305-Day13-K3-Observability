from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio

PROMPT_NAME = "day13-chat"

PROMPT_V1 = "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}"
PROMPT_V2 = (
    "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}\n"
    "Answer in at most 3 sentences."
)


def main() -> int:
    configure_utf8_stdio()
    load_dotenv(REPO_ROOT / ".env")

    from app.tracing import get_langfuse_client, tracing_enabled

    if not tracing_enabled():
        print("KHÔNG HỢP LỆ: Langfuse credentials chưa được cấu hình (kiểm tra .env).")
        return 1

    client = get_langfuse_client()

    v1 = client.create_prompt(
        name=PROMPT_NAME,
        prompt=PROMPT_V1,
        labels=["baseline", "production"],
        type="text",
        commit_message="v1: baseline template",
    )
    print(f"Created {PROMPT_NAME} version={v1.version} labels={v1.labels}")

    v2 = client.create_prompt(
        name=PROMPT_NAME,
        prompt=PROMPT_V2,
        labels=["candidate"],
        type="text",
        commit_message="v2: cap answer length to 3 sentences",
    )
    print(f"Created {PROMPT_NAME} version={v2.version} labels={v2.labels}")

    print("\nTiếp theo:")
    print("1. Chạy app, gửi request với LANGFUSE_PROMPT_LABEL=baseline, rồi candidate.")
    print("2. Mở 2 trace trên Langfuse, kiểm tra prompt_name/prompt_label/prompt_version.")
    print(f"3. Chuyển label production sang version={v2.version} trên Langfuse UI, chạy lại 1 request.")
    print(f"4. Rollback production về version={v1.version}, lưu ảnh evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
