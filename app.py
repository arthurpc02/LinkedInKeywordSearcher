from __future__ import annotations

import csv
import io
import os
import re
from collections import Counter
from typing import List, Tuple

from flask import Flask, Response, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import RequestEntityTooLarge

app = Flask(__name__)

# Security and request-hardening defaults.
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-secret-change-me")
app.config["WTF_CSRF_TIME_LIMIT"] = None
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH", 512 * 1024))
app.config["MAX_JOB_TEXT_CHARS"] = int(os.getenv("MAX_JOB_TEXT_CHARS", 50000))
app.config["FLASK_ENV"] = os.getenv("FLASK_ENV", "production")

csrf = CSRFProtect(app)
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
)

# A lightweight built-in English stopword set for this POC.
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "can", "could", "did", "do", "does", "doing",
    "down", "during", "each", "few", "for", "from", "further", "had", "has", "have",
    "having", "he", "her", "here", "hers", "herself", "him", "himself", "his", "how",
    "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me", "more", "most",
    "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", "only", "or",
    "other", "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should",
    "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves",
    "then", "there", "these", "they", "this", "those", "through", "to", "too", "under",
    "until", "up", "very", "was", "we", "were", "what", "when", "where", "which", "while",
    "who", "whom", "why", "will", "with", "you", "your", "yours", "yourself", "yourselves",
    "s", "re", "ve", "ll", "d", "m", "t", "eg", "etc",
}

TOKEN_RE = re.compile(r"[a-zA-Z]+(?:'[a-zA-Z]+)*")
MIN_TOKEN_LENGTH = 2


def normalize_token(token: str) -> str:
    """Normalize token for counting by handling casing and apostrophe artifacts."""
    normalized = token.lower().strip("'")
    if normalized.endswith("'s"):
        normalized = normalized[:-2]
    return normalized.strip("'")


def extract_top_keywords(text: str, limit: int = 200) -> List[Tuple[str, int]]:
    """Return the top keywords and counts, sorted descending by frequency."""
    words = TOKEN_RE.findall(text)
    normalized_words = (normalize_token(word) for word in words)
    filtered = [
        token
        for token in normalized_words
        if len(token) >= MIN_TOKEN_LENGTH and token not in STOPWORDS
    ]
    counts = Counter(filtered)
    return counts.most_common(limit)


def tokenizer_sanity_check() -> bool:
    """Deterministic check for apostrophe handling and abbreviation artifacts."""
    sample = "friend's you're e.g. don't"
    extracted = {keyword for keyword, _ in extract_top_keywords(sample, limit=20)}
    required = {"friend", "you're", "don't"}
    excluded = {"s", "re", "e", "g"}
    return required.issubset(extracted) and excluded.isdisjoint(extracted)


def _validate_job_text(text_input: str) -> Tuple[str, str | None]:
    max_chars = app.config["MAX_JOB_TEXT_CHARS"]
    if len(text_input) > max_chars:
        return (
            text_input[:max_chars],
            f"Input is too long. Please keep job text under {max_chars:,} characters.",
        )
    return text_input, None


@app.after_request
def add_secure_headers(response: Response) -> Response:
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.errorhandler(RequestEntityTooLarge)
def handle_large_request(_: RequestEntityTooLarge):
    return (
        render_template(
            "index.html",
            text_input="",
            keywords=[],
            error_message="Request too large. Please submit at most 512 KB of data.",
        ),
        413,
    )


@app.route("/", methods=["GET", "POST"])
@limiter.limit("30 per minute")
def index() -> str:
    text_input = ""
    keywords: List[Tuple[str, int]] = []
    error_message: str | None = None

    if request.method == "POST":
        text_input = request.form.get("job_text", "")
        text_input, error_message = _validate_job_text(text_input)
        if error_message is None:
            keywords = extract_top_keywords(text_input)

    return render_template(
        "index.html",
        text_input=text_input,
        keywords=keywords,
        error_message=error_message,
    )


@app.route("/export-csv", methods=["POST"])
@limiter.limit("15 per minute")
def export_csv() -> Response:
    text_input = request.form.get("job_text", "")
    text_input, error_message = _validate_job_text(text_input)
    if error_message:
        return Response(error_message, status=400, mimetype="text/plain")

    keywords = extract_top_keywords(text_input)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["keyword", "count"])
    writer.writerows(keywords)

    csv_content = output.getvalue()
    output.close()

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=top_keywords.csv"},
    )


if __name__ == "__main__":
    app.run(debug=False)
