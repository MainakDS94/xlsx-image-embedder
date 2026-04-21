"""
Local proxy + static server for the xlsx-image-embedder HTML app.

Why this exists:
  Browsers block cross-origin image requests from a local HTML file to most
  sites, even when you're already logged in there. This tiny server:
    1. Logs you into the target site once via Playwright (persistent session).
    2. Serves the HTML app at http://localhost:8765/
    3. Exposes /fetch?url=... which downloads any URL using your logged-in
       session and streams the bytes back to the browser, with CORS headers
       set so the HTML can read the response.

Setup (one time):
    pip install -r requirements.txt
    playwright install chromium
    python proxy.py --login --site https://example.com/login

Run:
    python proxy.py
    # then open http://localhost:8765/ in any browser

See README.md for full docs.
"""
import argparse
import asyncio
import sys
from pathlib import Path

from aiohttp import web
from playwright.async_api import async_playwright

SESSION_DIR = Path("./session").resolve()
DEFAULT_SITE = "https://example.com/"
HTML_FILE = Path(__file__).parent / "image_embedder.html"


async def do_login(site: str):
    SESSION_DIR.mkdir(exist_ok=True)
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            str(SESSION_DIR), headless=False
        )
        page = await ctx.new_page()
        await page.goto(site)
        print(f"\nBrowser opened at {site}")
        print("Log in, then come back to this terminal.")
        await asyncio.get_event_loop().run_in_executor(
            None, input, "Press Enter once you're logged in to save the session..."
        )
        await ctx.close()
    print(f"Session saved to {SESSION_DIR}")


async def serve(args):
    if not SESSION_DIR.exists():
        print("No session directory found — starting without a logged-in session.")
        print("If downloads fail with 401/403, run: python proxy.py --login --site <URL>")
        SESSION_DIR.mkdir(exist_ok=True)
    if not HTML_FILE.exists():
        sys.exit(f"Cannot find {HTML_FILE}. "
                 f"Keep proxy.py and image_embedder.html in the same folder.")

    pw = await async_playwright().start()
    ctx = await pw.chromium.launch_persistent_context(
        str(SESSION_DIR), headless=args.headless
    )
    print(f"Playwright context ready (headless={args.headless}).")

    async def index(request):
        return web.FileResponse(HTML_FILE)

    async def fetch(request):
        url = request.query.get("url")
        if not url:
            return web.Response(status=400, text="Missing ?url=")
        if not url.startswith(("http://", "https://")):
            return web.Response(status=400, text="Bad URL")
        try:
            resp = await ctx.request.get(url, timeout=20000)
            body = await resp.body()
            headers = {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": resp.headers.get(
                    "content-type", "application/octet-stream"
                ),
                "X-Upstream-Status": str(resp.status),
            }
            return web.Response(
                status=resp.status, body=body, headers=headers
            )
        except Exception as e:
            return web.Response(
                status=502,
                text=f"{type(e).__name__}: {e}",
                headers={"Access-Control-Allow-Origin": "*"},
            )

    async def health(request):
        return web.json_response({"ok": True, "session": SESSION_DIR.exists()})

    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/fetch", fetch)
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", args.port)
    await site.start()

    print(f"\n  \u2794  Open  http://localhost:{args.port}/\n")
    print("Ctrl+C to stop.")
    try:
        await asyncio.Event().wait()
    finally:
        await ctx.close()
        await pw.stop()
        await runner.cleanup()


def main():
    ap = argparse.ArgumentParser(
        description="Local proxy + UI for downloading image URLs from an "
                    "Excel sheet using a logged-in browser session."
    )
    ap.add_argument("--port", type=int, default=8765,
                    help="Port to serve on (default: 8765)")
    ap.add_argument("--login", action="store_true",
                    help="Open a browser for interactive login, then exit")
    ap.add_argument("--site", default=DEFAULT_SITE,
                    help="URL to open during --login (default: example.com)")
    ap.add_argument("--headless", action="store_true",
                    help="Run the background browser headless while serving")
    args = ap.parse_args()

    if args.login:
        asyncio.run(do_login(args.site))
        return
    asyncio.run(serve(args))


if __name__ == "__main__":
    main()
