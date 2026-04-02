from __future__ import annotations

import csv
import io
import re
from collections import Counter
from typing import List, Tuple

from flask import Flask, Response, render_template, request

app = Flask(__name__)

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
}


def extract_top_keywords(text: str, limit: int = 200) -> List[Tuple[str, int]]:
    """Return the top keywords and counts, sorted descending by frequency."""
    words = re.findall(r"[a-zA-Z]+", text.lower())
    filtered = [w for w in words if w not in STOPWORDS]
    counts = Counter(filtered)
    return counts.most_common(limit)


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    text_input = ""
    keywords: List[Tuple[str, int]] = []

    if request.method == "POST":
        text_input = request.form.get("job_text", "")
        keywords = extract_top_keywords(text_input)

    return render_template("index.html", text_input=text_input, keywords=keywords)


@app.route("/export-csv", methods=["POST"])
def export_csv() -> Response:
    text_input = request.form.get("job_text", "")
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
    app.run(debug=True)
