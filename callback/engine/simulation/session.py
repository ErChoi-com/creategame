"""The player-facing façade. Every other file in this package (career.py, full_career.py,
bands.py, and every actor/rolodex/leverage/life/world/awards module underneath them) is engine —
built to be composed, tested, and reused, not to be handed to a UI directly.

Session is the one thing a UI (simulation/cli.py, or anything else built on this engine later)
should ever import from callback.engine. Its whole surface is: plain method calls in, plain data
(strings, numbers, small dicts/tuples) out — no Role, ActorState, ReceptionResult, StandingModel,
or any other engine type ever crosses this boundary. If a screen needs to know something, Session
has a method that returns exactly that, already shaped for printing.

This is also where the built-but-previously-unreachable systems get wired into actual play:
rolodex/interactions.py (check in / show up / read their agenda / vouch), leverage/catalogue.py
(agent-tier progression, Disappear/Scarcity), and awards/awards.py (a real campaign after a
Notices-worthy project) were all implemented and tested earlier but never called from anywhere a
player could reach. They're reachable through this file now.

Not wired here, and said plainly rather than faked shallow: leverage/indispensability.py's
holdout needs a tracked "this is installment N of a franchise" concept this pass never built, and
director/ is a second playable career — a different Session entirely. Both are real, tested
engine code with no player-facing entry point yet.
"""
from __future__ import annotations

import random
from dataclasses import replace

from callback.engine.actor.offers import Role, offer_probability, resolve_casting_path
from callback.engine.actor.persona import GENRES
from callback.engine.actor.positions import DIAL_LABELS, DIALS, PLAYER_LABELS, POSITIONS, generosity, upstaging
from callback.engine.actor.prep import PREP_OPTIONS, WING_IT
from callback.engine.actor.release import RELEASE_STRATEGIES, WIDE, LIMITED, weekly_gross_curve
from callback.engine.actor.script_notes import SCRIPT_NOTE_OPTIONS, apply_script_note
from callback.engine.actor.studios import STUDIOS
from callback.engine.awards.awards import NarrativeContext, buzz_score, narrative_bonus
from callback.engine.leverage.approvals import can_negotiate_approvals, fee_after_approvals
from callback.engine.leverage.catalogue import accumulate_scarcity, advance_agent_tier, can_advance_agent_tier, next_agent_tier
from callback.engine.rolodex import interactions as rolodex_interactions
from callback.engine.simulation._backgrounds import BACKGROUND_TABLE, REGIONAL_STAGE_START_AGE
from callback.engine.simulation._release_labels import RELEASE_LABELS
from callback.engine.simulation.bands import audience_band, critic_band, performance_band, relationship_band, roi_band, standing_band
from callback.engine.simulation.career import ProjectResult
from callback.engine.simulation.full_career import (
    FullState,
    accept_and_play,
    advance_between_years,
    decline_and_resolve,
    new_full_state,
    obituary,
    offer_this_year,
    utility_for,
)

MAX_AGE = 90
AWARDS_NOTICES_THRESHOLD = 68.0  # a project has to be genuinely well-received to be buzz-worthy
FAVOUR_GAIN_ON_SERVED_AGENDA = 1
STANDING_WEIGHTS = {"heat": 0.4, "prestige": 0.3, "affection": 0.3}  # a general-purpose read, not a gatekeeper profile


