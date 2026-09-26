import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .infrai_pdf import InfraiError, InfraiPdfClient
from .share_policy import decide_external_share


class ExternalShareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    course_code: str = Field(min_length=1, max_length=40)
    learner_id: str = Field(min_length=1, max_length=80)
    learner_deadline: datetime
    recipient_organization: str = Field(min_length=1, max_length=120)
    pdf: str = Field(min_length=1)

    @field_validator("learner_deadline")
    @classmethod
    def deadline_has_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("learner_deadline must include a timezone offset")
        return value


class ExternalShareReport(BaseModel):
    status: str
    course_code: str
    learner_id: str
    recipient_organization: str
    reason: str
    document: dict[str, Any] | None = None


def create_app(client: InfraiPdfClient | None = None) -> FastAPI:
    app = FastAPI(title="Course packet sharing")

    @app.post("/external-shares", response_model=ExternalShareReport)
    def create_external_share(request: ExternalShareRequest) -> ExternalShareReport:
        decision = decide_external_share(
            course_code=request.course_code,
            learner_id=request.learner_id,
            deadline=request.learner_deadline,
            recipient_organization=request.recipient_organization,
            now=datetime.now(timezone.utc),
        )
        report = {
            "course_code": request.course_code,
            "learner_id": request.learner_id,
            "recipient_organization": request.recipient_organization,
            "reason": decision.reason,
        }
        if not decision.allowed:
            return ExternalShareReport(status="blocked", **report)

        pdf_client = client or InfraiPdfClient(api_key=_api_key())
        try:
            document = pdf_client.watermark(
                pdf=request.pdf,
                text=decision.watermark_text or "",
                idempotency_key=f"course-share-{uuid4()}",
            )
        except InfraiError as exc:
            caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
            raise HTTPException(
                status_code=caller_status,
                detail={"code": exc.code, "message": str(exc)},
            ) from exc
        finally:
            if client is None:
                pdf_client.close()

        return ExternalShareReport(status="watermarked", document=document, **report)

    return app


def _api_key() -> str:
    value = os.environ.get("INFRAI_API_KEY")
    if not value:
        raise RuntimeError("Set INFRAI_API_KEY before sharing a course packet")
    return value


app = create_app()

