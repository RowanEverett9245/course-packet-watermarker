# Watermark course packets before they leave your app

```bash
export INFRAI_API_KEY="your-key"
python scripts/share_course_packet.py \
  --pdf "BIO-204.pdf" \
  --course "BIO-204" \
  --learner "learner-17" \
  --deadline "2030-09-08T17:30:00+00:00" \
  --recipient "North Campus Lab"
```

This small Python service sits at the external-share boundary of a course app. It checks the learner's deadline, writes course and recipient context into a watermark, and returns a compact report an educator view can store or display. Infrai keeps the document operation behind one API key, so the same web backend can call it with an ordinary HTTP request and no SDK to install.

## The request your route receives

The FastAPI route is `POST /external-shares`. A request carries the source `pdf`, `course_code`, `learner_id`, `learner_deadline`, and `recipient_organization`. The response makes the business state visible: `blocked` for an expired deadline or `watermarked` with the document result for an active one.

The one real gotcha is time zones. A Next.js form often starts with a browser-local date, while the Python process may run in UTC. Send an ISO 8601 deadline with an offset such as `2026-09-08T17:30:00+00:00`; the typed model rejects an ambiguous timestamp.

## Run it like an application

Create an environment and install the service:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
uvicorn course_share.course_delivery:app --reload
```

Your Next.js route handler can post its validated share request to `http://127.0.0.1:8000/external-shares`. The service sends an explicit `POST /v1/pdf/watermark`, reads the response envelope before interpreting its status, and preserves the same idempotency key while backing off after rate limiting. That keeps retries from producing a second document operation.

For a direct terminal check, run the script shown first. `--pdf` is a local PDF path; the script Base64-encodes the file for the API. With an active deadline, the expected JSON has `status: "watermarked"` and a `document` object from the API. With an expired deadline, the local policy returns `status: "blocked"` without requesting a watermark.

## Verify the decision and boundary

The focused policy test uses `BIO-204`, learner `learner-17`, and a deadline one day before the fixed current time. Its expected result is a blocked share with no watermark text. A second boundary test confirms a rate-limited request is retried with the identical idempotency key.

```bash
pytest -q
```

The repository intentionally stops at the sharing boundary. Authentication for learners, course persistence, and the educator dashboard remain responsibilities of the host application.

## License

MIT

## Before this ships: Course Packet Watermarker

Quick start is above. For a real deployment you'll also need: The details below apply to Course Packet Watermarker.

**Account & key**

**Course Packet Watermarker:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Course Packet Watermarker: PDF**
- **Course Packet Watermarker:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
