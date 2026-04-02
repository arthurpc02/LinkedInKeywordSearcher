# LinkedInKeywordSearcher

Simple Flask web app to analyze job description text and return the top 200 most used keywords.

## Features
- Paste one or multiple job descriptions.
- Extracts keywords case-insensitively (`Python` == `python`).
- Ignores numbers and symbols.
- Excludes common English stopwords (`the`, `and`, `to`, etc.).
- Handles contractions (e.g., `friend's`, `you're`, `don't`) without splitting on apostrophes.
- Removes contraction/abbreviation artifacts (like `s`, `re`, `e`, `g`, `eg`, `etc`) via normalization and stopword filtering.
- Shows up to 200 keywords sorted by highest frequency.
- CSV export of resulting keywords and counts.
- Request hardening: input-size validation, per-IP rate limiting, CSRF protection, and secure response headers.

## Run locally
1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
python app.py
```

4. Open `http://127.0.0.1:5000`.

## Environment variables
Use these variables to make deployment behavior reproducible:

- `SECRET_KEY`: Flask secret key used by CSRF/session signing. **Set this in production.**
- `MAX_CONTENT_LENGTH`: Maximum HTTP request size in bytes. Default: `524288` (512 KB).
- `MAX_JOB_TEXT_CHARS`: Maximum characters accepted in `job_text`. Default: `50000`.
- `RATELIMIT_STORAGE_URI`: Backend for rate-limit counters. Default: `memory://`.
  - For multi-instance production deployments, use shared storage such as Redis (for example, `redis://...`).
- `FLASK_ENV`: Defaults to `production`.

## Production hardening notes
- `debug` is disabled in `app.run(...)` and should remain disabled in production.
- Large payloads are rejected with HTTP `413` before keyword extraction.
- Oversized `job_text` values are not processed and return a user-friendly message.
- Per-IP rate limits are applied:
  - `30/minute` on `/` (analyze)
  - `15/minute` on `/export-csv`
- CSRF tokens are required on form POST endpoints.
- Security headers are added on every response:
  - `Content-Security-Policy`
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `X-Frame-Options: DENY`
- The app does not intentionally log raw submitted job text; keep upstream reverse-proxy/app-server logs configured to avoid request-body logging.

## Notes
- Tokenization lowercases text, strips possessive endings (`'s`), trims leading/trailing apostrophes, and ignores tokens shorter than 2 characters.
- This is a lightweight POC and intentionally simple.
