# Contributing

Thanks for your interest! The codebase is deliberately tiny:

- `image_embedder.html` — the entire UI (HTML + CSS + vanilla JS, no build step)
- `proxy.py` — local HTTP server + Playwright-backed fetch endpoint

Please keep it that way. No bundlers, no frameworks, no ORMs.

## Dev setup

```bash
git clone https://github.com/YOUR-USERNAME/xlsx-image-embedder.git
cd xlsx-image-embedder
pip install -r requirements.txt
playwright install chromium
python proxy.py
# open http://localhost:8765/
```

## Before submitting a PR

1. Run the checks locally:
   ```bash
   python -m py_compile proxy.py
   # extract <script> and run: node --check _check.js
   ```
   Or just let the GitHub Actions workflow run on your PR.

2. Test with a real spreadsheet that has image URLs. Include a screenshot if you're changing UI.

3. Keep changes focused — one feature or fix per PR.

## Issue reports

Please include:
- What site / URLs you were trying to download
- What you expected vs. what happened
- The error log from the UI (the dark box in step 02)
- Your Python version and OS

## Scope

Things we'd accept:
- Bug fixes, performance improvements, better error messages
- Additional output formats (e.g., CSV sidecar with status per row)
- Headless batch mode (CLI equivalent of the UI)
- Accessibility improvements

Things out of scope:
- Bypassing site anti-scraping measures beyond standard session reuse
- Site-specific integrations (keep it generic)
- Heavy frontend frameworks
