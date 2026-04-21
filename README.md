# xlsx-image-embedder

Download image URLs from an Excel spreadsheet, embed thumbnails back into the sheet, and get the raw files in a ZIP — all through your browser, with a local helper that handles authenticated sites.

Works with any site you can log into. Auth is handled by a one-time browser login; after that the helper reuses your session so you can batch-download images that require a logged-in session, cookies, or that block direct hotlinking.

![mode note shows green when proxy is connected](docs/screenshot.png)

---

## Features

- **Drop-in HTML UI** — upload an `.xlsx`, pick which columns contain URLs, watch progress.
- **Column picker** — the app scans every column, counts URLs, and lets you select which to process.
- **Parallel downloads** — configurable concurrency with live progress, error log, and thumbnail gallery.
- **Two outputs** — original workbook with images embedded next to each URL, plus a ZIP of the full-resolution files.
- **Handles authenticated sites** — a tiny local helper logs into the target site once and reuses that session for all downloads.
- **No server, no account, no data leaves your machine.** Everything runs locally.

## Requirements

- Python 3.9+
- A modern browser (Chrome, Firefox, Edge, Safari)

## Installation

```bash
git clone https://github.com/YOUR-USERNAME/xlsx-image-embedder.git
cd xlsx-image-embedder
pip install -r requirements.txt
playwright install chromium
```

## Usage

### 1. Log in to the target site (one time)

```bash
python proxy.py --login --site https://example.com/login
```

A Chromium window opens at the URL you pass. Log in normally, then press Enter in the terminal. Your session is saved to `./session/` for future runs.

> Tip: if the site doesn't need auth, you can skip this step — direct URLs will still work through the proxy, which sidesteps CORS.

### 2. Start the app

```bash
python proxy.py
```

Open **http://localhost:8765/** in any browser.

### 3. Process a file

1. Drop your `.xlsx` onto the drop zone.
2. Click the column chips to toggle which ones contain image URLs. Counts show how many rows have URLs in each column; top candidates are auto-selected.
3. Adjust thumbnail size, concurrency, or row limit if needed.
4. Click **Process all rows**.
5. When done, download:
   - **Excel** — original workbook with one new `{column}_img` column per selected column, thumbnails embedded.
   - **ZIP** — raw full-resolution images named `row0042_column.ext`.
   - **Delete all & reset** — clears browser memory.

## Command-line options

### `proxy.py`

```
python proxy.py [--port 8765] [--login] [--site URL] [--headless]
```

| Flag | Default | What it does |
|---|---|---|
| `--port` | `8765` | Port to serve the app on. |
| `--login` | | Open a browser for interactive login, save session, exit. |
| `--site` | `https://example.com/` | URL to navigate to during `--login`. |
| `--headless` | | Run the background browser headless while serving. |

## How it works

```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐
│  Browser    │◀────▶│  proxy.py    │◀────▶│  Target site │
│  (HTML UI)  │ /fetch│  (localhost) │ HTTPS│              │
└─────────────┘      └──────────────┘      └──────────────┘
                       Playwright
                       session (cookies)
```

The HTML UI does all the work — reading the spreadsheet, building the Excel output, zipping files, showing progress. It only calls the proxy for one thing: fetching image bytes. The proxy forwards each request through a persistent Playwright browser context, which carries your logged-in cookies, then streams the response back with permissive CORS headers so the HTML can read it.

## Standalone (no proxy)

If your URLs are publicly accessible and the site sends permissive CORS headers, you can open `image_embedder.html` directly in a browser — it auto-detects the absence of the proxy and falls back to direct `fetch()` calls. Most real-world sites block this, which is why the proxy exists.

## Troubleshooting

**"No session. Run `python proxy.py --login` first."**
The session directory doesn't exist yet. Run the login step.

**"No proxy detected" / all downloads fail with CORS errors**
You opened the HTML file directly instead of going through `http://localhost:8765/`. Start the proxy and use the localhost URL.

**Every image returns 403**
Your session expired. Re-run `python proxy.py --login`.

**Downloads are slow**
Bump `Concurrency` in the UI. Watch out for rate-limiting from the target site — if errors start climbing, turn it back down.

**Output Excel is huge**
Thumbnails are compressed, but 1,000+ embedded images add up. Lower `Thumb px` to 60 or skip the embed step and just use the ZIP.

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Issues and PRs welcome. The codebase is deliberately small: one HTML file for the UI, one Python file for the proxy. Keep it that way.
