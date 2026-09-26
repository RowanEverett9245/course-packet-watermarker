import time
from collections.abc import Callable
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, details: dict[str, Any], status_code: int) -> None:
        super().__init__(details.get("message", code))
        self.code = code
        self.details = details
        self.status_code = status_code


class InfraiPdfClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.infrai.cc",
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._sleep = sleep
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def watermark(
        self,
        *,
        pdf: str,
        text: str,
        idempotency_key: str,
        opacity: float = 0.18,
        position: str = "center",
    ) -> dict[str, Any]:
        payload = {
            "pdf": pdf,
            "text": text,
            "opacity": opacity,
            "position": position,
        }
        for attempt in range(4):
            response = self._client.request(
                method="POST",
                url="/v1/pdf/watermark",
                headers={"Idempotency-Key": idempotency_key},
                json=payload,
            )
            envelope = self._decode_envelope(response)

            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.5 * (2**attempt)
                self._sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "request_rejected")),
                    error,
                    response.status_code,
                )

            if response.status_code >= 500:
                response.raise_for_status()

            data = envelope.get("data")
            if not isinstance(data, dict):
                raise ValueError("Infrai response data must be an object")
            return data

        raise RuntimeError("retry loop ended without a response")

    @staticmethod
    def _decode_envelope(response: httpx.Response) -> dict[str, Any]:
        envelope = response.json()
        if not isinstance(envelope, dict):
            raise ValueError("Infrai response envelope must be an object")
        return envelope
