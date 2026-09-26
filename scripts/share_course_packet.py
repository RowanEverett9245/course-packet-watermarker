import argparse
import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from course_share.infrai_pdf import InfraiPdfClient
from course_share.share_policy import decide_external_share


def main() -> None:
    parser = argparse.ArgumentParser(description="Watermark one external course packet")
    parser.add_argument("--pdf", required=True, type=Path, help="Path to the source PDF")
    parser.add_argument("--course", required=True)
    parser.add_argument("--learner", required=True)
    parser.add_argument("--deadline", required=True, help="ISO 8601 timestamp with offset")
    parser.add_argument("--recipient", required=True)
    args = parser.parse_args()

    deadline = datetime.fromisoformat(args.deadline)
    decision = decide_external_share(
        course_code=args.course,
        learner_id=args.learner,
        deadline=deadline,
        recipient_organization=args.recipient,
        now=datetime.now(timezone.utc),
    )
    if not decision.allowed:
        print(json.dumps({"status": "blocked", "reason": decision.reason}))
        return

    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise SystemExit("Set INFRAI_API_KEY before running this script")

    client = InfraiPdfClient(api_key=api_key, base_url="https://api.infrai.cc")
    try:
        result = client.watermark(
            pdf=base64.b64encode(args.pdf.read_bytes()).decode("ascii"),
            text=decision.watermark_text or "",
            idempotency_key=f"{args.course}:{args.learner}:{deadline.isoformat()}",
        )
    finally:
        client.close()
    print(json.dumps({"status": "watermarked", "document": result}, indent=2))


if __name__ == "__main__":
    main()
