#!/usr/bin/env python3
"""A JSON API over Session for the TypeScript frontend in web/: the browser counterpart of cli.py
at callback/engine/README.md's player-facing seam. Every route goes through
_session_bridge.GameRegistry, so the frontend only ever sees plain data.

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
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from callback.engine.simulation._session_bridge import GameError, GameRegistry, to_plain
from callback.engine.simulation.session import Session

REPO_ROOT = Path(__file__).resolve().parents[3]
DIST = REPO_ROOT / "web" / "dist"
MAX_BODY = 1 << 20

GAMES = GameRegistry()


def options() -> dict:
    """Every static option list a screen needs, fetched once at load."""
    return to_plain({
        "backgrounds": Session.background_options(),
        "ambitions": Session.ambition_options(),
        "prep": Session.prep_options(),
        "dials": Session.dial_options(),
        "positions": Session.position_options(),
        "scenes": Session.scene_names(),
        "release": Session.release_options(),
        "rating_cut": Session.rating_cut_options(),
        "script_notes": Session.script_note_options(),
        "orientations": Session.orientation_options(),
        "bonus_types": Session.box_office_bonus_type_options(),
        "director_genres": Session.director_genre_options(),
        "director_budget_tiers": Session.director_budget_tier_options(),
        "director_dev_actions": Session.director_dev_action_options(),
        "attach_star_types": Session.attach_star_type_options(),
    })


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

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise GameError("request body too large")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            raise GameError("body must be JSON") from None
        if not isinstance(data, dict):
            raise GameError("body must be a JSON object")
        return data

    def _route(self, method: str) -> None:
        parts = [p for p in self.path.split("?", 1)[0].split("/") if p]
        try:
            if parts[:1] != ["api"]:
                return self._static(parts) if method == "GET" else self._json(404, {"error": "not found"})
            if parts == ["api", "options"] and method == "GET":
                return self._json(200, options())
            if parts == ["api", "games"] and method == "GET":
                return self._json(200, GAMES.list_games())
            if parts == ["api", "games"] and method == "POST":
                b = self._body()
                seed = b.get("seed")
                return self._json(200, GAMES.new_game(b.get("background", ""), b.get("ambition", ""),
                                                      int(seed) if seed not in (None, "") else None))
            if len(parts) == 4 and parts[:2] == ["api", "games"]:
                game_id, action = parts[2], parts[3]
                if action == "status" and method == "GET":
                    return self._json(200, GAMES.status(game_id))
                if action == "call" and method == "POST":
                    b = self._body()
                    return self._json(200, {"result": GAMES.call(game_id, b.get("method", ""), b.get("args") or {})})
                if action == "auto_play" and method == "POST":
                    return self._json(200, GAMES.auto_play(game_id, int(self._body().get("years", 1))))
            return self._json(404, {"error": f"no route {method} {self.path}"})
        except GameError as exc:
            return self._json(400, {"error": str(exc)})
        except Exception as exc:  # noqa: BLE001 - an engine crash is reported to the UI, not fatal
            traceback.print_exc()
            return self._json(500, {"error": f"engine error: {exc!r}"})

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
