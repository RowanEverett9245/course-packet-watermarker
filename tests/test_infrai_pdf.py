import httpx

from course_share.infrai_pdf import InfraiPdfClient


def test_watermark_retries_429_with_the_same_idempotency_key() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "0"},
                json={
                    "ok": False,
                    "data": None,
                    "error": {"message": "Retry the request shortly"},
                    "metadata": {},
                },
            )
        return httpx.Response(
            200,
            json={"ok": True, "data": {"url": "https://documents.example/watermarked.pdf"}, "error": None, "metadata": {}},
        )

    client = InfraiPdfClient(
        api_key="test-key",
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
    )
    try:
        result = client.watermark(
            pdf="https://documents.example/course.pdf",
            text="BIO-204 external copy",
            idempotency_key="share-17",
        )
    finally:
        client.close()

    assert result["url"].endswith("watermarked.pdf")
    assert len(requests) == 2
    assert {request.headers["Idempotency-Key"] for request in requests} == {"share-17"}
