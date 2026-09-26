from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ShareDecision:
    allowed: bool
    reason: str
    watermark_text: str | None


def decide_external_share(
    *,
    course_code: str,
    learner_id: str,
    deadline: datetime,
    recipient_organization: str,
    now: datetime,
) -> ShareDecision:
    if deadline.tzinfo is None or now.tzinfo is None:
        raise ValueError("deadline and now must include a timezone offset")

    if deadline <= now:
        return ShareDecision(
            allowed=False,
            reason="learner deadline has passed",
            watermark_text=None,
        )

    stamp = deadline.isoformat(timespec="minutes")
    return ShareDecision(
        allowed=True,
        reason="active learner deadline",
        watermark_text=(
            f"{course_code} | learner {learner_id} | external copy for "
            f"{recipient_organization} | deadline {stamp}"
        ),
    )