class Session:
    """One player's run, start to obituary. Owns all engine state; exposes none of it directly."""

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)
        self.state: FullState | None = None
        self.ambition: str = ""
        self._role: Role | None = None
        self._would_be_offered: bool = False
        self._approvals: frozenset[str] = frozenset()
        self._prep_choice: str | None = None
        self._scenes: list[dict[str, str]] = []
        self._last_result: ProjectResult | None = None
        self._script_note = None
        self._orientation_npc_id: str | None = None
        self._orientation_effect = None
        self._requested_director_npc_id: str | None = None

    # ---- character creation ----------------------------------------------------------------

    @staticmethod
    def background_options() -> list[tuple[str, str, str]]:
        """(key, name, tagline)."""
        return [(k, v[0], v[1]) for k, v in BACKGROUND_TABLE.items()]

    @staticmethod
    def ambition_options() -> list[tuple[str, str]]:
        return [
            ("work", "The Work"), ("prize", "The Prize"), ("fortune", "The Fortune"),
            ("run", "The Run"), ("franchise", "The Franchise"), ("voice", "The Voice"),
        ]

    def start(self, background_key: str, ambition_key: str) -> str:
        name, _, attrs, money = BACKGROUND_TABLE.get(background_key, BACKGROUND_TABLE["conservatory"])
        start_age = REGIONAL_STAGE_START_AGE if background_key == "regional_stage" else 22

        state = new_full_state(self.rng, start_age=start_age)
        state = replace(state, actor=replace(state.actor, attrs=attrs.clamped()))
        if money is not None:
            state = replace(state, life=replace(state.life, money=money))
        self.state = state
        self.ambition = dict(self.ambition_options()).get(ambition_key, "The Work")
        return f"You are, at heart, {name}. You're chasing {self.ambition}."

    # ---- the hub ------------------------------------------------------------------------------

    def age(self) -> int:
        return self.state.actor.age

    def is_over(self) -> bool:
        return self.state.actor.age >= MAX_AGE

    def standing_summary(self) -> str:
        sc = self.state.actor.standing.weighted_score(STANDING_WEIGHTS)
        return standing_band(sc)

    # ---- the offer board ------------------------------------------------------------------

    def roll_offer(self) -> dict:
        role = offer_this_year(self.state, self.rng)
        utility = utility_for(self.state, role)
        path = resolve_casting_path(utility, role)
        would_offer = path == "direct_offer" or self.rng.random() < offer_probability(utility, role.difficulty)

        self._role = role
        self._would_be_offered = would_offer
        studio = STUDIOS[role.studio]
        return {
            "genre": role.genre,
            "billing": role.billing,
            "budget_millions": round(role.budget_for_role, 2),
            "available": would_offer,
            "union": role.union,
            "studio_name": studio.name,
            "studio_tagline": studio.tagline,
        }

    def accept(self) -> None:
        if not self._would_be_offered:
            raise ValueError("this offer never came through — check roll_offer()['available'] first")
        self._script_note = None
        self._orientation_npc_id = None
        self._orientation_effect = None
        self._requested_director_npc_id = None

    def decline(self) -> dict:
        """Resolves the role through the background industry (§10.0) and advances the year."""
        self.state = decline_and_resolve(self.state, self._role, self.rng)
        self.state = advance_between_years(self.state, self.rng, worked_this_year=False)
        record = self.state.declined[-1]
        return {
            "genre": record.role_genre,
            "roi_band": roi_band(record.result.reception.roi),
            "critic_band": critic_band(record.result.reception.film_critic_score),
        }

    # ---- the deal -----------------------------------------------------------------------------

    def approvals_available(self) -> bool:
        sc = self.state.actor.standing.weighted_score(STANDING_WEIGHTS)
        return can_negotiate_approvals(sc)

    def choose_deal(self, want_approvals: bool) -> float | None:
        if want_approvals and self.approvals_available():
            self._approvals = frozenset({"script", "costar"})
            return round(fee_after_approvals(self._role.budget_for_role, self._approvals), 2)
        self._approvals = frozenset()
        return None

    # ---- script notes (§5.15) — only if the Deal secured script approval --------------------

    def script_notes_available(self) -> bool:
        return "script" in self._approvals

    @staticmethod
    def script_note_options() -> list[tuple[str, str]]:
        return [
            ("clarity", "Push for clarity — audiences follow it, critics call it obvious"),
            ("ambiguity", "Push for ambiguity — critics lean in, audiences find it cold"),
            ("your_part", "Push for your part — you read better, the script reads worse"),
            ("whole_film", "Push for the whole film — nothing in it for you, but it gets better"),
        ]

    def choose_script_note(self, key: str) -> None:
        self._script_note = apply_script_note(key) if key in SCRIPT_NOTE_OPTIONS else None

    # ---- request your director — pull a tracked Rolodex director onto the project ----------

    DIRECTOR_REQUEST_FAVOUR_COST = 2

    def available_directors(self) -> list[dict]:
        return [
            {"id": n.npc_id, "relationship": relationship_band(n.relationship_state),
             "favour_balance": self.state.leverage.favours.balance(n.npc_id)}
            for n in self.state.rolodex.tracked() if n.npc_type == "director"
        ]

    def request_director(self, npc_id: str) -> str:
        favours = self.state.leverage.favours
        if not favours.can_spend(npc_id, self.DIRECTOR_REQUEST_FAVOUR_COST):
            return "They don't owe you enough for that yet."
        self.state = replace(self.state, leverage=replace(
            self.state.leverage, favours=favours.spend(npc_id, self.DIRECTOR_REQUEST_FAVOUR_COST),
        ))
        self._requested_director_npc_id = npc_id
        return "They're directing this one."

    # ---- your scene partner — how you play toward them this project ------------------------

    def costar_options(self) -> list[dict]:
        return [
            {"id": n.npc_id, "relationship": relationship_band(n.relationship_state)}
            for n in self.state.rolodex.tracked() if n.npc_type == "costar"
        ]

    @staticmethod
    def orientation_options() -> list[tuple[str, str]]:
        return [
            ("neutral", "Play it straight"),
            ("generous", "Be generous — let them have the moment"),
            ("upstage", "Take the moment — upstage them"),
        ]

    def choose_orientation(self, npc_id: str | None, choice: str) -> None:
        self._orientation_npc_id = npc_id
        if choice == "generous":
            self._orientation_effect = generosity()
        elif choice == "upstage":
            self._orientation_effect = upstaging()
        else:
            self._orientation_effect = None

    # ---- prep -----------------------------------------------------------------------------

    @staticmethod
    def prep_options() -> list[tuple[str, str]]:
        return [(o, o.replace("_", " ")) for o in PREP_OPTIONS if o != WING_IT]

    def choose_prep(self, key: str) -> None:
        self._prep_choice = key

    # ---- the shoot ----------------------------------------------------------------------------

    @staticmethod
    def scene_names() -> list[str]:
        return ["the setup", "the turn", "the resolution"]

    @staticmethod
    def dial_options() -> list[tuple[str, str]]:
        return [(d, DIAL_LABELS[d]) for d in DIALS]

    @staticmethod
    def position_options() -> list[tuple[str, str]]:
        return [(p, PLAYER_LABELS[p]) for p in POSITIONS]

    def play_scene(self, choices: dict[str, str]) -> None:
        """Call once per scene, in order (3 calls total per project — see scene_names())."""
        self._scenes.append(choices)

    # ---- release --------------------------------------------------------------------------

    @staticmethod
    def release_options() -> list[tuple[str, str]]:
        return [(s, RELEASE_LABELS[s]) for s in RELEASE_STRATEGIES]

    def choose_release(self, strategy: str) -> dict:
        """Resolves the whole project — the one point everything collected since roll_offer()
        actually gets spent — and advances the year. Returns the Post & Release summary."""
        scenes = tuple(self._scenes) if len(self._scenes) == 3 else (self._scenes + [{}] * 3)[:3]
        self.state, result = accept_and_play(
            self.state, self._role, self._prep_choice or "table_work", scenes, self.rng,
            release_strategy=strategy,
            script_note=self._script_note,
            orientation_npc_id=self._orientation_npc_id,
            orientation_effect=self._orientation_effect,
            requested_director_npc_id=self._requested_director_npc_id,
        )
        self.state = advance_between_years(self.state, self.rng, worked_this_year=True, billing=self._role.billing)
        self._last_result = result
        self._scenes = []

        return {
            "performance_band": performance_band(result.performance),
            "critic_band": critic_band(result.film_critic_score),
            "critic_score": round(result.film_critic_score),
            "audience_band": audience_band(result.audience_score),
            "release_label": RELEASE_LABELS[strategy],
            "studio_name": STUDIOS[result.studio_id].name,
            "roi_band": roi_band(result.roi),
            "gross_millions": round(result.gross, 1),
            "budget_millions": round(result.budget, 1),
            "roi": round(result.roi, 2),
            "weekly_gross": self._weekly_gross(result, strategy),
        }

    @staticmethod
    def _weekly_gross(result: ProjectResult, strategy: str) -> list[float] | None:
        if strategy not in (WIDE, LIMITED) or result.gross <= 0:
            return None
        return [round(w, 1) for w in weekly_gross_curve(result.opening, result.legs, weeks=5)]

    # ---- awards (§4.11) — wired in for the first time here -------------------------------

    def awards_campaign_available(self) -> bool:
        return self._last_result is not None and self._last_result.notices >= AWARDS_NOTICES_THRESHOLD

    def run_awards_campaign(self, spend_millions: float = 1.0) -> dict:
        """A real BuzzScore campaign, resolved on the spot against a handful of generated
        competitors — not the full multi-year awards-season calendar (out of scope), but a real
        use of awards/awards.py's formulas instead of leaving them unreachable."""
        r = self._last_result
        prestige = self.state.actor.standing["prestige"]
        ctx = NarrativeContext(is_first_nomination=self.state.actor.credits <= 3, age=self.state.actor.age)
        bonus = narrative_bonus(ctx)
        your_buzz = buzz_score(r.notices, r.film_critic_score, spend_millions, prestige, bonus, 0.0, self.rng)
        competitors = [
            buzz_score(self.rng.gauss(55, 15), self.rng.gauss(55, 10), self.rng.uniform(0.2, 2.0),
                       self.rng.gauss(50, 20), 0.0, 0.0, self.rng)
            for _ in range(4)
        ]
        won = your_buzz > max(competitors)
        nominated = won or your_buzz > sorted(competitors)[1]
        return {"won": won, "nominated": nominated, "narrative_bonus": bonus}

    # ---- the pull menu: Rolodex, Leverage, Trades -----------------------------------------

    def trades(self) -> list[str]:
        from callback.engine.world.trades import generate_digest
        return generate_digest(self.state.genre_heat, self.state.rolodex, GENRES)

    def rolodex_summary(self) -> list[dict]:
        return [
            {"id": n.npc_id, "type": n.npc_type, "relationship": relationship_band(n.relationship_state)}
            for n in self.state.rolodex.tracked()
        ]

    def interact(self, npc_id: str, action: str) -> str:
        """action: "check_in" | "show_up" | "read_agenda" | "vouch". Returns a short result line."""
        npc = self.state.rolodex.npcs.get(npc_id)
        if npc is None:
            return "You don't know them well enough for that yet."

        year = self.age()
        before = npc.relationship_state
        if action == "check_in":
            updated = rolodex_interactions.check_in(npc, year)
        elif action == "show_up":
            updated = rolodex_interactions.show_up_for_them(npc, year)
        elif action == "read_agenda":
            served = self.rng.random() < 0.5  # the player is genuinely guessing, same as a real read
            updated = rolodex_interactions.read_agenda_and_act(npc, served, year)
            if served:
                leverage = replace(self.state.leverage, favours=self.state.leverage.favours.credit(npc_id, FAVOUR_GAIN_ON_SERVED_AGENDA))
                self.state = replace(self.state, leverage=leverage)
        elif action == "vouch":
            updated = rolodex_interactions.vouch_for_them(npc, year)
        else:
            return "Not sure how to do that."

        npcs = dict(self.state.rolodex.npcs)
        npcs[npc_id] = updated
        self.state = replace(self.state, rolodex=replace(self.state.rolodex, npcs=npcs))

        if updated.relationship_state != before:
            return f"Now: {relationship_band(updated.relationship_state)}."
        return "Noted. Nothing's changed yet."

    def leverage_status(self) -> dict:
        lev = self.state.leverage
        return {"agent_tier": lev.agent_tier, "scarcity": round(lev.scarcity, 1), "next_tier": next_agent_tier(lev.agent_tier)}

    def try_advance_agent_tier(self) -> str:
        sc = self.state.actor.standing.weighted_score(STANDING_WEIGHTS)
        lev = self.state.leverage
        if not can_advance_agent_tier(lev.agent_tier, sc):
            nxt = next_agent_tier(lev.agent_tier)
            return f"Not yet — {nxt} wants more Standing than you're carrying." if nxt else "You're already at the top."
        new_tier = advance_agent_tier(lev.agent_tier, sc)
        self.state = replace(self.state, leverage=replace(lev, agent_tier=new_tier))
        return f"Signed with a {new_tier} agency."

    def disappear(self) -> str:
        """§6.6 — a real pull action: skip the next offer on purpose, banking Scarcity for a
        better one when you come back."""
        lev = self.state.leverage
        self.state = replace(self.state, leverage=replace(lev, scarcity=accumulate_scarcity(lev.scarcity)))
        self.state = advance_between_years(self.state, self.rng, worked_this_year=False)
        return "You go quiet for a year. People notice, eventually, when you come back."

    # ---- the obituary -----------------------------------------------------------------------

    def obituary_summary(self) -> dict:
        ob = obituary(self.state)
        return {
            "credits": len(ob.filmography),
            "declined": [
                {"genre": d.role_genre, "roi_band": roi_band(d.result.reception.roi),
                 "critic_band": critic_band(d.result.reception.film_critic_score)}
                for d in ob.declined
            ],
            "kept": len(ob.kept),
            "lost": len(ob.lost),
            "best_hidden_performance": (
                {"genre": ob.best_hidden_performance.role.genre, "band": performance_band(ob.best_hidden_performance.performance)}
                if ob.best_hidden_performance else None
            ),
        }
