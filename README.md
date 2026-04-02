# LinkedInKeywordSearcher

Simple Flask web app to analyze job description text and return the top 200 most used keywords.

## Features
- Paste one or multiple job descriptions.
- Extracts keywords case-insensitively (`Python` == `python`).
- Ignores numbers and symbols.
- Excludes common English stopwords (`the`, `and`, `to`, etc.).
- Shows up to 200 keywords sorted by highest frequency.
- CSV export of resulting keywords and counts.

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

## Notes
- This is a lightweight POC and intentionally simple.
