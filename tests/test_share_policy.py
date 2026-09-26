from datetime import datetime, timezone

from course_share.share_policy import decide_external_share


def test_expired_deadline_blocks_external_share() -> None:
    decision = decide_external_share(
        course_code="BIO-204",
        learner_id="learner-17",
        deadline=datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc),
        recipient_organization="North Campus Lab",
        now=datetime(2026, 9, 2, 9, 0, tzinfo=timezone.utc),
    )

    assert decision.allowed is False
    assert decision.reason == "learner deadline has passed"
    assert decision.watermark_text is None


def test_active_deadline_builds_auditable_watermark() -> None:
    decision = decide_external_share(
        course_code="BIO-204",
        learner_id="learner-17",
        deadline=datetime(2026, 9, 8, 17, 30, tzinfo=timezone.utc),
        recipient_organization="North Campus Lab",
        now=datetime(2026, 9, 2, 9, 0, tzinfo=timezone.utc),
    )

    assert decision.allowed is True
    assert decision.watermark_text == (
        "BIO-204 | learner learner-17 | external copy for North Campus Lab | "
        "deadline 2026-09-08T17:30+00:00"
    )

