#!/usr/bin/env python3
"""An MCP (Model Context Protocol) server for Callback, so an AI agent can play, playtest and
balance-check the game. It is a third UI at callback/engine/README.md's Session seam, alongside
cli.py and web_server.py. All game access goes through _session_bridge.GameRegistry.

Zero dependencies, like the rest of the engine: JSON-RPC 2.0 over stdio, one message per line
(the MCP stdio transport). Run from the repository root:

    python3 -m callback.engine.simulation.mcp_server

stdout is the protocol channel, so everything else that prints (the CLI's auto-play transcript,
stray engine output) is redirected to stderr or captured.
"""
from __future__ import annotations

import json
import subprocess
import sys
import traceback
from pathlib import Path

from callback.engine.simulation import _archetype_policies
from callback.engine.simulation._session_bridge import (
    MAX_AUTO_YEARS, GameError, GameRegistry, describe_methods, to_plain,
)
from callback.engine.simulation.session import Session

SERVER_INFO = {"name": "callback", "version": "0.1.0"}
SUPPORTED_PROTOCOLS = ("2025-06-18", "2025-03-26", "2024-11-05")
REPO_ROOT = Path(__file__).resolve().parents[3]
ARCHETYPES = ("prestige_chaser", "franchise_maximizer", "indie_purist", "risk_averse", "gambler",
              "director_track", "family_first", "burnout_avoider")
TRANSCRIPT_LIMIT = 40_000

INSTRUCTIONS = """Callback is a Hollywood career sim: you play an actor (and later a director) from
about 22 to 82. One game year, in order (this mirrors cli.acting_block):
  1. Optional pull menu: trades, rolodex_summary, interact(npc_id, action), leverage_status.
  2. offer_board(), then accept(index) on a listing with available=true. If none are available,
     try generate_more_listings() or decline_board().
  3. If holdout_available(): request_holdout() is optional.
  4. choose_deal(want_approvals, want_box_office_bonus, bonus_type, want_merchandising).
  5. Optional: sign_multi_picture_deal, request_marketing_push, choose_script_note,
     request_director, choose_orientation.
  6. choose_prep(key), then for each episode, for each of scene_names(): play_scene({dial: position}).
  7. If rating_preview()['cut_available']: choose_rating_stance(key).
  8. choose_release(strategy, bid_policy='best'|'self'), then optionally run_awards_campaign(...).
  9. Directing, once directing_unlocked(): become_director(), start_directing_project(...),
     advance_directing(project_index, action) once per quarter.
 10. end_year(). Repeat until is_over(), then read obituary_summary().
Use call_session for every step, list_methods to look up signatures, and auto_play to fast-forward
whole years with the CLI's default choices. run_archetype and run_verify are for balance work."""


def _tool(name: str, description: str, properties: dict, required: tuple = ()) -> dict:
    return {
        "name": name,
        "description": description,
        "inputSchema": {"type": "object", "properties": properties, "required": list(required),
                        "additionalProperties": False},
    }


GAME_ID = {"type": "string", "description": "Id returned by new_game, e.g. 'g1'"}

TOOLS = [
    _tool("new_game", "Start a new career. Returns game_id, the intro line and the starting status.", {
        "background": {"type": "string", "enum": [k for k, _, _ in Session.background_options()],
                       "description": "; ".join(f"{k}: {name} ({tag})" for k, name, tag in Session.background_options())},
        "ambition": {"type": "string", "enum": [k for k, _ in Session.ambition_options()],
                     "description": "What the obituary measures you against: "
                                    + ", ".join(f"{k} = {label}" for k, label in Session.ambition_options())},
        "seed": {"type": "integer", "description": "RNG seed for a reproducible run (random if omitted)"},
    }, ("background", "ambition")),
    _tool("game_status", "Dashboard for one game: age, standing band, persona, leverage, franchises, directing state.",
          {"game_id": GAME_ID}, ("game_id",)),
    _tool("call_session",
          "Call any public Session method on a game and return its plain-data result. This is how you play: "
          "offer_board, accept, choose_deal, choose_prep, play_scene, choose_release, end_year and so on. "
          "For choose_release, pass bid_policy 'best' (default, top payout) or 'self' (keep or self-distribute) "
          "in place of the CLI's bid-selector callbacks.", {
              "game_id": GAME_ID,
              "method": {"type": "string", "description": "Session method name, e.g. 'offer_board'"},
              "args": {"type": "object", "description": "Keyword arguments, e.g. {\"index\": 3}", "additionalProperties": True},
          }, ("game_id", "method")),
    _tool("list_methods", "Catalogue of Session methods (signature, group and docstring summary), filterable by substring.",
          {"query": {"type": "string", "description": "Filter on name, group or doc, e.g. 'release' or 'directing'"}}),
    _tool("auto_play", "Fast-forward whole years using the CLI's own auto-play defaults. Call at a year boundary. "
          "Returns the transcript (truncated from the front if long) and the new status.", {
              "game_id": GAME_ID,
              "years": {"type": "integer", "minimum": 1, "maximum": MAX_AUTO_YEARS, "default": 1},
          }, ("game_id",)),
    _tool("list_games", "Games currently in memory.", {}),
    _tool("close_game", "Forget a game.", {"game_id": GAME_ID}, ("game_id",)),
    _tool("run_archetype", "Run one scripted playtest policy (from the balance pass) for a full career and return its outcome.", {
        "archetype": {"type": "string", "enum": list(ARCHETYPES)},
        "seed": {"type": "integer", "default": 1},
        "years": {"type": "integer", "minimum": 1, "maximum": 70, "default": 60},
    }, ("archetype",)),
    _tool("run_verify", "Run the statistical checks against design/part-14 tuning targets (verify.py). Takes a few seconds.", {
        "suite": {"type": "string", "enum": ["reception", "creative", "all"], "default": "all"},
    }),
]


