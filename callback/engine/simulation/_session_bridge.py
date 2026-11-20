"""callback/engine/README.md's player-facing boundary, served to remote UIs: the shared game
registry and Session dispatch behind mcp_server.py (AI agents over MCP) and web_server.py (the
TypeScript frontend in web/). Like cli.py, the only engine type used here is Session. Every value
that leaves this module passes through to_plain(), so no engine dataclass can cross the wire.

choose_release()'s bid selectors are the one place Session hands a UI engine objects (the
StreamingBid / FestivalBid pool, which cli.py reads in place). Remote callers can't answer a
callback mid-resolution, so they pick a policy up front ("best" payout, or "self" to keep the film)
and get the chosen bid back as plain data.
"""
from __future__ import annotations

import contextlib
import inspect
import io
import itertools
import time

from callback.engine.simulation import cli
from callback.engine.simulation.session import Session

MAX_GAMES = 64
MAX_AUTO_YEARS = 60

# Read-only queries that make up the status dashboard. Each is tried independently, because some
# (director_status, for one) only make sense in certain states.
STATUS_QUERIES = (
    "age", "is_over", "standing_summary", "persona_status", "application_status", "leverage_status",
    "franchise_status", "multi_picture_deal_status", "merchandising_status", "directing_unlocked",
    "is_directing", "actor_quarters_remaining_this_year", "quarters_remaining_this_year",
)

# Grouping that mirrors the year's flow (cli.acting_block / directing_block), used to describe the
# method catalogue to an agent or a UI.
METHOD_GROUPS = (
    ("character creation", ("background_options", "ambition_options", "start")),
    ("hub", ("age", "is_over", "standing_summary", "persona_status", "application_status")),
    ("offer board", ("offer_board", "generate_more_listings", "director_info", "accept", "decline_board")),
    ("franchise holdout", ("holdout_available", "request_holdout", "franchise_status", "spinoff_options", "launch_spinoff")),
    ("the deal", ("box_office_bonus_available", "box_office_bonus_type_options", "approvals_available",
                  "merchandising_available", "choose_deal", "multi_picture_deal_available", "multi_picture_deal_terms",
                  "sign_multi_picture_deal", "request_marketing_push")),
    ("on set", ("script_notes_available", "script_note_options", "choose_script_note", "available_directors",
                "request_director", "costar_options", "orientation_options", "choose_orientation",
                "prep_options", "choose_prep")),
    ("the shoot", ("is_series", "episode_labels", "scene_names", "dial_options", "position_options", "play_scene")),
    ("post & release", ("rating_preview", "rating_cut_options", "choose_rating_stance", "release_options",
                        "streaming_bid_options", "festival_bid_options", "choose_release")),
    ("awards", ("awards_campaign_available", "available_award_categories", "run_awards_campaign")),
    ("pull menu", ("trades", "rolodex_summary", "interact", "leverage_status", "try_advance_agent_tier",
                   "disappear", "cut_lifestyle_floor")),
    ("directing", ("directing_unlocked", "become_director", "director_status", "director_genre_options",
                   "director_budget_tier_options", "start_directing_project", "director_dev_action_options",
                   "advance_directing", "scrap_directing_project", "check_for_hire_offer", "accept_hire_offer",
                   "decline_hire_offer", "run_director_awards_campaign")),
    ("calendar", ("end_year", "obituary_summary")),
)


class GameError(ValueError):
    """A caller mistake (unknown game, method or argument). Reported back, never fatal."""


def to_plain(value):
    """JSON-safe copy of whatever Session returned. Session promises plain data; this enforces it."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(k): to_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_plain(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted(to_plain(v) for v in value)
    return repr(value)


def _public_methods() -> dict[str, inspect.Signature]:
    """Every public Session method's signature, minus `self` (static methods have none)."""
    out = {}
    for name, fn in inspect.getmembers(Session, predicate=inspect.isfunction):
        if name.startswith("_"):
            continue
        sig = inspect.signature(fn)
        if not isinstance(inspect.getattr_static(Session, name), staticmethod):
            sig = sig.replace(parameters=list(sig.parameters.values())[1:])
        out[name] = sig
    return out


PUBLIC_METHODS = _public_methods()


def describe_methods(query: str = "") -> list[dict]:
    """[{name, group, signature, doc}] for every public Session method, filtered by substring."""
    group_of = {}
    for group, names in METHOD_GROUPS:
        for n in names:
            group_of.setdefault(n, group)
    q = query.lower()
    rows = []
    for name, sig in PUBLIC_METHODS.items():
        doc = inspect.getdoc(getattr(Session, name)) or ""
        first_para = doc.split("\n\n", 1)[0].replace("\n", " ")
        params = str(sig)
        if name == "choose_release":
            params = "(strategy: str, streaming_multiplier: float | None = None, bid_policy: 'best' | 'self' = 'best')"
        row = {"name": name, "group": group_of.get(name, "other"), "signature": f"{name}{params}", "doc": first_para}
        if not q or q in name.lower() or q in row["group"] or q in first_para.lower():
            rows.append(row)
    return sorted(rows, key=lambda r: (r["group"], r["name"]))


