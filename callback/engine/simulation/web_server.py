#!/usr/bin/env python3
"""A JSON API over Session for the TypeScript frontend in web/: the browser counterpart of cli.py
at callback/engine/README.md's player-facing seam. The routes themselves live in _web_routes.py
(shared with the browser-only Pyodide build); this file is only the HTTP transport.

Standard library only. A single-threaded server is deliberate: Session isn't thread-safe, and one
local player doesn't need concurrency. From the repository root:

    python3 -m callback.engine.simulation.web_server            # API + built frontend on :8765
    python3 -m callback.engine.simulation.web_server --port=9000

    POST /api/games                   {background, ambition, seed?}  -> new game
    GET  /api/options                 static option lists (backgrounds, prep, dials, ...)
    GET  /api/games/<id>/status       dashboard
    POST /api/games/<id>/call         {method, args}  -> any public Session method
    POST /api/games/<id>/auto_play    {years}
"""
from __future__ import annotations

import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from callback.engine.simulation._web_routes import route

REPO_ROOT = Path(__file__).resolve().parents[3]
DIST = REPO_ROOT / "web" / "dist"
MAX_BODY = 1 << 20


class Handler(BaseHTTPRequestHandler):
    server_version = "CallbackWeb/0.1"

    def log_message(self, fmt, *args):  # keep the console quiet apart from errors
        pass

    def _json(self, status: int, payload) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _route(self, method: str) -> None:
        path = self.path.split("?", 1)[0]
        if not path.startswith("/api/"):
            return self._static([p for p in path.split("/") if p]) if method == "GET" else self._json(404, {"error": "not found"})
        body = None
        if method == "POST":
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                return self._json(413, {"error": "request body too large"})
            try:
                body = json.loads(self.rfile.read(length) or b"{}") if length else {}
            except json.JSONDecodeError:
                return self._json(400, {"error": "body must be JSON"})
            if not isinstance(body, dict):
                return self._json(400, {"error": "body must be a JSON object"})
        status, payload = route(method, path, body)
        return self._json(status, payload)

    def _static(self, parts: list[str]) -> None:
        if not DIST.is_dir():
            return self._json(404, {"error": "frontend not built: run `npm run build` in web/, or use `npm run dev`"})
        target = (DIST / "/".join(parts)).resolve() if parts else DIST / "index.html"
        if not str(target).startswith(str(DIST.resolve())) or not target.is_file():
            target = DIST / "index.html"  # single-page app fallback
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802 - http.server's naming
        self._route("GET")

    def do_POST(self):  # noqa: N802
        self._route("POST")


def main(argv: list[str]) -> int:
    port = 8765
    for arg in argv[1:]:
        if arg.startswith("--port="):
            port = int(arg.split("=", 1)[1])
    httpd = HTTPServer(("127.0.0.1", port), Handler)
    print(f"Callback web API on http://127.0.0.1:{port}/  (frontend: {'built' if DIST.is_dir() else 'run npm run dev in web/'})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
