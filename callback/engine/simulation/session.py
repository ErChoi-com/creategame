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
Spotlight-worthy project) were all implemented and tested earlier but never called from anywhere a
player could reach. They're reachable through this file now.

leverage/indispensability.py's holdout is wired in too, now that simulation/_franchises.py gives
it the "this is installment N of a franchise" tracking it needs — see franchise_status()/
holdout_available()/request_holdout() below, composed with genre/franchise.py's sequel-value
curve and director/skill.py's engagement bonus for a director returning to their own franchise.

The director career (director/) is fused into this same Session/FullState rather than a second
Session — a sufficiently prestigious actor can cross into directing (become_director()) and the
two tracks share one calendar (a year spent developing/shooting a directed project is a year not
spent acting) and one Standing philosophy, via simulation/_director.py. See
directing_unlocked()/become_director()/director_status()/advance_directing() below — a distinct
set of methods and a distinct CLI menu, not the acting screens repurposed.
"""
from __future__ import annotations

import random
from dataclasses import replace

from callback.engine.actor.offers import Role, offer_probability, resolve_casting_path
from callback.engine.actor.persona import GENRES
from callback.engine.actor.positions import DIAL_LABELS, DIALS, PLAYER_LABELS, POSITIONS, generosity, upstaging
from callback.engine.actor.prep import PREP_OPTIONS, WING_IT
from callback.engine.actor.release import RELEASE_STRATEGIES, STREAMING_BUYOUT_MULTIPLIER, WIDE, LIMITED, weekly_gross_curve
from callback.engine.actor.script_notes import SCRIPT_NOTE_OPTIONS, apply_script_note
from callback.engine.actor.studios import SELF_DISTRIBUTE_MULTIPLIER, STUDIOS, streaming_bidders
from callback.engine.awards.awards import NarrativeContext, buzz_score, narrative_bonus
from callback.engine.leverage.approvals import (
    box_office_bonus_earned,
    can_negotiate_approvals,
    can_negotiate_box_office_bonus,
    fee_after_approvals,
)
from callback.engine.leverage.catalogue import accumulate_scarcity, advance_agent_tier, can_advance_agent_tier, next_agent_tier
from callback.engine.rolodex import interactions as rolodex_interactions
from callback.engine.simulation._backgrounds import BACKGROUND_TABLE, REGIONAL_STAGE_START_AGE
from callback.engine.simulation._franchises import FRANCHISE_INDISPENSABILITY_HOLDOUT_THRESHOLD
from callback.engine.leverage.indispensability import recast_cost, resolve_holdout
from callback.engine.director.development import DEV_ACTIONS
from callback.engine.studio.slate import TIER_BUDGETS
from callback.engine.simulation._director import (
    DIRECTOR_UNLOCK_MIN_CREDITS,
    DIRECTOR_UNLOCK_PRESTIGE,
    apply_dev_action_and_advance,
    new_director_state,
    start_development,
)
from callback.engine.world.genre_cycle import accumulate_heat
from callback.engine.world.genre_cycle import genre_demand as world_genre_demand
from callback.engine.world.guild import add_residual_stream
from callback.engine.simulation._relationships import trust_band, utility_bonus_from_trust
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
AWARDS_SPOTLIGHT_THRESHOLD = 68.0  # a project has to be genuinely well-received to be buzz-worthy
FAVOUR_GAIN_ON_SERVED_AGENDA = 1
OFFER_BOARD_MIN_LISTINGS = 20
OFFER_BOARD_MAX_LISTINGS = 30
OFFER_BOARD_GENERATE_MORE_BATCH = 10
STANDING_WEIGHTS = {"heat": 0.4, "prestige": 0.3, "affection": 0.3}  # a general-purpose read, not a gatekeeper profile


class Session:
    """One player's run, start to obituary. Owns all engine state; exposes none of it directly."""

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)
        self.state: FullState | None = None
        self.ambition: str = ""
        self._role: Role | None = None
        self._board: list[Role] = []
        self._board_would_offer: list[bool] = []
        self._approvals: frozenset[str] = frozenset()
        self._box_office_bonus_negotiated: bool = False
        self._prep_choice: str | None = None
        self._scenes: list[dict[str, str]] = []
        self._last_result: ProjectResult | None = None
        self._script_note = None
        self._orientation_npc_id: str | None = None
        self._orientation_effect = None
        self._requested_director_npc_id: str | None = None
        # This year's calendar-advance inputs, accumulated by whatever you did this year (acting
        # and/or directing — see end_year()) and applied exactly once when the year actually ends.
        self._acting_worked_this_year: bool = False
        self._pending_billing: str | None = None
        self._pending_bonus_income: float = 0.0

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

    def offer_board(self, size: int | None = None) -> list[dict]:
        """A real multi-listing board (§4.4's own vision) rather than a single yearly roll — the
        engine's role generator (actor/offers.sample_role) isn't Standing-aware yet, so procedurally
        generating a lot of listings per year is this pass's mitigation: more looks at the dice, not
        a smarter die. size=None picks a procedurally varying board (at least
        OFFER_BOARD_MIN_LISTINGS) each year. Resets the board — call this once per year, then
        generate_more_listings() if that isn't enough."""
        n = size if size is not None else self.rng.randint(OFFER_BOARD_MIN_LISTINGS, OFFER_BOARD_MAX_LISTINGS)
        self._board = []
        self._board_would_offer = []
        return self._generate_listings(n)

    def generate_more_listings(self, count: int = OFFER_BOARD_GENERATE_MORE_BATCH) -> list[dict]:
        """Appends more listings to the current board rather than replacing it — the offer board
        isn't capped; there's always another audition to generate if the player wants to keep
        looking. Returns only the newly generated listings (their index continues the board's)."""
        return self._generate_listings(count)

    def _generate_listings(self, count: int) -> list[dict]:
        listings = []
        for _ in range(count):
            role = offer_this_year(self.state, self.rng)
            # A studio that's made money with you before wants you back; one you burned is
            # warier — a real memory, not just flavor text on the tagline.
            utility = utility_for(self.state, role) + utility_bonus_from_trust(self.state.studio_relations, role.studio)
            path = resolve_casting_path(utility, role)
            would_offer = path == "direct_offer" or self.rng.random() < offer_probability(utility, role.difficulty)
            index = len(self._board)
            self._board.append(role)
            self._board_would_offer.append(would_offer)
            studio = STUDIOS[role.studio]
            listings.append({
                "index": index,
                "genre": role.genre,
                "billing": role.billing,
                "budget_millions": round(role.budget_for_role, 2),
                "available": would_offer,
                "union": role.union,
                "studio_name": studio.name,
                "studio_tagline": studio.tagline,
                "franchise_id": role.franchise_id,
                "installment_number": role.installment_number,
            })
        return listings

    def accept(self, index: int) -> None:
        if not (0 <= index < len(self._board)):
            raise ValueError("no such listing on this year's offer_board()")
        if not self._board_would_offer[index]:
            raise ValueError("this offer never came through — check offer_board()[index]['available'] first")
        self._role = self._board[index]
        # everything else on the board quietly resolves through the background industry (§10.0),
        # same as a single declined offer always has — you only ever work one project a year.
        for i, role in enumerate(self._board):
            if i != index:
                self.state = decline_and_resolve(self.state, role, self.rng)
        self._script_note = None
        self._orientation_npc_id = None
        self._orientation_effect = None
        self._requested_director_npc_id = None
        self._box_office_bonus_negotiated = False

    def decline_board(self) -> list[dict]:
        """Passes on every listing on the board, resolves each through the background industry,
        Does not advance the year itself — you might still work on directing this year (see
        end_year()); call that once you're done with everything this year's turn covers."""
        results = []
        for role in self._board:
            self.state = decline_and_resolve(self.state, role, self.rng)
            record = self.state.declined[-1]
            results.append({
                "genre": record.role_genre,
                "roi_band": roi_band(record.result.reception.roi),
                "critic_band": critic_band(record.result.reception.film_critic_score),
            })
        return results

    # ---- franchises (design §9.5's sequel-value curve + §6.4-6.5's Indispensability holdout) --

    def franchise_status(self) -> list[dict]:
        return [
            {
                "id": f.franchise_id,
                "genre": f.genre,
                "studio_name": STUDIOS[f.studio_id].name,
                "installments": f.installments_starred,
                "indispensability": round(f.indispensability, 1),
                "recast_cost_millions": round(recast_cost(f.indispensability), 2),
            }
            for f in self.state.franchises.values()
        ]

    def holdout_available(self) -> bool:
        """True only right after accept()-ing a sequel (installment 2+) to a franchise you've
        built real Indispensability in — a brand-new franchise's part 1 has nothing to hold out
        for yet."""
        if self._role is None or not self._role.franchise_id or self._role.installment_number <= 1:
            return False
        f = self.state.franchises.get(self._role.franchise_id)
        return f is not None and f.indispensability >= FRANCHISE_INDISPENSABILITY_HOLDOUT_THRESHOLD

    def request_holdout(self) -> dict:
        """Leverage's real Indispensability holdout (§6.5): they either pay a raise, recast the
        part out from under you (the project doesn't happen this year, and you lose the
        franchise), or call your bluff and proceed at the original terms."""
        f = self.state.franchises[self._role.franchise_id]
        outcome = resolve_holdout(f.indispensability, f.prior_holdouts, self.rng)

        franchises = dict(self.state.franchises)
        franchises[f.franchise_id] = replace(f, prior_holdouts=f.prior_holdouts + 1)

        proceeds = True
        if outcome.they_paid:
            self._role = replace(self._role, budget_for_role=self._role.budget_for_role * outcome.raise_multiplier)
        elif outcome.recast:
            proceeds = False
            del franchises[f.franchise_id]
            standing = self.state.actor.standing.copy()
            standing.add("notoriety", outcome.notoriety_delta)
            self.state = replace(self.state, actor=replace(self.state.actor, standing=standing))

        self.state = replace(self.state, franchises=franchises)
        if not proceeds:
            self._role = None  # no project this year — the year still advances via end_year()

        return {
            "paid": outcome.they_paid,
            "recast": outcome.recast,
            "raise_multiplier": round(outcome.raise_multiplier, 2),
            "proceeds": proceeds,
        }

    # ---- the deal -----------------------------------------------------------------------------

    def approvals_available(self) -> bool:
        sc = self.state.actor.standing.weighted_score(STANDING_WEIGHTS)
        return can_negotiate_approvals(sc)

    def box_office_bonus_available(self) -> bool:
        """A real backend point — a much higher Standing bar than approvals, on purpose (§6.5's
        own executive-producer-credit row gates a small backend behind real weight, not a rubber
        stamp; this is the general-case version of that same idea)."""
        sc = self.state.actor.standing.weighted_score(STANDING_WEIGHTS)
        return can_negotiate_box_office_bonus(sc)

    def choose_deal(self, want_approvals: bool, want_box_office_bonus: bool = False) -> float | None:
        self._box_office_bonus_negotiated = want_box_office_bonus and self.box_office_bonus_available()
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
             "favour_balance": self.state.leverage.favours.balance(n.npc_id),
             "trust": self._director_trust(n.npc_id)}
            for n in self.state.rolodex.tracked() if n.npc_type == "director"
        ]

    def _director_trust(self, npc_id: str) -> dict | None:
        rel = self.state.director_relations.get(npc_id)
        if rel is None:
            return None
        return {"projects_together": rel.projects_together, "trust_band": trust_band(rel.trust)}

    # ---- studio and director relationships — profit and loss, remembered -------------------

    def studio_relations_status(self) -> list[dict]:
        return [
            {"studio_name": STUDIOS[rel.subject_id].name, "projects_together": rel.projects_together,
             "trust_band": trust_band(rel.trust), "net_profit_millions": round(rel.net_profit_millions, 1)}
            for rel in self.state.studio_relations.values()
        ]

    def director_relationship_status(self) -> list[dict]:
        return [
            {"id": rel.subject_id, "projects_together": rel.projects_together,
             "trust_band": trust_band(rel.trust), "net_profit_millions": round(rel.net_profit_millions, 1)}
            for rel in self.state.director_relations.values()
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

    def streaming_bid_options(self) -> list[dict]:
        """A real bidding pool for streaming rights, not one flat studio-default number — every
        studio whose money plays in this budget range makes an offer at its own terms, deterministic
        (no rng) so it's a stable menu to compare rather than a fresh roll each look. Always
        includes the financing studio's own SELF_DISTRIBUTE_MULTIPLIER option: they just put it up
        on their own service for nothing — you get your budget back, no more."""
        budget = self._role.budget_for_role
        bidders = streaming_bidders(budget, self._role.studio)
        options = [
            {
                "studio_id": s.id, "studio_name": s.name,
                "multiplier": round(STREAMING_BUYOUT_MULTIPLIER + s.streaming_multiplier_delta, 2),
                "payout_millions": round(budget * (STREAMING_BUYOUT_MULTIPLIER + s.streaming_multiplier_delta), 2),
                "self_distribute": False,
            }
            for s in bidders
        ]
        financing = STUDIOS[self._role.studio]
        options.append({
            "studio_id": financing.id, "studio_name": financing.name,
            "multiplier": SELF_DISTRIBUTE_MULTIPLIER,
            "payout_millions": round(budget * SELF_DISTRIBUTE_MULTIPLIER, 2),
            "self_distribute": True,
        })
        return options

    def choose_release(self, strategy: str, streaming_multiplier: float | None = None) -> dict:
        """Resolves the whole project — the one point everything collected since offer_board()
        actually gets spent. Does not advance the year itself (see end_year()) — you might also
        work on directing this same year; acting and directing no longer compete for the same
        calendar slot.

        streaming_multiplier: only meaningful when strategy == "streaming" — the specific bidder's
        terms from streaming_bid_options(), in place of the financing studio's own default."""
        scenes = tuple(self._scenes) if len(self._scenes) == 3 else (self._scenes + [{}] * 3)[:3]
        franchise_installment = self._role.installment_number
        self.state, result = accept_and_play(
            self.state, self._role, self._prep_choice or "table_work", scenes, self.rng,
            release_strategy=strategy,
            script_note=self._script_note,
            orientation_npc_id=self._orientation_npc_id,
            orientation_effect=self._orientation_effect,
            requested_director_npc_id=self._requested_director_npc_id,
            streaming_multiplier_override=streaming_multiplier if strategy == "streaming" else None,
        )
        bonus = box_office_bonus_earned(result.gross, result.roi) if self._box_office_bonus_negotiated else 0.0
        self._acting_worked_this_year = True
        self._pending_billing = self._role.billing
        self._pending_bonus_income = bonus
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
            "marketing_millions": round(result.marketing, 1),
            "roi": round(result.roi, 2),
            "weekly_gross": self._weekly_gross(result, strategy),
            "franchise_installment": franchise_installment,
            "box_office_bonus_millions": round(bonus, 2),
        }

    @staticmethod
    def _weekly_gross(result: ProjectResult, strategy: str) -> list[float] | None:
        if strategy not in (WIDE, LIMITED) or result.gross <= 0:
            return None
        return [round(w, 1) for w in weekly_gross_curve(result.opening, result.legs, weeks=5)]

    # ---- awards (§4.11) — wired in for the first time here -------------------------------

    def awards_campaign_available(self) -> bool:
        return self._last_result is not None and self._last_result.spotlight >= AWARDS_SPOTLIGHT_THRESHOLD

    def run_awards_campaign(self, spend_millions: float = 1.0) -> dict:
        """A real BuzzScore campaign, resolved on the spot against a handful of generated
        competitors — not the full multi-year awards-season calendar (out of scope), but a real
        use of awards/awards.py's formulas instead of leaving them unreachable."""
        r = self._last_result
        prestige = self.state.actor.standing["prestige"]
        ctx = NarrativeContext(is_first_nomination=self.state.actor.credits <= 3, age=self.state.actor.age)
        bonus = narrative_bonus(ctx)
        your_buzz = buzz_score(r.spotlight, r.film_critic_score, spend_millions, prestige, bonus, 0.0, self.rng)
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
        better one when you come back. Doesn't advance the year itself (see end_year())."""
        lev = self.state.leverage
        self.state = replace(self.state, leverage=replace(lev, scarcity=accumulate_scarcity(lev.scarcity)))
        return "You go quiet for a year. People notice, eventually, when you come back."

    # ---- directing — a second career fused into this same Session/FullState ------------------

    def directing_unlocked(self) -> bool:
        """Real weight in the room, not a rubber stamp: enough Prestige and enough credits to get
        someone to finance your own project."""
        return (
            self.state.actor.standing["prestige"] >= DIRECTOR_UNLOCK_PRESTIGE
            and self.state.actor.credits >= DIRECTOR_UNLOCK_MIN_CREDITS
        )

    def is_directing(self) -> bool:
        return self.state.director is not None

    def become_director(self) -> str:
        if self.state.director is not None:
            return "You're already directing."
        if not self.directing_unlocked():
            return "Not yet — you don't have the weight in the room for someone to finance your own film."
        self.state = replace(self.state, director=new_director_state())
        return "You step behind the camera for the first time."

    def director_status(self) -> dict:
        d = self.state.director
        in_development = d.current_project is not None
        return {
            "credits": d.credits,
            "standing": standing_band(d.standing.weighted_score(STANDING_WEIGHTS)),
            "in_development": in_development,
            "genre": d.current_genre if in_development else None,
            "budget_ask": round(d.current_project.budget_ask, 2) if in_development else None,
            "momentum": round(d.current_project.momentum, 2) if in_development else None,
            "quarters_in_dev": d.current_project.quarters_in_dev if in_development else 0,
        }

    @staticmethod
    def director_genre_options() -> list[tuple[str, str]]:
        return [(g, g.title()) for g in GENRES]

    @staticmethod
    def director_budget_tier_options() -> list[tuple[str, str]]:
        return [(tier, f"{tier.title()} — ${budget:.0f}M") for tier, budget in TIER_BUDGETS.items()]

    def start_directing_project(self, genre: str, budget_tier: str) -> None:
        budget = TIER_BUDGETS.get(budget_tier, TIER_BUDGETS["low"])
        self.state = replace(self.state, director=start_development(self.state.director, genre, budget, self.rng))

    @staticmethod
    def director_dev_action_options() -> list[tuple[str, str]]:
        labels = {
            "rewrite": "Rewrite — improve the script",
            "attach_star": "Attach a star — real bankability, real momentum",
            "cut_budget": "Cut the budget — easier to greenlight, less to work with",
            "new_financier": "Find a new financier",
            "take_to_market": "Take it to market",
            "self_finance": "Self-finance — guarantee it happens",
            "drawer": "Put it in the drawer — walk away for now",
        }
        return [(a, labels[a]) for a in DEV_ACTIONS]

    def advance_directing(self, action: str) -> dict:
        """One year's directing work — mirrors choose_release()'s one-project-a-year cadence on
        the acting side. Does not advance the shared calendar itself (see end_year()) — acting and
        directing no longer compete for the same year; you can do both in the same turn."""
        demand = world_genre_demand(self.state.genre_heat, self.state.director.current_genre)
        director, info = apply_dev_action_and_advance(self.state.director, action, demand, self.rng)

        genre_heat = self.state.genre_heat
        guild = self.state.guild
        if info["greenlit"]:
            genre_heat = accumulate_heat(genre_heat, info["genre"], info["roi"])
            guild = add_residual_stream(guild, info["roi"], info["budget"])

        self.state = replace(self.state, director=director, genre_heat=genre_heat, guild=guild)

        result = {"greenlit": info["greenlit"], "dead": info["dead"], "frozen": info.get("frozen", False),
                  "momentum": info["momentum"]}
        if info["greenlit"]:
            result.update({
                "critic_band": critic_band(info["film_critic_score"]),
                "critic_score": info["critic_score"],
                "audience_band": audience_band(info["audience_score"]),
                "roi_band": roi_band(info["roi"]),
                "roi": info["roi"],
                "gross_millions": info["gross_millions"],
                "budget_millions": round(info["budget"], 1),
                "marketing_millions": info["marketing_millions"],
            })
        return result

    # ---- the calendar — advances exactly once per year, however much you did in it -----------

    def end_year(self) -> None:
        """The one point the shared calendar actually moves: aging, Standing decay, Life, the
        Guild, Rolodex re-ranking, franchise dormancy. Call this once per year after resolving
        whatever combination of acting and/or directing you did — choose_release()/decline_board()/
        request_holdout()/advance_directing()/disappear() all resolve their own outcome (Standing
        deltas, money, a directed film's own result) immediately, but none of them touch the
        calendar anymore, so acting and directing are free to both happen in the same year."""
        self.state = advance_between_years(
            self.state, self.rng, worked_this_year=self._acting_worked_this_year,
            billing=self._pending_billing, bonus_income=self._pending_bonus_income,
        )
        self._acting_worked_this_year = False
        self._pending_billing = None
        self._pending_bonus_income = 0.0

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
