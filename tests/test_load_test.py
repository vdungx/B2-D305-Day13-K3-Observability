from __future__ import annotations

from scripts.load_test import send_request


class _ErrorResponse:
    status_code = 500
    headers = {"x-request-id": "req-error01"}

    @staticmethod
    def json() -> dict[str, str]:
        return {"detail": "RuntimeError"}


class _ErrorClient:
    @staticmethod
    def post(*args, **kwargs) -> _ErrorResponse:
        return _ErrorResponse()


def test_load_test_prefers_request_id_header_for_error_response(capsys) -> None:
    send_request(_ErrorClient(), {"feature": "refund"})

    assert "[500] req-error01 | refund |" in capsys.readouterr().out
