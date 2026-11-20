"""The web frontend's JSON API as a pure function, route(method, path, body) -> (status, payload).
web_server.py serves it over HTTP. The browser-only build (web/, Pyodide) calls it directly in
WebAssembly with no server at all. Like cli.py, the only engine type used is Session, through
_session_bridge.GameRegistry (callback/engine/README.md's player-facing boundary).
"""
from __future__ import annotations

import json
import traceback

from callback.engine.simulation._session_bridge import GameError, GameRegistry, to_plain
from callback.engine.simulation.session import Session

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


def route(method: str, path: str, body: dict | None = None) -> tuple[int, object]:
    """/api/... routes. Returns (http_status, json_payload); never raises."""
    parts = [p for p in path.split("?", 1)[0].split("/") if p]
    b = body or {}
    try:
        if parts == ["api", "options"] and method == "GET":
            return 200, options()
        if parts == ["api", "games"] and method == "GET":
            return 200, GAMES.list_games()
        if parts == ["api", "games"] and method == "POST":
            seed = b.get("seed")
            return 200, GAMES.new_game(b.get("background", ""), b.get("ambition", ""),
                                       int(seed) if seed not in (None, "") else None)
        if len(parts) == 4 and parts[:2] == ["api", "games"]:
            game_id, action = parts[2], parts[3]
            if action == "status" and method == "GET":
                return 200, GAMES.status(game_id)
            if action == "call" and method == "POST":
                return 200, {"result": GAMES.call(game_id, b.get("method", ""), b.get("args") or {})}
            if action == "auto_play" and method == "POST":
                return 200, GAMES.auto_play(game_id, int(b.get("years", 1)))
        return 404, {"error": f"no route {method} {path}"}
    except GameError as exc:
        return 400, {"error": str(exc)}
    except Exception as exc:  # noqa: BLE001 - an engine crash is reported to the UI, not fatal
        traceback.print_exc()
        return 500, {"error": f"engine error: {exc!r}"}


def route_json(method: str, path: str, body_json: str) -> str:
    """JSON-string in/out wrapper, the easy call shape for Pyodide's JS bridge."""
    status, payload = route(method, path, json.loads(body_json) if body_json else None)
    return json.dumps({"status": status, "payload": payload}, ensure_ascii=False)
