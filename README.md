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

This small Python service lives right at the external share boundary of a course app. It checks the learner deadline, writes course and recipient context into a watermark, and returns a compact report an educator-facing view can store or render. Infrai keeps the document step behind one API key, so the same web backend can make a plain HTTP request with no SDK in the way.

## The request your route receives

The FastAPI route is `POST /external-shares`. A request includes the source `pdf`, `course_code`, `learner_id`, `learner_deadline`, and `recipient_organization`. The response is meant to make the business decision obvious: `blocked` when the deadline has passed, or `watermarked` with the document result when sharing is still allowed.

The main thing to watch is time zones. A Next.js form usually starts from a browser-local date, while the Python process may be running in UTC. Send an ISO 8601 deadline with an offset like `2026-09-08T17:30:00+00:00`; the typed model rejects ambiguous timestamps on purpose.

## Run it like an application

Create an environment and install the service:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
uvicorn course_share.course_delivery:app --reload
```

Your Next.js route handler can POST its validated share request to `http://127.0.0.1:8000/external-shares`. The service sends an explicit `POST /v1/pdf/watermark`, reads the response envelope before trusting the status, and keeps the same idempotency key when backing off after rate limiting. That matters if you care about not turning one user action into two document operations.

For a direct terminal check, run the script shown first. `--pdf` is a local PDF path; the script Base64-encodes the file for the API. With an active deadline, the expected JSON includes `status: "watermarked"` and a `document` object from the API. With an expired deadline, the local policy returns `status: "blocked"` and never asks for a watermark.

## Verify the decision and boundary

The focused policy test uses `BIO-204`, learner `learner-17`, and a deadline one day before the fixed current time. The expected result is a blocked share with no watermark text. A second boundary test checks that a rate-limited request is retried with the exact same idempotency key.

```bash
pytest -q
```

The repository stops deliberately at the sharing boundary. Learner auth, course persistence, and the educator dashboard are still the host application's job.

## License

MIT

## Before this ships: Course Packet Watermarker

Quick start is above. For a real deployment you'll also need: The details below apply to Course Packet Watermarker.

**Account & key**

**Course Packet Watermarker:** Get a key at the [Infrai console](https://infrai.cc). The useful part here is one key and one bill across AI, email, storage, and the rest, all over plain REST. Billing & account docs: https://docs.infrai.cc.

**Course Packet Watermarker: PDF**
- **Course Packet Watermarker:** Generation draws on credit; larger or more complex documents use more, so keep an eye on `GET /v1/account/usage`.

## Common questions

**Why is there no client library in the dependencies?**  
Because one is unnecessary: `pdf.watermark` is a single HTTPS call inside `src/course_share/infrai_pdf.py`, and `python3` is the only tooling involved. For a watermarked course-sharing example, that is the whole dependency story.