def _pick_bid(policy: str, record: dict):
    """A bid selector for choose_release that records what it picked as plain data."""
    def select(bids):
        own = [b for b in bids if getattr(b, "self_release", False) or getattr(b, "self_distribute", False)]
        chosen = own[0] if policy == "self" and own else max(bids, key=lambda b: b.payout_millions)
        record.update({
            "studio_name": chosen.studio_name,
            "payout_millions": round(chosen.payout_millions, 2),
            "kept_it": bool(getattr(chosen, "self_release", False) or getattr(chosen, "self_distribute", False)),
            "offers": len(bids),
        })
        return chosen
    return select


class GameRegistry:
    """In-memory games, keyed by id. Oldest is evicted past MAX_GAMES."""

    def __init__(self):
        self._games: dict[str, dict] = {}
        self._ids = itertools.count(1)

    def new_game(self, background: str, ambition: str, seed: int | None = None) -> dict:
        valid_bg = [k for k, _, _ in Session.background_options()]
        valid_amb = [k for k, _ in Session.ambition_options()]
        if background not in valid_bg:
            raise GameError(f"unknown background {background!r}; choose from {valid_bg}")
        if ambition not in valid_amb:
            raise GameError(f"unknown ambition {ambition!r}; choose from {valid_amb}")
        seed = seed if seed is not None else int(time.time() * 1000) % 1_000_000
        session = Session(seed=seed)
        intro = session.start(background, ambition)
        game_id = f"g{next(self._ids)}"
        self._games[game_id] = {"session": session, "seed": seed, "background": background, "ambition": ambition}
        while len(self._games) > MAX_GAMES:
            self._games.pop(next(iter(self._games)))
        return {"game_id": game_id, "seed": seed, "intro": intro, "status": self.status(game_id)}

    def session(self, game_id: str) -> Session:
        game = self._games.get(game_id)
        if game is None:
            raise GameError(f"no game {game_id!r}; active games: {list(self._games) or 'none'}")
        return game["session"]

    def list_games(self) -> list[dict]:
        return [
            {"game_id": gid, "seed": g["seed"], "background": g["background"], "ambition": g["ambition"],
             "age": g["session"].age(), "is_over": g["session"].is_over()}
            for gid, g in self._games.items()
        ]

    def close(self, game_id: str) -> None:
        self.session(game_id)
        del self._games[game_id]

    def status(self, game_id: str) -> dict:
        session = self.session(game_id)
        out = {"game_id": game_id}
        for name in STATUS_QUERIES:
            try:
                out[name] = to_plain(getattr(session, name)())
            except Exception:  # noqa: BLE001 - a query that doesn't apply in this state is skipped
                continue
        if out.get("is_directing"):
            try:
                out["director_status"] = to_plain(session.director_status())
            except Exception:  # noqa: BLE001
                pass
        return out

    def call(self, game_id: str, method: str, args: dict | None = None) -> object:
        session = self.session(game_id)
        if method not in PUBLIC_METHODS:
            raise GameError(f"unknown Session method {method!r}; use list_methods to see the catalogue")
        args = dict(args or {})
        if method == "choose_release":
            policy = args.pop("bid_policy", "best")
            if policy not in ("best", "self"):
                raise GameError("bid_policy must be 'best' or 'self'")
            record: dict = {}
            args["streaming_bid_selector"] = _pick_bid(policy, record)
            args["festival_bid_selector"] = _pick_bid(policy, record)
        sig = PUBLIC_METHODS[method]
        try:
            sig.bind(**args)
        except TypeError as exc:
            raise GameError(f"bad arguments for {method}{sig}: {exc}") from None
        result = getattr(session, method)(**args)
        if method == "choose_release":
            result = dict(result or {})
            if record:
                result["bid_taken"] = record
        return to_plain(result)

    def auto_play(self, game_id: str, years: int = 1) -> dict:
        """Plays whole years with the CLI's own auto defaults (cli.play_year); returns the transcript."""
        session = self.session(game_id)
        years = max(1, min(int(years), MAX_AUTO_YEARS))
        buf = io.StringIO()
        played = 0
        with contextlib.redirect_stdout(buf):
            for _ in range(years):
                if session.is_over():
                    break
                cli.play_year(session, auto=True)
                played += 1
        return {"years_played": played, "transcript": buf.getvalue(), "status": self.status(game_id)}