def _truncate_lists(value, limit: int = 8):
    if isinstance(value, list):
        head = [_truncate_lists(v, limit) for v in value[:limit]]
        return head + ([f"... {len(value) - limit} more"] if len(value) > limit else [])
    if isinstance(value, dict):
        return {k: _truncate_lists(v, limit) for k, v in value.items()}
    return value


class CallbackMcp:
    def __init__(self):
        self.games = GameRegistry()

    # ---- tool implementations ----------------------------------------------------------------

    def run_tool(self, name: str, a: dict) -> object:
        schema = next((t["inputSchema"] for t in TOOLS if t["name"] == name), None)
        if schema is None:
            raise GameError(f"unknown tool {name!r}")
        missing = [r for r in schema["required"] if r not in a]
        if missing:
            raise GameError(f"missing required argument(s): {', '.join(missing)}")
        if name == "new_game":
            return self.games.new_game(a["background"], a["ambition"], a.get("seed"))
        if name == "game_status":
            return self.games.status(a["game_id"])
        if name == "call_session":
            return self.games.call(a["game_id"], a["method"], a.get("args"))
        if name == "list_methods":
            return describe_methods(a.get("query", ""))
        if name == "auto_play":
            result = self.games.auto_play(a["game_id"], a.get("years", 1))
            t = result["transcript"]
            if len(t) > TRANSCRIPT_LIMIT:
                result["transcript"] = "...[earlier output trimmed]...\n" + t[-TRANSCRIPT_LIMIT:]
            return result
        if name == "list_games":
            return self.games.list_games()
        if name == "close_game":
            self.games.close(a["game_id"])
            return f"closed {a['game_id']}"
        if name == "run_archetype":
            if a["archetype"] not in ARCHETYPES:
                raise GameError(f"unknown archetype; choose from {list(ARCHETYPES)}")
            fn = getattr(_archetype_policies, a["archetype"])
            return _truncate_lists(to_plain(fn(seed=int(a.get("seed", 1)), years=int(a.get("years", 60)))))
        if name == "run_verify":
            suite = a.get("suite", "all")
            if suite not in ("reception", "creative", "all"):
                raise GameError("suite must be reception, creative or all")
            proc = subprocess.run(
                [sys.executable, "-m", "callback.engine.simulation.verify", suite],
                cwd=REPO_ROOT, capture_output=True, text=True, timeout=600,
            )
            return {"exit_code": proc.returncode, "output": (proc.stdout + proc.stderr)[-TRANSCRIPT_LIMIT:]}
        raise GameError(f"unknown tool {name!r}")

    # ---- JSON-RPC --------------------------------------------------------------------------------

    def handle(self, msg: dict) -> dict | None:
        method = msg.get("method")
        msg_id = msg.get("id")
        if msg_id is None:  # a notification (e.g. notifications/initialized): never answered
            return None
        params = msg.get("params") or {}
        if method == "initialize":
            requested = params.get("protocolVersion")
            version = requested if requested in SUPPORTED_PROTOCOLS else SUPPORTED_PROTOCOLS[0]
            return _ok(msg_id, {"protocolVersion": version, "capabilities": {"tools": {"listChanged": False}},
                                "serverInfo": SERVER_INFO, "instructions": INSTRUCTIONS})
        if method == "ping":
            return _ok(msg_id, {})
        if method == "tools/list":
            return _ok(msg_id, {"tools": TOOLS})
        if method == "tools/call":
            name = params.get("name", "")
            try:
                result = self.run_tool(name, params.get("arguments") or {})
                text = result if isinstance(result, str) else json.dumps(result, indent=1, ensure_ascii=False)
                return _ok(msg_id, {"content": [{"type": "text", "text": text}], "isError": False})
            except GameError as exc:
                return _ok(msg_id, {"content": [{"type": "text", "text": str(exc)}], "isError": True})
            except Exception as exc:  # noqa: BLE001 - an engine crash is a finding; report it, keep serving
                tb = traceback.format_exc(limit=6)
                return _ok(msg_id, {"content": [{"type": "text", "text": f"engine error: {exc!r}\n{tb}"}], "isError": True})
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"method not found: {method}"}}


def _ok(msg_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def main() -> int:
    protocol_out = sys.stdout
    sys.stdout = sys.stderr  # anything else that prints must not corrupt the protocol stream
    server = CallbackMcp()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        else:
            reply = server.handle(msg) if isinstance(msg, dict) else None
        if reply is not None:
            protocol_out.write(json.dumps(reply, ensure_ascii=False) + "\n")
            protocol_out.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
