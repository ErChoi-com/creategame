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
from types import SimpleNamespace
from dataclasses import replace

from callback.engine.actor.offers import (
    in_lane,
    is_breaking_type,
    offer_probability,
    quarters_for_role,
    resolve_casting_path,
    Role,
    sample_budget_millions,
    sample_role,
    type_break_difficulty_tax,
)
from callback.engine.core.util import clamp
from callback.engine.actor.persona import GENRES
from callback.engine.actor.positions import DIAL_LABELS, DIALS, PLAYER_LABELS, POSITIONS, WITH, generosity, upstaging
from callback.engine.actor.prep import PREP_OPTIONS, WING_IT
from callback.engine.actor.rating import RATING_CUT, RATING_RELEASE_AS_SHOT, near_boundary, rating_band, rating_score
from callback.engine.actor.release import (
    FESTIVAL_ACQUISITION_BASE_MULTIPLIER,
    RELEASE_STRATEGIES,
    STREAMING_BUYOUT_MULTIPLIER,
    WIDE,
    LIMITED,
    weekly_gross_curve,
)
from callback.engine.core.script_notes import DIRECTOR_SCRIPT_NOTE_OPTIONS, SCRIPT_NOTE_OPTIONS, apply_script_note
from callback.engine.actor.standing import standing_score
from callback.engine.life.money import CUT_THE_FLOOR_AFFECTION_COST, cut_the_floor
from callback.engine.actor.studios import (
    SELF_DISTRIBUTE_MULTIPLIER,
    STUDIOS,
    decide_release_strategy,
    festival_bidders,
    streaming_bidders,
)
from callback.engine.awards.awards import (
    BREAKTHROUGH,
    BREAKTHROUGH_COMPETITOR_CRITIC_MEAN,
    BREAKTHROUGH_COMPETITOR_CRITIC_SD,
    BREAKTHROUGH_COMPETITOR_SPOTLIGHT_MEAN,
    BREAKTHROUGH_COMPETITOR_SPOTLIGHT_SD,
    DIRECTOR,
    ENSEMBLE,
    FIELD_COMPETITOR_CRITIC_MEAN,
    FIELD_COMPETITOR_CRITIC_SD,
    FIELD_COMPETITOR_SPOTLIGHT_MEAN,
    FIELD_COMPETITOR_SPOTLIGHT_SD,
    NarrativeContext,
    apply_award_ceiling,
    award_win_bonus,
    buzz_score,
    category_fraud,
    eligible_performance_categories,
    ensemble_buzz_score,
    narrative_bonus,
)
from callback.engine.director import skill
from callback.engine.leverage.approvals import (
    box_office_bonus_earned,
    BOX_OFFICE_BONUS_TYPES,
    can_negotiate_approvals,
    can_negotiate_box_office_bonus,
    fee_after_approvals,
    negotiated_bonus_share,
)
from callback.engine.leverage.catalogue import (
    accumulate_scarcity,
    advance_agent_tier,
    agent_application_boost,
    application_fatigue_tax,
    can_advance_agent_tier,
    fatigue_band,
    next_agent_tier,
)
from callback.engine.leverage.multi_picture_deal import (
    BREAK_NOTORIETY_PENALTY,
    MULTI_PICTURE_MAX_FILMS,
    MULTI_PICTURE_MIN_FILMS,
    MULTI_PICTURE_MIN_STANDING,
    deal_terms,
    fulfill_one,
    sign_deal,
)
from callback.engine.rolodex import interactions as rolodex_interactions
from callback.engine.simulation._backgrounds import BACKGROUND_TABLE, REGIONAL_STAGE_START_AGE
from callback.engine.simulation._franchises import (
    apply_exit,
    FRANCHISE_INDISPENSABILITY_HOLDOUT_THRESHOLD,
    create_spinoff_entry,
    reboot_probability,
    REBOOT_MIN_DORMANT_YEARS,
    REBOOT_REVIVAL_INDISPENSABILITY_SHARE,
    SEQUEL_ELIGIBLE_MAX_DORMANT_YEARS,
    SPINOFF_INDISPENSABILITY_THRESHOLD,
    spinoff_available as _spinoff_available,
    studio_protectiveness,
    update_franchise_after_project,
    WRITEOUT_HOLDOUT_NOTORIETY_DISCOUNT,
)
from callback.engine.leverage.indispensability import recast_cost, resolve_holdout
from callback.engine.leverage.merchandising import (
    MerchandisingDeal,
    annual_royalty_payout,
    can_negotiate_merchandising,
    negotiated_merch_share,
)
from callback.engine.director import casting as director_casting
from callback.engine.director import shoot_style as director_shoot_style
from callback.engine.director import development as director_development
from callback.engine.director.development import DEV_ACTIONS, attach_star_favour_cost, momentum_band as director_momentum_band
from callback.engine.studio.slate import sample_tier_budget_millions, TIER_BUDGETS

QUARTERS_PER_YEAR = 4  # §7.4 v16 — directing spends its one real action per quarter, not per year;
# which project gets a given quarter is the actual triage decision, split across the slate.
from callback.engine.simulation._director import (
    accept_hire_offer,
    advance_shoots_and_resolve,
    apply_dev_action_and_advance,
    can_start_new_project,
    MAX_PROJECTS,
    choose_director_casting,
    choose_director_script_note,
    choose_director_shoot_style,
    director_box_office_bonus_available as director_can_negotiate_box_office_bonus,
    director_deal_available as director_deal_still_open,
    DIRECTOR_STUDIO_TRUST,
    DirectedReleaseSnapshot,
    expansion_available,
    HireOffer,
    new_director_state,
    push_director_deal_for_backend as negotiate_director_backend_deal,
    request_director_marketing_push,
    request_director_release,
    resolve_expansion,
    roll_hire_offer,
    scrap_project,
    PLAYER_DIRECTOR_ID,
    start_development,
)
from callback.engine.world.genre_cycle import accumulate_heat
from callback.engine.world.genre_cycle import genre_demand as world_genre_demand
from callback.engine.world.guild import add_residual_stream
from callback.engine.simulation._relationships import TRUST_DEFAULT, trust_band, trust_of, update_relationship, utility_bonus_from_trust
from callback.engine.simulation._release_labels import RELEASE_LABELS
from callback.engine.simulation.bands import (
    audience_band, buzz_band, critic_band, demand_band, franchise_scale_band, performance_band,
    relationship_band, roi_band, standing_band,
)
from callback.engine.simulation.career import ProjectResult, generate_palette
from callback.engine.simulation.full_career import (
    FullState,
    accept_and_play,
    accept_and_play_season,
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

# The neutral fallback for any scene a caller didn't actually play — every dial resolved at "with"
# (the same real, valid position resolve_scene_positions requires on every dial; an empty {} pad
# used to crash with a KeyError the moment a caller under-supplied scenes rather than degrading).
_NEUTRAL_SCENE = {d: WITH for d in DIALS}

# actor.offers.gatekeeper_legibility_multiplier's own lean, read back as real flavor text instead
# of a silent probability shift — a "mid" or "low" legible actor reads the same to every gatekeeper
# (the multiplier only actually bites once you're genuinely typecast), so only "high" gets a note.
_TYPECASTING_GATEKEEPER_NOTES = {
    "studio_tentpole": "A studio tentpole — they like knowing exactly what they're getting from you.",
    "franchise_reboot": "A franchise — a known quantity is exactly what they're buying.",
    "network_tv": "Network TV — being 'the one who plays X' has never hurt here.",
    "streamer_volume": None,
    "indie_first_timer": "An indie — a known type reads as a little less interesting to them.",
    "prestige_auteur": "A prestige auteur — they want range, not a known quantity.",
}


def _typecasting_note(gatekeeper: str, legibility_band: str) -> str | None:
    if legibility_band != "high":
        return None
    return _TYPECASTING_GATEKEEPER_NOTES.get(gatekeeper)

# §4.4 v19 — the offer board's own new signals. BUZZ_NOISE_SD was 12.0 against latent_quality's
# own SD of 14 — nearly 1:1 noise-to-signal, which meant even a strict "real buzz or better" filter
# barely outperformed picking blind (verified empirically: raising the bar from "some heat" to
# "real buzz" only moved average accepted-film critic score 53.9 -> 56.1, still under the neutral
# centre). Lowered so buzz is still a real, imperfect read — never the number itself — but one
# that actually earns the name: a genuinely great project should usually read as buzzy, not
# routinely get lost in the noise the way a near-1:1 ratio guarantees.
BUZZ_NOISE_SD = 7.0
DIRECTOR_ATTACH_CHANCE = 0.35  # how often a listing already has a tracked Rolodex director on it
# rather than an unfamiliar one — high enough that a real relationship history is a genuine,
# recurring factor in offer quality, not a rare curiosity.


class Session:
    """One player's run, start to obituary. Owns all engine state; exposes none of it directly."""

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)
        self.state: FullState | None = None
        self.ambition: str = ""
        self._role: Role | None = None
        self._board: list[Role] = []
        self._board_would_offer: list[bool] = []
        # leverage.catalogue's agent-tier boost/fatigue — every application this year (every
        # listing actually rolled through offer_probability, not just generated) counts, win or
        # lose. Reset once a year, in offer_board().
        self._applications_this_year: int = 0
        self._approvals: frozenset[str] = frozenset()
        self._box_office_bonus_negotiated: bool = False
        self._box_office_bonus_type: str = "net_points"
        self._box_office_bonus_share: float = 0.0
        self._merch_negotiated: bool = False
        self._merch_share: float = 0.0
        self._prep_choice: str | None = None
        self._scenes: list[dict[str, str]] = []
        self._last_result: ProjectResult | None = None
        self._script_note = None
        self._orientation_npc_id: str | None = None
        self._orientation_effect = None
        self._requested_director_npc_id: str | None = None
        self._requested_marketing_push: bool = False
        self._palette = None
        self._requested_rating_stance: str = RATING_RELEASE_AS_SHOT
        self._director_attach_target_npc_id: str | None = None
        self._director_attach_type: str = director_development.ATTACHMENT_BANKABLE
        self._director_licensing_cost_fraction: float = 0.5  # v19/v20 — "option_adaptation"'s own
        # real, player-chosen spend against adaptation_option_cost's ceiling; see choose_adaptation_
        # licensing_fraction(). 0.5 (a mid-range option) until the player actually picks.
        self._director_adaptation_source_type: str = "novel"
        self._director_quarters_this_year: int = 0
        self._actor_quarters_this_year: int = 0
        self._last_directed_release: DirectedReleaseSnapshot | None = None
        self._pending_hire_offer: HireOffer | None = None
        # This year's calendar-advance inputs, accumulated by whatever you did this year (acting
        # and/or directing — see end_year()) and applied exactly once when the year actually ends.
        self._acting_worked_this_year: bool = False
        self._pending_billing: str | None = None
        self._pending_bonus_income: float = 0.0
        # A signed multi-picture deal or a launched spin-off guarantees one listing on the next
        # board — tracked by index so accept() knows to fulfill it rather than treat it as a
        # normal roll. Only one guaranteed slot per board (see _generate_listings).
        self._guaranteed_index: int | None = None
        self._guaranteed_source: str | None = None  # "deal" | "spinoff" | "renewed_series"
        self._pending_spinoff_franchise_id: str | None = None
        # §5.18 — a renewed season's real trap: next year's listing is guaranteed, not negotiated
        # fresh, and locked at the same Role (so the same fee) the season was originally sold at.
        self._pending_renewed_series: Role | None = None

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
        self._applications_this_year = 0
        self._guaranteed_index = None
        self._guaranteed_source = None
        listings = []
        guaranteed = self._guaranteed_listing()
        if guaranteed is not None:
            listings.append(guaranteed)
            n = max(n - 1, 0)
        listings.extend(self._generate_listings(n))
        return listings

    def generate_more_listings(self, count: int = OFFER_BOARD_GENERATE_MORE_BATCH) -> list[dict]:
        """Appends more listings to the current board rather than replacing it — the offer board
        isn't capped; there's always another audition to generate if the player wants to keep
        looking. Returns only the newly generated listings (their index continues the board's)."""
        return self._generate_listings(count)

    def _maybe_attach_director(self, role: Role) -> Role:
        """§4.4 v17 — with real, not-guaranteed odds, a listing already has a tracked Rolodex
        director on it rather than an unfamiliar one. Doesn't invent new NPC-director modeling —
        the "info" a player gets on a known director is exactly the same relationship/trust data
        director_relationship_status() already tracks; an unfamiliar one stays genuinely unknown."""
        directors = [n for n in self.state.rolodex.tracked() if n.npc_type == "director"]
        if not directors or self.rng.random() >= DIRECTOR_ATTACH_CHANCE:
            return role
        pick = self.rng.choice(directors)
        return replace(role, director_npc_id=pick.npc_id)

    def _director_tag(self, role: Role) -> dict:
        if role.director_npc_id is None:
            return {"id": None, "known": False, "relationship": None}
        npc = self.state.rolodex.npcs.get(role.director_npc_id)
        return {
            "id": role.director_npc_id, "known": True,
            "relationship": relationship_band(npc.relationship_state) if npc is not None else None,
        }

    def _listing_extra_fields(self, role: Role) -> dict:
        """The fields shared by both _generate_listings and _guaranteed_listing — every real
        signal now available before a player has to decide, all bands, never a raw number."""
        persona = self.state.actor.persona
        return {
            "secondary_genre": role.secondary_genre,  # design/part-09 §9.2 — None for a normal
            # single-genre listing; set, this is a hybrid ("sci-fi horror") and the player should
            # see both genre tags together, not just the primary one.
            "demand_band": demand_band(world_genre_demand(self.state.genre_heat, role.genre)),
            "buzz_band": buzz_band(clamp(role.latent_quality + self.rng.gauss(0.0, BUZZ_NOISE_SD), 0.0, 100.0)),
            "source_material_popularity": role.source_material_popularity,
            "franchise_scale": franchise_scale_band(role.installment_number),
            "director": self._director_tag(role),
            "project_type": role.project_type,
            "n_episodes": role.n_episodes,
            "series_renewable": role.series_renewable,
            "is_animation": role.is_animation,
            # Typecasting, made legible instead of a hidden number moving the odds underneath —
            # actor.persona/actor.offers's own real mechanics, surfaced so the player can read why
            # one listing is easier or harder than another before deciding.
            "in_your_lane": in_lane(persona, role),
            "breaking_type": is_breaking_type(persona, role),
            "typecasting_note": _typecasting_note(role.gatekeeper, persona.legibility_band()),
            # actor.offers.quarters_for_role — how much of the year this listing actually costs,
            # visible before accepting rather than discovered after. A player choosing between a
            # quick animation gig and a slow tentpole shoot needs to see that trade up front.
            "quarters_required": quarters_for_role(role),
        }

    def director_info(self, npc_id: str) -> dict:
        """§4.4 v17 — the "click on a director" action: real relationship/trust/track-record data
        for someone you've actually worked with or tracked before. Nothing invented for a stranger
        — the same honest uncertainty every other unfamiliar NPC in this design carries."""
        npc = self.state.rolodex.npcs.get(npc_id)
        if npc is None:
            return {"known": False}
        rel = self.state.director_relations.get(npc_id)
        return {
            "known": True, "id": npc_id, "relationship": relationship_band(npc.relationship_state),
            "projects_together": rel.projects_together if rel is not None else 0,
            "trust_band": trust_band(rel.trust) if rel is not None else "no history yet",
            "net_profit_millions": round(rel.net_profit_millions, 1) if rel is not None else 0.0,
        }

    def _guaranteed_listing(self) -> dict | None:
        """A signed multi-picture deal or a launched spin-off owes you a real, always-available
        listing this year — not a roll of the dice like everything else on the board. Only one
        guaranteed slot per board: a deal and a spin-off never compete for it in the same year,
        the deal takes priority since it's the actor's standing commitment of the two."""
        deal = self.state.multi_picture_deal
        if deal is not None and deal.films_remaining > 0:
            # The deal's guaranteed_budget_millions is a fee floor (built off quote_value), not a
            # film budget — sample a real film budget plausible for this studio's own range so
            # reception/marketing/ROI still resolve against a sane production budget, distinct
            # from the fixed fee the deal actually guarantees.
            deal_studio = STUDIOS[deal.studio_id]
            film_budget = clamp(sample_budget_millions(self.rng), *deal_studio.budget_range)
            role = replace(
                sample_role(self.rng), studio=deal.studio_id,
                budget_for_role=deal.guaranteed_budget_millions, film_budget_millions=film_budget,
            )
            source = "deal"
        elif self._pending_renewed_series is not None:
            # Locked at the original Role, unchanged — the whole point of the trap: no fresh
            # negotiation, same fee, same terms, unless the player calls a holdout on it.
            role = self._pending_renewed_series
            source = "renewed_series"
        elif self._pending_spinoff_franchise_id is not None:
            f = self.state.franchises.get(self._pending_spinoff_franchise_id)
            if f is None:
                # A signed multi-picture deal can take the guaranteed slot the same year a spin-off
                # was launched, leaving the spin-off's own listing un-fulfilled that year — untouched,
                # it's exactly what decay_dormant_franchises() prunes at year's end. The pointer here
                # would otherwise dangle into a KeyError next time the board is built; treat a pruned
                # spin-off the same as one that was never launched rather than crashing on it.
                self._pending_spinoff_franchise_id = None
                return None
            role = replace(
                sample_role(self.rng), studio=f.studio_id, genre=f.genre,
                franchise_id=self._pending_spinoff_franchise_id, installment_number=1,
            )
            source = "spinoff"
        else:
            return None

        role = self._maybe_attach_director(role)
        index = len(self._board)
        self._board.append(role)
        self._board_would_offer.append(True)
        self._guaranteed_index = index
        self._guaranteed_source = source
        studio = STUDIOS[role.studio]
        return {
            "index": index,
            "genre": role.genre,
            "billing": role.billing,
            "budget_millions": round(role.film_budget_millions, 2),
            "fee_millions": round(role.budget_for_role, 2),
            "available": True,
            "union": role.union,
            "studio_name": studio.name,
            "studio_tagline": studio.tagline,
            "franchise_id": role.franchise_id,
            "installment_number": role.installment_number,
            "source_material": role.source_material,
            **self._listing_extra_fields(role),
            "guaranteed": True,
        }

    def _generate_listings(self, count: int) -> list[dict]:
        listings = []
        for _ in range(count):
            role = offer_this_year(self.state, self.rng)
            role = self._maybe_attach_director(role)
            # A studio that's made money with you before wants you back; one you burned is
            # warier — a real memory, not just flavor text on the tagline.
            utility = utility_for(self.state, role) + utility_bonus_from_trust(self.state.studio_relations, role.studio)
            path = resolve_casting_path(utility, role)
            agent_tier = self.state.leverage.agent_tier
            # type_break_difficulty_tax — the one added friction a genuine type-break carries,
            # separate from (not stacked on top of a second economic penalty against) the Fit
            # penalty already inside utility. See actor.offers's own docstring. The board itself
            # stays unlimited to scan and apply to — what actually gates volume is leverage.
            # catalogue's own agent boost (real representation, felt on every single application)
            # against its own fatigue tax (repeated asking within the same year gets harder, at a
            # rate that depends entirely on who's making the calls).
            difficulty = (
                role.difficulty + type_break_difficulty_tax(self.state.actor.persona, role)
                - agent_application_boost(agent_tier, self.rng)
                + application_fatigue_tax(agent_tier, self._applications_this_year, self.rng)
            )
            would_offer = path == "direct_offer" or self.rng.random() < offer_probability(utility, difficulty)
            self._applications_this_year += 1
            index = len(self._board)
            self._board.append(role)
            self._board_would_offer.append(would_offer)
            studio = STUDIOS[role.studio]
            listings.append({
                "index": index,
                "genre": role.genre,
                "billing": role.billing,
                "budget_millions": round(role.film_budget_millions, 2),
                "fee_millions": round(role.budget_for_role, 2),
                "available": would_offer,
                "union": role.union,
                "studio_name": studio.name,
                "studio_tagline": studio.tagline,
                "franchise_id": role.franchise_id,
                "installment_number": role.installment_number,
                "source_material": role.source_material,
                **self._listing_extra_fields(role),
                "guaranteed": False,
            })
        return listings

    def actor_quarters_remaining_this_year(self) -> int:
        """§4/§6 v16 — the same real cadence directing now runs on (QUARTERS_PER_YEAR), applied to
        everything an actor does *between* roles: Rolodex check-ins, working Leverage, going quiet
        on purpose. Accepting a role consumes actor.offers.quarters_for_role(role) quarters, not
        automatically the whole year — a real production ties up as much of your calendar as its
        own real scale actually costs, and whatever's left over is the real budget for how you
        spend your own attention instead of an unlimited free menu."""
        return max(0, QUARTERS_PER_YEAR - self._actor_quarters_this_year)

    def accept(self, index: int) -> None:
        if not (0 <= index < len(self._board)):
            raise ValueError("no such listing on this year's offer_board()")
        if not self._board_would_offer[index]:
            raise ValueError("this offer never came through — check offer_board()[index]['available'] first")
        self._role = self._board[index]
        # actor.offers.quarters_for_role — a role's own real scale (animation, budget, episode
        # count) decides how much of the year it actually costs, not a flat "the whole year" every
        # time. Whatever's left over is real: actor_quarters_remaining_this_year() already gates
        # Rolodex check-ins, agent-tier pushes, and disappearing — a quick animation gig now
        # genuinely leaves room to also work those, in the same year as a real acting credit.
        self._actor_quarters_this_year = quarters_for_role(self._role)
        # Generated once, here — the film's palette (and so its §5.19 RatingScore) is fixed the
        # moment casting happens, untouched by prep/the shoot/script notes, so a rating preview is
        # knowable and stable for the whole project rather than a surprise sprung at release time.
        self._palette = generate_palette(self._role.genre, self.rng)
        self._requested_rating_stance = RATING_RELEASE_AS_SHOT
        if index == self._guaranteed_index:
            if self._guaranteed_source == "deal":
                self.state = replace(self.state, multi_picture_deal=fulfill_one(self.state.multi_picture_deal))
            elif self._guaranteed_source == "spinoff":
                self._pending_spinoff_franchise_id = None
            elif self._guaranteed_source == "renewed_series":
                self._pending_renewed_series = None
            self._guaranteed_index = None
            self._guaranteed_source = None
        # everything else on the board quietly resolves through the background industry (§10.0),
        # same as a single declined offer always has — you only ever work one project a year.
        for i, role in enumerate(self._board):
            if i != index:
                self.state = decline_and_resolve(self.state, role, self.rng)
        self._script_note = None
        self._orientation_npc_id = None
        self._orientation_effect = None
        self._requested_director_npc_id = None
        self._requested_marketing_push = False
        self._box_office_bonus_negotiated = False
        self._box_office_bonus_type = "net_points"
        self._box_office_bonus_share = 0.0

    def request_marketing_push(self) -> None:
        """Lobby the studio for a bigger campaign — real input, not a guarantee: the studio honors
        it with the same steeply fame-gated influence curve as a release-strategy request (studios.
        actor_influence_on_studio_decision). Callable any time between accept() and choose_release()."""
        self._requested_marketing_push = True

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
                "you_are_current_lead": f.you_are_current_lead,
                "exit_type": f.exit_type,  # "recast", "written_out", or None while still active
                "exit_year": f.exit_year,
                # Only meaningful once you've left — a real, live "how's it doing without me" read:
                # the audience score frozen the moment you left vs. wherever it's drifted to since,
                # off-screen (simulation._franchises.advance_franchises_without_you).
                "audience_score_at_exit": (
                    round(f.audience_score_at_exit, 1) if f.audience_score_at_exit is not None else None
                ),
                "audience_score_now": round(f.prior_audience_score, 1) if not f.you_are_current_lead else None,
            }
            for f in self.state.franchises.values()
        ]

    def directing_franchise_options(self) -> list[dict]:
        """v27 — directors now pitch sequels off the SAME shared franchises pool the actor track
        already uses (design/part-09's own sequel-value curve), not a second system. Same
        eligibility bar maybe_attach_franchise already applies to the acting side: not dormant too
        long, and still led by whoever's currently attached (a franchise you were recast/written
        out of as an actor is still visible here if a director never held it in the first place —
        franchises don't distinguish who's "in" them by role type, only by continuity)."""
        current_year = self.age()
        return [
            {
                "id": f.franchise_id, "genre": f.genre, "installment_number": f.installments_starred + 1,
                "prior_audience_score": round(f.prior_audience_score, 1),
                "years_since_last": current_year - f.last_installment_year,
                "you_directed_the_last_one": f.last_director_npc_id == PLAYER_DIRECTOR_ID,
            }
            for f in self.state.franchises.values()
            if current_year - f.last_installment_year <= SEQUEL_ELIGIBLE_MAX_DORMANT_YEARS
        ]

    # ---- directing: reboots (compartmentalized from directing_franchise_options' ordinary
    # sequel pitch above — a retired property, not an active one) --------------------------------

    def directing_reboot_options(self) -> list[dict]:
        """Retired franchises (simulation.full_career's own retired_franchises archive —
        decay_dormant_franchises' one-way "fades to nothing" arc) real enough to pitch a comeback
        for. Same REBOOT_MIN_DORMANT_YEARS floor the background yearly roll (resolve_reboots)
        already uses — nothing that only just ended is eligible."""
        current_year = self.age()
        return [
            {
                "franchise_id": fid, "genre": f.genre,
                "years_dormant": current_year - (f.retired_year if f.retired_year is not None else current_year),
                "peak_indispensability": round(f.peak_indispensability, 1),
            }
            for fid, f in self.state.retired_franchises.items()
            if current_year - (f.retired_year if f.retired_year is not None else current_year) >= REBOOT_MIN_DORMANT_YEARS
        ]

    def pitch_reboot(self, franchise_id: str) -> bool:
        """A real ask, not a guarantee — rolls the SAME reboot_probability the background yearly
        check already uses (years dormant + the property's own peak_indispensability), just fired
        on demand instead of silently once a year. On success, revives it with the same partial-
        value shape resolve_reboots' own background revival already uses (never full peak value —
        a real, partial second life) and it's immediately pitchable via start_directing_project
        (franchise_id=...). Returns whether the studio actually said yes."""
        f = self.state.retired_franchises.get(franchise_id)
        if f is None:
            return False
        current_year = self.age()
        years_dormant = current_year - (f.retired_year if f.retired_year is not None else current_year)
        if self.rng.random() >= reboot_probability(years_dormant, f.peak_indispensability):
            return False
        revived = replace(
            f, indispensability=f.peak_indispensability * REBOOT_REVIVAL_INDISPENSABILITY_SHARE,
            last_installment_year=current_year, retired_year=None, you_are_current_lead=True,
            exit_type=None, exit_year=None, audience_score_at_exit=None,
        )
        self.state = replace(
            self.state,
            franchises={**self.state.franchises, franchise_id: revived},
            retired_franchises={k: v for k, v in self.state.retired_franchises.items() if k != franchise_id},
        )
        return True

    # ---- directing: spin-offs (compartmentalized from the actor track's own spinoff_options/
    # launch_spinoff above — a director's own pitch, not gated on who's still playing the lead) ---

    def directing_spinoff_options(self) -> list[dict]:
        """Same SPINOFF_INDISPENSABILITY_THRESHOLD bar the actor path's spinoff_available() uses,
        deliberately WITHOUT that path's you_are_current_lead gate — spinning off a popular side
        element is the director's own creative pitch, not contingent on whether the original
        actor still holds the lead role."""
        return [
            {"franchise_id": fid, "genre": f.genre, "indispensability": round(f.indispensability, 1)}
            for fid, f in self.state.franchises.items() if f.indispensability >= SPINOFF_INDISPENSABILITY_THRESHOLD
        ]

    def launch_directing_spinoff(self, franchise_id: str) -> str | None:
        """Creates the new franchise immediately (seeded off the parent's own indispensability —
        simulation._franchises.create_spinoff_entry, the same real head-start the actor path's own
        launch_spinoff already gives) and returns its id — pitch it directly with
        start_directing_project(franchise_id=...), no separate guaranteed-offer step needed the
        way the actor path requires (a director pitches, they aren't cast)."""
        parent = self.state.franchises.get(franchise_id)
        if parent is None or parent.indispensability < SPINOFF_INDISPENSABILITY_THRESHOLD:
            return None
        new_id = f"fr_dspinoff_{self.rng.randrange(10**6):06d}"
        entry = create_spinoff_entry(parent, new_id, current_year=self.age())
        self.state = replace(self.state, franchises={**self.state.franchises, new_id: entry})
        return new_id

    def merchandising_status(self) -> list[dict]:
        """Every active merchandising royalty stream (leverage/merchandising.py) and what it's
        actually paying this year — reads the franchise's own current indispensability fresh, so
        a fading property's own number here fades right along with it, and a reboot's own spike
        shows up here automatically, with no special-casing needed."""
        result = []
        for deal in self.state.merchandising_deals:
            f = self.state.franchises.get(deal.franchise_id)
            indispensability_now = f.indispensability if f is not None else 0.0
            result.append({
                "franchise_id": deal.franchise_id,
                "royalty_share_pct": round(deal.royalty_share * 100, 2),
                "signed_year": deal.signed_year,
                "still_active": f is not None,
                "this_years_payout_millions": round(annual_royalty_payout(deal.royalty_share, indispensability_now), 3),
            })
        return result

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
        outcome = resolve_holdout(f.indispensability, f.prior_holdouts, self.rng, studio_protectiveness(f))

        franchises = dict(self.state.franchises)
        franchises[f.franchise_id] = replace(f, prior_holdouts=f.prior_holdouts + 1)

        proceeds = True
        merchandising_deals = self.state.merchandising_deals
        if outcome.they_paid:
            self._role = replace(self._role, budget_for_role=self._role.budget_for_role * outcome.raise_multiplier)
        elif outcome.recast:
            proceeds = False
            # The franchise doesn't end here — it continues without you (simulation._franchises.
            # apply_exit/advance_franchises_without_you), the same "the studio owns the property"
            # logic a declined sequel resolves through too. apply_exit itself rolls which of the two
            # real outcomes this becomes (recast vs written out) off the character's own identity —
            # this branch just knows the part isn't yours anymore, not which shape that takes. Any
            # royalty stream tied to it ends here either way — a merchandising deal was negotiated
            # off your own likeness/portrayal, not the character in the abstract.
            exited = apply_exit(f, self.age(), self.rng)
            franchises[f.franchise_id] = exited
            merchandising_deals = tuple(d for d in merchandising_deals if d.franchise_id != f.franchise_id)
            standing = self.state.actor.standing.copy()
            # resolve_holdout's own notoriety_delta reads as "the failed negotiation became public"
            # — real regardless of outcome, but a quiet write-out generates far less of a stir than
            # a visible recast, so it's discounted rather than dropped.
            notoriety_delta = (
                outcome.notoriety_delta if exited.exit_type == "recast"
                else outcome.notoriety_delta * WRITEOUT_HOLDOUT_NOTORIETY_DISCOUNT
            )
            standing.add("notoriety", notoriety_delta)
            self.state = replace(self.state, actor=replace(self.state.actor, standing=standing))

        self.state = replace(self.state, franchises=franchises, merchandising_deals=merchandising_deals)
        if not proceeds:
            self._role = None  # no project this year — the year still advances via end_year()

        return {
            "paid": outcome.they_paid,
            "recast": outcome.recast,
            "raise_multiplier": round(outcome.raise_multiplier, 2),
            "proceeds": proceeds,
        }

    # ---- spin-offs — a franchise character indispensable enough earns its own new property ----

    def spinoff_options(self) -> list[dict]:
        """Franchises real enough to spin off — indispensability alone gates it (see genre.
        franchise/leverage.indispensability): a character the audience can't imagine the franchise
        without is exactly the one a studio will bankroll a new property around."""
        return [
            {
                "franchise_id": fid,
                "genre": f.genre,
                "studio_name": STUDIOS[f.studio_id].name,
                "indispensability": round(f.indispensability, 1),
            }
            for fid, f in self.state.franchises.items() if _spinoff_available(f)
        ]

    def launch_spinoff(self, franchise_id: str) -> str:
        """Creates the new franchise immediately (seeded with a real head-start audience bonus off
        the parent's own indispensability — see simulation._franchises.create_spinoff_entry) and
        guarantees its first installment shows up on next year's offer_board()."""
        parent = self.state.franchises[franchise_id]
        new_id = f"fr_spinoff_{self.rng.randrange(10**6):06d}"
        entry = create_spinoff_entry(parent, new_id, current_year=self.age())
        self.state = replace(self.state, franchises={**self.state.franchises, new_id: entry})
        self._pending_spinoff_franchise_id = new_id
        return f"You pitch a spin-off out of {parent.genre} — {STUDIOS[parent.studio_id].name} bites."

    # ---- multi-picture deals — future terms, not just this project's --------------------------

    def multi_picture_deal_available(self) -> bool:
        """Only offerable right after accepting a role — the deal is with that role's own
        financing studio — and only once, not stacked on top of an already-signed deal."""
        if self._role is None or self.state.multi_picture_deal is not None:
            return False
        return standing_score(self.state.actor.standing) >= MULTI_PICTURE_MIN_STANDING

    def multi_picture_deal_terms(self, film_count: int) -> dict:
        """A preview, not a commitment — call sign_multi_picture_deal() to actually take it."""
        film_count = max(MULTI_PICTURE_MIN_FILMS, min(film_count, MULTI_PICTURE_MAX_FILMS))
        quote_value = self.state.actor.quote_value()
        per_film, total = deal_terms(quote_value, film_count)
        return {
            "studio_name": STUDIOS[self._role.studio].name,
            "films": film_count,
            "per_film_budget_millions": round(per_film, 2),
            "total_value_millions": round(total, 2),
        }

    def sign_multi_picture_deal(self, film_count: int) -> dict:
        """Locks in a guaranteed floor budget across film_count future films with this role's own
        studio — trading the freedom to negotiate project-by-project for real security. Each film
        appears as a guaranteed listing on a future offer_board() until the deal is worked off (see
        _guaranteed_listing()); walking away early costs real notoriety (break_multi_picture_deal
        ())."""
        film_count = max(MULTI_PICTURE_MIN_FILMS, min(film_count, MULTI_PICTURE_MAX_FILMS))
        quote_value = self.state.actor.quote_value()
        deal = sign_deal(self._role.studio, quote_value, film_count, current_year=self.age())
        self.state = replace(self.state, multi_picture_deal=deal)
        return {
            "studio_name": STUDIOS[deal.studio_id].name,
            "films": deal.films_remaining,
            "per_film_budget_millions": round(deal.guaranteed_budget_millions, 2),
        }

    def multi_picture_deal_status(self) -> dict | None:
        deal = self.state.multi_picture_deal
        if deal is None:
            return None
        return {
            "studio_name": STUDIOS[deal.studio_id].name,
            "films_remaining": deal.films_remaining,
            "guaranteed_budget_millions": round(deal.guaranteed_budget_millions, 2),
        }

    def break_multi_picture_deal(self) -> str:
        """A real exit, not a free one — the studio remembers, the same asymmetric-trust read
        simulation._relationships.py already applies elsewhere."""
        deal = self.state.multi_picture_deal
        if deal is None:
            return "No deal to break."
        standing = self.state.actor.standing.copy()
        standing.add("notoriety", BREAK_NOTORIETY_PENALTY)
        self.state = replace(self.state, multi_picture_deal=None, actor=replace(self.state.actor, standing=standing))
        return f"You walk away from {STUDIOS[deal.studio_id].name}'s deal early — word gets around."

    # ---- the deal -----------------------------------------------------------------------------

    def approvals_available(self) -> bool:
        sc = self.state.actor.standing.weighted_score(STANDING_WEIGHTS)
        return can_negotiate_approvals(sc)

    def box_office_bonus_available(self, bonus_type: str = "net_points") -> bool:
        """§6.5 v21 — two real deal shapes, two real bars. "net_points" (the default — nothing
        pays out until the studio's recouped its own break-even, then a real share of the actual
        profit) needs the same Standing this always asked for; "first_dollar_gross" (paid on raw
        gross from dollar one, whether the film ever turns a profit or not — real risk the studio
        eats) is the rarer ask and needs a real Standing far above it."""
        sc = self.state.actor.standing.weighted_score(STANDING_WEIGHTS)
        return can_negotiate_box_office_bonus(sc, bonus_type)

    @staticmethod
    def box_office_bonus_type_options() -> list[tuple[str, str]]:
        return [
            ("net_points", "Net points — a real share of actual profit, but only once the studio's been made whole"),
            ("first_dollar_gross", "First-dollar gross — paid from dollar one regardless of profit, a rarer ask"),
        ]

    def merchandising_available(self) -> bool:
        """leverage/merchandising.py — only ever on the table for an animated franchise role
        (real toy-shelf merchandising, not live action's own rarer licensing shape) with the
        Standing to ask for a real cut of it."""
        if self._role is None or not self._role.is_animation or not self._role.franchise_id:
            return False
        sc = self.state.actor.standing.weighted_score(STANDING_WEIGHTS)
        return can_negotiate_merchandising(sc)

    def choose_deal(
        self, want_approvals: bool, want_box_office_bonus: bool = False, bonus_type: str = "net_points",
        want_merchandising: bool = False,
    ) -> float | None:
        bonus_type = bonus_type if bonus_type in BOX_OFFICE_BONUS_TYPES else "net_points"
        # A box-office bonus is a first-dollar-gross/net-points deal against theatrical/streaming
        # receipts — neither exists for a season (see _choose_release_series's own docstring), so
        # it's never actually on the table here regardless of Standing.
        self._box_office_bonus_negotiated = want_box_office_bonus and not self.is_series() and self.box_office_bonus_available(bonus_type)
        self._box_office_bonus_type = bonus_type
        if self._box_office_bonus_negotiated:
            # The real percentage is negotiated once, right now — never re-rolled at payout time.
            # Two separate axes: box_office_bonus_available() already gated whether this deal
            # shape is on the table at all; this is what share you actually land within it.
            leverage = standing_score(self.state.actor.standing) / 100.0
            self._box_office_bonus_share = negotiated_bonus_share(bonus_type, leverage, self.rng)
        else:
            self._box_office_bonus_share = 0.0

        self._merch_negotiated = want_merchandising and self.merchandising_available()
        if self._merch_negotiated:
            leverage = standing_score(self.state.actor.standing) / 100.0
            existing = self.state.franchises.get(self._role.franchise_id)
            protectiveness = studio_protectiveness(existing) if existing is not None else 0.0
            self._merch_share = negotiated_merch_share(leverage, protectiveness, self.rng)
        else:
            self._merch_share = 0.0

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

    # ---- the rating (§5.19) — read off the palette the moment it's generated in accept() -----

    def rating_preview(self) -> dict:
        """The film's own RatingScore/band, fixed since accept() and untouched by anything you do
        between now and release — callable any time mid-project, not just at Post & Release."""
        score = rating_score(self._palette.intensity, self._role.genre)
        return {"band": rating_band(score), "cut_available": near_boundary(score)}

    def rating_cut_available(self) -> bool:
        return self.rating_preview()["cut_available"]

    @staticmethod
    def rating_cut_options() -> list[tuple[str, str]]:
        return [
            (RATING_CUT, "Cut for the friendlier rating — the compromise shows on screen"),
            (RATING_RELEASE_AS_SHOT, "Release as shot — the harder rating, the film you made"),
        ]

    def choose_rating_stance(self, key: str) -> None:
        self._requested_rating_stance = key if key in (RATING_CUT, RATING_RELEASE_AS_SHOT) else RATING_RELEASE_AS_SHOT

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

    def is_series(self) -> bool:
        return self._role is not None and self._role.project_type == "series"

    def episode_labels(self) -> list[str]:
        """§5.18 — how many real, played passes through scene_names() this project needs: one for
        a film, two (premiere, finale) for a series — everything between is a discounted echo,
        never a played scene at all. A film's own single implicit pass has no label of its own."""
        return ["premiere", "finale"] if self.is_series() else [""]

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
        """A rough, budget-only preview of who could plausibly buy streaming rights — before the
        film is actually made, nobody's seen it yet, so this can't reflect quality. Deterministic
        (no rng): a stable menu to compare, not a fresh roll each look. The real offers, shaped by
        the finished film's actual quality (fewer or worse bidders for a bad film, each buyer's own
        noisy read on it), are resolved inside choose_release("streaming") itself — see
        _streaming_bid_summary below. Always includes the financing studio's own SELF_DISTRIBUTE_
        MULTIPLIER option: they just put it up on their own service for nothing — you get your
        budget back, no more."""
        budget = self._role.film_budget_millions
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

    def festival_bid_options(self) -> list[dict]:
        """A rough, budget-only preview of who could plausibly buy festival distribution rights —
        before the film has even premiered, nobody's seen it yet (§10.3's own "all reviews land at
        once" reveal), so this can't reflect quality or whether the film gets acquired at all.
        Deterministic (no rng), same shape as streaming_bid_options(). The real offers — fewer or
        worse bidders for a weak premiere, and the financing studio's own real self-release numbers
        in place of a flat guarantee — are resolved inside choose_release("festival") itself, and
        only reached at all if the submission clears festival_acquisition_probability's own gate;
        an unsold submission never gets this far."""
        budget = self._role.film_budget_millions
        bidders = festival_bidders(budget, self._role.studio)
        return [
            {
                "studio_id": s.id, "studio_name": s.name,
                "multiplier": round(FESTIVAL_ACQUISITION_BASE_MULTIPLIER + s.festival_acquisition_multiplier_delta, 2),
                "payout_millions": round(budget * (FESTIVAL_ACQUISITION_BASE_MULTIPLIER + s.festival_acquisition_multiplier_delta), 2),
            }
            for s in bidders
        ]

    def choose_release(
        self, strategy: str, streaming_multiplier: float | None = None, streaming_bid_selector=None,
        festival_bid_selector=None,
    ) -> dict:
        """Resolves the whole project — the one point everything collected since offer_board()
        actually gets spent. Does not advance the year itself (see end_year()) — you might also
        work on directing this same year; acting and directing no longer compete for the same
        calendar slot.

        strategy is your *request*, not the final word — the studio decides (studios.
        decide_release_strategy()). How often you actually get your way scales with how much this
        studio trusts you (studio_relations) and how big a star you currently are (Standing's own
        standing_score); otherwise it releases the film its own way (Studio.preferred_release).
        The resolved summary reports both what you asked for and what actually happened.

        streaming_multiplier: only meaningful when the studio's actual decision is "streaming" — a
        specific, already-known buyer's terms (e.g. the financing studio's own SELF_DISTRIBUTE_
        MULTIPLIER option from streaming_bid_options()), skipping the real quality-aware bid pool.
        streaming_bid_selector: only meaningful when the studio's actual decision is "streaming"
        and no streaming_multiplier is given. Called with the real bid pool (list[actor.studios.
        StreamingBid]) once the finished film's quality is actually known — an awful, no-wide-
        release film can draw a thin or empty outside pool, since each buyer's read on it varies.
        Must return the chosen StreamingBid. Defaults to auto-accepting the best offer when no
        selector is given.
        festival_bid_selector: only meaningful when the studio's actual decision is "festival" and
        the submission actually clears festival_acquisition_probability's own gate — an unsold
        submission never reaches it at all. Called with the real bid pool (list[actor.studios.
        FestivalBid] — competing distributors' flat guarantees, plus one self_release=True entry
        for keeping the film and releasing it yourselves at the real LIMITED-release numbers rather
        than a flat guarantee). Must return the chosen FestivalBid. Defaults to auto-accepting the
        best payout when no selector is given, same as streaming."""
        if self.is_series():
            return self._choose_release_series()
        scenes = tuple(self._scenes) if len(self._scenes) == 3 else (self._scenes + [_NEUTRAL_SCENE] * 3)[:3]
        franchise_installment = self._role.installment_number

        studio = STUDIOS[self._role.studio]
        trust = trust_of(self.state.studio_relations, self._role.studio)
        importance = standing_score(self.state.actor.standing)
        actual_strategy = decide_release_strategy(studio, strategy, trust, importance, self.rng)
        overruled = actual_strategy != strategy

        chosen_bid = {}
        chosen_festival_bid = {}

        def _capture(bids):
            nonlocal chosen_bid
            picked = streaming_bid_selector(bids) if streaming_bid_selector is not None else max(
                bids, key=lambda b: b.payout_millions,
            )
            chosen_bid = {"studio_name": picked.studio_name, "self_distribute": picked.self_distribute}
            return picked

        def _capture_festival(bids):
            nonlocal chosen_festival_bid
            picked = festival_bid_selector(bids) if festival_bid_selector is not None else max(
                bids, key=lambda b: b.payout_millions,
            )
            chosen_festival_bid = {"studio_name": picked.studio_name, "self_release": picked.self_release}
            return picked

        self.state, result = accept_and_play(
            self.state, self._role, self._prep_choice or "table_work", scenes, self.rng,
            release_strategy=actual_strategy,
            script_note=self._script_note,
            orientation_npc_id=self._orientation_npc_id,
            orientation_effect=self._orientation_effect,
            # §4.4 v17 — if the listing already had a known director attached (role.director_npc_id,
            # visible on the offer before accepting) and the player never explicitly pulled a
            # different one via request_director(), that already-attached director is who actually
            # directs — the info shown pre-accept is real, not decorative.
            requested_director_npc_id=self._requested_director_npc_id or self._role.director_npc_id,
            streaming_multiplier_override=streaming_multiplier if actual_strategy == "streaming" else None,
            streaming_bid_selector=_capture if actual_strategy == "streaming" and streaming_multiplier is None else None,
            festival_bid_selector=_capture_festival if actual_strategy == "festival" else None,
            studio_trust=trust, requested_marketing_push=self._requested_marketing_push,
            palette=self._palette, requested_rating_stance=self._requested_rating_stance,
        )
        bonus = (
            box_office_bonus_earned(result.gross, result.break_even, self._box_office_bonus_share, self._box_office_bonus_type)
            if self._box_office_bonus_negotiated else 0.0
        )
        if self._merch_negotiated:
            deal = MerchandisingDeal(franchise_id=self._role.franchise_id, royalty_share=self._merch_share, signed_year=self.age())
            self.state = replace(self.state, merchandising_deals=(*self.state.merchandising_deals, deal))
        self._acting_worked_this_year = True
        self._pending_billing = self._role.billing
        self._pending_bonus_income = bonus
        self._last_result = result
        self._scenes = []

        return {
            "requested_release": RELEASE_LABELS[strategy],
            "studio_overruled": overruled,
            "streaming_buyer": chosen_bid.get("studio_name"),
            "streaming_self_distributed": chosen_bid.get("self_distribute", False),
            "festival_buyer": chosen_festival_bid.get("studio_name"),
            "festival_self_released": chosen_festival_bid.get("self_release", False),
            "marketing_push_requested": result.marketing_push_requested,
            "marketing_push_honored": result.marketing_push_honored,
            "rating_band": result.rating_band,
            "rating_stance": result.rating_stance_applied,
            "rating_cut_forced": result.rating_cut_forced,
            "rating_studio_pressure": result.rating_studio_pressure,
            "performance_band": performance_band(result.performance),
            "critic_band": critic_band(result.film_critic_score),
            "critic_score": round(result.film_critic_score),
            "audience_band": audience_band(result.audience_score),
            "release_label": RELEASE_LABELS[actual_strategy],
            "studio_name": STUDIOS[result.studio_id].name,
            "roi_band": roi_band(result.roi),
            "gross_millions": round(result.gross, 1),
            "budget_millions": round(result.budget, 1),
            "marketing_millions": round(result.marketing, 1),
            "roi": round(result.roi, 2),
            "weekly_gross": self._weekly_gross(result, actual_strategy),
            "franchise_installment": franchise_installment,
            "box_office_bonus_millions": round(bonus, 2),
            "box_office_bonus_type": self._box_office_bonus_type if self._box_office_bonus_negotiated else None,
            "box_office_bonus_share_pct": round(self._box_office_bonus_share * 100, 2) if self._box_office_bonus_negotiated else None,
            "merchandising_negotiated": self._merch_negotiated,
            "merchandising_share_pct": round(self._merch_share * 100, 2) if self._merch_negotiated else None,
            "director_note_choice": result.director_note_choice,
        }

    def _choose_release_series(self) -> dict:
        """§5.18 — the season-shaped counterpart to choose_release's film path. Expects 6 real
        scenes collected via play_scene() (3 for the premiere, 3 for the finale — see
        episode_labels()); short of that, pads with the neutral default position the same way the
        film path tolerates fewer than 3 (a caller that isn't series-aware still gets a sane,
        if lesser, finale rather than an error).

        No release-strategy question and no box-office bonus here, deliberately: unlike a film, a
        season isn't sold to theaters or shopped for streaming rights after the fact — role.studio
        (already fixed at offer time — a streamer vs. a network deal) already IS the distribution,
        and "box office bonus" (leverage.approvals) is a first-dollar-gross/net-points deal against
        theatrical/streaming receipts, neither of which exists for a season. The real money is
        series.aggregate_season's own license_value, reported below.

        Renewal (role.series_renewable only) is rolled here, once, off the season's own real
        retention/audience numbers (actor.series.renewal_probability) — a renewed season's next
        listing is guaranteed and locked at this exact Role next year (see _guaranteed_listing's
        own "renewed_series" branch), the real trap §9.6 already names for a franchise, not a
        fresh negotiation. Deliberately out of scope this pass: routing a renewed show through the
        Franchise/Indispensability holdout system so a player can fight the quote lock — a real,
        bounded follow-up, not attempted here."""
        scenes = (self._scenes + [_NEUTRAL_SCENE] * 6)[:6]
        premiere_scenes = tuple(scenes[0:3])
        finale_scenes = tuple(scenes[3:6])
        studio = STUDIOS[self._role.studio]
        trust = trust_of(self.state.studio_relations, self._role.studio)

        self.state, result, renewal_chance, retention_summary = accept_and_play_season(
            self.state, self._role, self._prep_choice or "table_work", premiere_scenes, finale_scenes, self.rng,
            orientation_npc_id=self._orientation_npc_id, orientation_effect=self._orientation_effect,
            studio_trust=trust, requested_marketing_push=self._requested_marketing_push,
            requested_rating_stance=self._requested_rating_stance,
        )

        renewed = None
        if renewal_chance is not None:
            renewed = self.rng.random() < renewal_chance
            if renewed:
                self._pending_renewed_series = self._role

        if self._merch_negotiated:
            deal = MerchandisingDeal(franchise_id=self._role.franchise_id, royalty_share=self._merch_share, signed_year=self.age())
            self.state = replace(self.state, merchandising_deals=(*self.state.merchandising_deals, deal))

        self._acting_worked_this_year = True
        self._pending_billing = self._role.billing
        self._pending_bonus_income = 0.0
        self._last_result = result
        self._scenes = []

        return {
            "n_episodes": self._role.n_episodes,
            "studio_name": studio.name,
            "merchandising_negotiated": self._merch_negotiated,
            "merchandising_share_pct": round(self._merch_share * 100, 2) if self._merch_negotiated else None,
            "marketing_push_requested": result.marketing_push_requested,
            "marketing_push_honored": result.marketing_push_honored,
            "rating_band": result.rating_band,
            "rating_stance": result.rating_stance_applied,
            "rating_cut_forced": result.rating_cut_forced,
            "rating_studio_pressure": result.rating_studio_pressure,
            "performance_band": performance_band(result.performance),
            "critic_band": critic_band(result.film_critic_score),
            "critic_score": round(result.film_critic_score),
            "audience_band": audience_band(result.audience_score),
            "roi_band": roi_band(result.roi),
            "license_value_millions": round(result.gross, 1),
            "budget_millions": round(result.budget, 1),
            "marketing_millions": round(result.marketing, 1),
            "roi": round(result.roi, 2),
            "final_retention_pct": retention_summary["final_retention_pct"],
            "average_retention_pct": retention_summary["average_retention_pct"],
            "renewable": self._role.series_renewable,
            "renewal_chance": round(renewal_chance, 2) if renewal_chance is not None else None,
            "renewed": renewed,
        }

    @staticmethod
    def _weekly_gross(result: ProjectResult, strategy: str) -> list[float] | None:
        if strategy not in (WIDE, LIMITED) or result.gross <= 0:
            return None
        return [round(w, 1) for w in weekly_gross_curve(result.opening, result.legs, weeks=5)]

    # ---- awards (§4.11) — six distinct categories, researched against how real ceremonies
    # actually differ (Academy: Lead/Supporting, no genre split; Globes: Lead splits Drama vs.
    # Musical/Comedy, Supporting doesn't; SAG: Ensemble judges the cast, not one performance;
    # Gotham/Spirit-style bodies: a genuinely easier Breakthrough lane) — see awards/awards.py's
    # own module-level note. -------------------------------------------------------------------

    def awards_campaign_available(self) -> bool:
        return self._last_result is not None and self._last_result.spotlight >= AWARDS_SPOTLIGHT_THRESHOLD

    def available_award_categories(self) -> list[str]:
        """The honest lane(s) your last completed role can campaign in — see
        awards.eligible_performance_categories's own docstring for why this can be more than one
        (Ensemble is always on the list; Breakthrough only for an early-career actor)."""
        if self._last_result is None:
            return []
        r = self._last_result
        return list(eligible_performance_categories(
            r.role.genre, r.role.billing, self.state.actor.credits, is_animation=r.role.is_animation,
        ))

    def run_awards_campaign(self, category: str, spend_millions: float = 1.0, attempt_category_fraud: bool = False) -> dict:
        """A real BuzzScore campaign, resolved on the spot against a handful of generated
        competitors — not the full multi-year awards-season calendar (out of scope), but a real
        use of awards/awards.py's formulas instead of leaving them unreachable.

        category: one of awards.AWARD_CATEGORIES. Ensemble reads the film (ensemble_buzz_score),
        not your own performance; every other category reads buzz_score as before.

        attempt_category_fraud: §4.11's lead-in-supporting play — a real, player-chosen risk
        (category_fraud()'s own +18 advantage against a 35% chance of getting caught and paying a
        real Notoriety cost). Only meaningful when campaigning SUPPORTING with a lead-billed role
        — the actual "played a lead, campaigned it as supporting" move this constant has always
        described. False (the default) campaigns straight, no advantage, no risk.

        Career history (award_nominations/award_wins) now feeds NarrativeContext for real — before
        this pass those were always 0, which meant "she's due" could never actually fire. Genre and
        role_depth gate every category (awards.apply_award_ceiling), per design/part-09 §9.1's
        genre table and creative-revamp-plan.md §14.3's role-depth gate — a horror film or an
        underwritten part is a real, capped lane, not a fair fight against a drama showcase.

        A win moves exactly one Standing meter by a small, one-time amount (awards.award_win_bonus)
        — Prestige for Lead/Supporting, Affection for Ensemble, Heat for Breakthrough — "a small
        amount of benefit, nothing too significant," never a second system on top of Standing."""
        r = self._last_result
        actor = self.state.actor
        prestige = actor.standing["prestige"]
        category_advantage = 0.0
        caught = False
        if attempt_category_fraud:
            category_advantage, caught, notoriety_delta = category_fraud(self.rng)
            if caught:
                standing = actor.standing.copy()
                standing.add("notoriety", notoriety_delta)
                actor = replace(actor, standing=standing)
                self.state = replace(self.state, actor=actor)
        ctx = NarrativeContext(
            prior_nominations=actor.award_nominations, prior_wins=actor.award_wins,
            is_first_nomination=actor.credits <= 3, age=actor.age,
            transformation_flag=r.transformation,
        )
        bonus = narrative_bonus(ctx)
        if category == ENSEMBLE:
            your_buzz = ensemble_buzz_score(r.film_critic_score, r.project_quality, r.spotlight, spend_millions, self.rng)
            comp_spotlight_mean, comp_spotlight_sd = FIELD_COMPETITOR_SPOTLIGHT_MEAN, FIELD_COMPETITOR_SPOTLIGHT_SD
            comp_critic_mean, comp_critic_sd = FIELD_COMPETITOR_CRITIC_MEAN, FIELD_COMPETITOR_CRITIC_SD
        else:
            your_buzz = buzz_score(r.spotlight, r.film_critic_score, spend_millions, prestige, bonus, category_advantage, self.rng)
            if category == BREAKTHROUGH:
                comp_spotlight_mean, comp_spotlight_sd = BREAKTHROUGH_COMPETITOR_SPOTLIGHT_MEAN, BREAKTHROUGH_COMPETITOR_SPOTLIGHT_SD
                comp_critic_mean, comp_critic_sd = BREAKTHROUGH_COMPETITOR_CRITIC_MEAN, BREAKTHROUGH_COMPETITOR_CRITIC_SD
            else:
                comp_spotlight_mean, comp_spotlight_sd = FIELD_COMPETITOR_SPOTLIGHT_MEAN, FIELD_COMPETITOR_SPOTLIGHT_SD
                comp_critic_mean, comp_critic_sd = FIELD_COMPETITOR_CRITIC_MEAN, FIELD_COMPETITOR_CRITIC_SD
        your_buzz = apply_award_ceiling(your_buzz, r.role.genre, r.role.role_depth, category)
        competitors = [
            buzz_score(self.rng.gauss(comp_spotlight_mean, comp_spotlight_sd), self.rng.gauss(comp_critic_mean, comp_critic_sd),
                       self.rng.uniform(0.2, 2.0), self.rng.gauss(50, 20), 0.0, 0.0, self.rng)
            for _ in range(4)
        ]
        won = your_buzz > max(competitors)
        nominated = won or your_buzz > sorted(competitors)[1]
        if won:
            meter, delta = award_win_bonus(category)
            standing = self.state.actor.standing.copy()
            standing.add(meter, delta)
            self.state = replace(self.state, actor=replace(self.state.actor, standing=standing))
        self.state = replace(self.state, actor=replace(
            self.state.actor,
            award_nominations=self.state.actor.award_nominations + (1 if nominated else 0),
            award_wins=self.state.actor.award_wins + (1 if won else 0),
        ))
        return {
            "category": category, "won": won, "nominated": nominated, "narrative_bonus": bonus,
            "category_fraud_attempted": attempt_category_fraud, "category_fraud_caught": caught,
        }

    # ---- director awards — same six-category system, judged on director inputs instead of an
    # actor's own Spotlight/Persona, competing against other directors. --------------------------

    def director_awards_campaign_available(self) -> bool:
        return self._last_directed_release is not None and self._last_directed_release.film_critic_score >= AWARDS_SPOTLIGHT_THRESHOLD

    def run_director_awards_campaign(self, spend_millions: float = 1.0) -> dict:
        """DIRECTOR is the only category a director campaigns — Lead/Supporting/Ensemble/
        Breakthrough are all actor-track categories by design (they read Persona/billing/credits,
        none of which a director has); this stays a real, separate, single-category campaign
        rather than force-fitting a director into the actor pool as a sixth flavor of "lead."""
        snapshot = self._last_directed_release
        d = self.state.director
        director_input = (
            skill.VISION_WEIGHT * d.attrs.vision + skill.COMMAND_WEIGHT * d.attrs.command + skill.CRAFT_WEIGHT * d.attrs.craft
        )
        prestige = d.standing["prestige"]
        your_buzz = buzz_score(director_input, snapshot.film_critic_score, spend_millions, prestige, 0.0, 0.0, self.rng)
        your_buzz = apply_award_ceiling(your_buzz, snapshot.genre, "standard")
        competitors = [
            buzz_score(self.rng.gauss(FIELD_COMPETITOR_SPOTLIGHT_MEAN, FIELD_COMPETITOR_SPOTLIGHT_SD),
                       self.rng.gauss(FIELD_COMPETITOR_CRITIC_MEAN, FIELD_COMPETITOR_CRITIC_SD),
                       self.rng.uniform(0.2, 2.0), self.rng.gauss(50, 20), 0.0, 0.0, self.rng)
            for _ in range(4)
        ]
        won = your_buzz > max(competitors)
        nominated = won or your_buzz > sorted(competitors)[1]
        if won:
            meter, delta = award_win_bonus(DIRECTOR)
            standing = d.standing.copy()
            standing.add(meter, delta)
            self.state = replace(self.state, director=replace(d, standing=standing))
        # One campaign per film: unlike the acting track (which naturally gets a fresh
        # ProjectResult almost every year), a director can spend several years developing the
        # next one — director_awards_campaign_available() would otherwise keep reading this same
        # snapshot as "eligible" and let the same finished film win or get nominated over and
        # over, once per year, until a new film actually wraps. Clearing it here means a real new
        # release is required before the next campaign, the same one-shot-per-film rule the
        # awards system is meant to enforce.
        self._last_directed_release = None
        return {"category": DIRECTOR, "won": won, "nominated": nominated}

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
        """action: "check_in" | "show_up" | "read_agenda" | "vouch". Returns a short result line.
        Costs one of this year's actor quarters (see actor_quarters_remaining_this_year()) — a real
        choice about where your attention goes when you're not tied up on a production, not a free
        unlimited menu."""
        if self.actor_quarters_remaining_this_year() <= 0:
            return "No time left this year — every quarter's already spoken for."
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
        self._actor_quarters_this_year += 1

        if updated.relationship_state != before:
            return f"Now: {relationship_band(updated.relationship_state)}."
        return "Noted. Nothing's changed yet."

    def persona_status(self) -> dict:
        """actor.persona.Persona's own Legibility, made visible for the first time — the whole
        typecasting system (offer-board flavor text, the in-lane audience bonus, the type-break
        difficulty tax, the transformation payoff) reads off this same profile, so the player needs
        a real way to see it, not just feel its effects as unexplained variance."""
        persona = self.state.actor.persona
        return {
            "legibility": round(persona.legibility(), 1),
            "legibility_band": persona.legibility_band(),
            "top_genre": persona.top_genre(),
            "top_archetype": persona.top_archetype(),
            "consecutive_same_lane": persona.consecutive_same_lane,
        }

    def application_status(self) -> dict:
        """leverage.catalogue's agent boost/fatigue, made visible — the same "never a silently
        moving number" rule persona_status() already follows. applications_this_year resets with
        every offer_board() (a new year, a clean slate); the band is agent-tier-relative (the same
        application count reads completely differently depending on who's actually making the
        calls), not a flat count."""
        agent_tier = self.state.leverage.agent_tier
        return {
            "agent_tier": agent_tier,
            "applications_this_year": self._applications_this_year,
            "fatigue_band": fatigue_band(agent_tier, self._applications_this_year),
        }

    def leverage_status(self) -> dict:
        lev = self.state.leverage
        return {"agent_tier": lev.agent_tier, "scarcity": round(lev.scarcity, 1), "next_tier": next_agent_tier(lev.agent_tier)}

    def try_advance_agent_tier(self) -> str:
        if self.actor_quarters_remaining_this_year() <= 0:
            return "No time left this year — every quarter's already spoken for."
        sc = self.state.actor.standing.weighted_score(STANDING_WEIGHTS)
        lev = self.state.leverage
        if not can_advance_agent_tier(lev.agent_tier, sc):
            nxt = next_agent_tier(lev.agent_tier)
            return f"Not yet — {nxt} wants more Standing than you're carrying." if nxt else "You're already at the top."
        new_tier = advance_agent_tier(lev.agent_tier, sc)
        self.state = replace(self.state, leverage=replace(lev, agent_tier=new_tier))
        self._actor_quarters_this_year += 1
        return f"Signed with a {new_tier} agency."

    def disappear(self) -> str:
        """§6.6 — a real pull action: skip the next offer on purpose, banking Scarcity for a
        better one when you come back. Doesn't advance the year itself (see end_year()). Spends the
        rest of this year's actor quarters at once — going quiet is a real, deliberate withdrawal of
        your whole year's attention, not a one-quarter errand."""
        if self.actor_quarters_remaining_this_year() <= 0:
            return "No time left this year — every quarter's already spoken for."
        self._actor_quarters_this_year = QUARTERS_PER_YEAR
        lev = self.state.leverage
        self.state = replace(self.state, leverage=replace(lev, scarcity=accumulate_scarcity(lev.scarcity)))
        return "You go quiet for a year. People notice, eventually, when you come back."

    # ---- directing — a second career fused into this same Session/FullState ------------------

    def directing_unlocked(self) -> bool:
        """Directing is reachable at any point — no Prestige/credits gate. Whether you actually
        get films made and how good they are comes entirely from your own DirectorAttributes
        (vision/command/craft/taste/efficiency, director/attributes.py) once you're in the chair,
        an independent stat block that never reads your acting Standing at all — there's no
        acting-side threshold to walk through first, only the director-side numbers you actually
        earn by directing. Kept as a method (not just always-True inline) so a future real gate —
        e.g. requiring a favour, or a one-time cost — has one call site to change."""
        return True

    def is_directing(self) -> bool:
        return self.state.director is not None

    def become_director(self) -> str:
        if self.state.director is not None:
            return "You're already directing."
        self.state = replace(self.state, director=new_director_state())
        return "You step behind the camera for the first time."

    def director_status(self) -> dict:
        """§7.4 v16 — every project is reported the same way, indexed by its position in the slate;
        there's no privileged "active" one. "quarters_this_year"/"quarters_per_year" tell a caller
        how much of this year's real attention is still available to spend."""
        d = self.state.director
        return {
            "credits": d.credits,
            "standing": standing_band(d.standing.weighted_score(STANDING_WEIGHTS)),
            "max_projects": MAX_PROJECTS,
            "can_start_new_project": can_start_new_project(d),
            "quarters_this_year": self._director_quarters_this_year,
            "quarters_per_year": QUARTERS_PER_YEAR,
            "trailing_roi": round(d.trailing_roi, 2),  # director.development.bankability_multiplier's
            # own input — a recency-weighted read of recent films' real ROI, not a lifetime average
            "projects": [
                {
                    "index": i, "genre": s.genre, "budget_ask": round(s.project.budget_ask, 2),
                    "franchise_id": s.project.franchise_id, "installment_number": s.project.installment_number,
                    "momentum_band": director_momentum_band(s.project.momentum),
                    # v21 — perceived_script_quality (director/attributes.py) existed but was never
                    # wired to anything; the player previously had zero read, true or perceived, on
                    # their own project's script quality. Banded through the same critic_band()
                    # scale everything else already uses — no new band table.
                    "script_quality_read": critic_band(s.perceived_script_quality),
                    "quarters_in_dev": s.project.quarters_in_dev,
                    "self_financed": s.project.self_financed,
                    "frozen": s.project.frozen,
                    # v12 — a real, visible production state: not developing anymore, and not
                    # resolved yet either. quarters_remaining_in_shoot counts down at end_year(),
                    # on its own real calendar, regardless of what other project gets this year's
                    # dev-action attention.
                    "shooting": s.project.quarters_remaining_in_shoot is not None,
                    "quarters_remaining_in_shoot": s.project.quarters_remaining_in_shoot,
                    # None for a self-financed or guaranteed (hire) project — neither ever rolls
                    # against a studio's own greenlight_probability, so bankability never applies.
                    "bankability": (
                        None if (s.project.self_financed or s.project.guaranteed_greenlight)
                        else round(director_development.bankability_multiplier(d.trailing_roi, s.project.budget_ask), 2)
                    ),
                    "attachments": [
                        {"id": a.attachment_id, "type": a.attachment_type, "quarters_attached": a.quarters_attached}
                        for a in s.project.attachments
                    ],
                    # §7.4 v25 — never a silently moving number: the same fee/backend terms
                    # push_director_deal_for_backend() can trade against, visible before and after.
                    "fee_share_pct": (
                        None if s.project.self_financed or s.project.negotiated_fee_share is None
                        else round(s.project.negotiated_fee_share * 100, 1)
                    ),
                    "box_office_bonus_type": s.project.box_office_bonus_type,
                    "box_office_bonus_share_pct": (
                        round(s.project.box_office_bonus_share * 100, 2) if s.project.box_office_bonus_type else None
                    ),
                }
                for i, s in enumerate(d.projects)
            ],
        }

    @staticmethod
    def director_genre_options() -> list[tuple[str, str]]:
        return [(g, g.title()) for g in GENRES]

    @staticmethod
    def director_budget_tier_options() -> list[tuple[str, str]]:
        # §7.4 v22 — a tier is a real range now, not a fixed number; "~$XM" is the honest label.
        return [(tier, f"{tier.title()} — ~${budget:.0f}M") for tier, budget in TIER_BUDGETS.items()]

    def start_directing_project(
        self, genre: str, budget_tier: str, self_financed: bool = False,
        franchise_id: str | None = None, new_franchise: bool = False,
        cast_decision: str | None = None,
    ) -> bool:
        """§7.4 v16 — returns False (a no-op) when the slate is already at MAX_PROJECTS; never
        gated behind Standing. Always appends — a new pitch never displaces anything in progress.

        §7.4 v22 — the chosen tier sets a real range to land in (sample_tier_budget_millions), the
        same log-normal-around-a-median shape the acting side's own budgets already use, not a
        single flat number every time.

        self_financed: a genuinely independent project — no studio ever attached, never a mid-
        development buyout. Real, matching trade: it routes through the exact same self_financed
        branch a buyout already does, so the very next action taken resolves the film outright —
        no runway left to attach anyone or rewrite the script first — and the whole budget comes
        out of your own net worth the moment it's made (see advance_directing()'s own deduction),
        whether or not you can actually afford it. Not a gate, a real financial cliff you choose to
        walk off — the same one an acquired project already walks off, just from day one instead.

        franchise_id: v27 — pitch the next installment of an existing franchise from directing_
        franchise_options() instead of an original property; genre is overridden to the
        franchise's own (matching how a sequel role's genre already works on the actor side).
        new_franchise: start a brand-new property instead — not registered in the shared pool
        until this first installment actually resolves (same shape update_franchise_after_project
        already uses for a fresh actor-side franchise).

        cast_decision: v28 — compartmentalized from the sequel/reboot/spinoff pitching above; only
        meaningful alongside franchise_id (an actual sequel). "recast" or "write_out" reuses the
        SAME two real outcomes a lost actor holdout already resolves through — director-initiated
        this time, not triggered by an actor's own leverage failure. Any other value (the default,
        None) keeps the returning cast, no penalty, no roll."""
        if not can_start_new_project(self.state.director):
            return False
        budget = sample_tier_budget_millions(budget_tier if budget_tier in TIER_BUDGETS else "low", self.rng)
        franchise = self.state.franchises.get(franchise_id) if franchise_id else None
        self.state = replace(
            self.state,
            director=start_development(
                self.state.director, genre, budget, self.rng,
                self_financed=self_financed, studio_relations=self.state.studio_relations,
                franchise=franchise, current_year=self.age(), new_franchise=new_franchise,
                cast_decision=cast_decision,
            ),
        )
        self._director_attach_target_npc_id = None
        return True

    def scrap_directing_project(self, project_index: int) -> None:
        """§7.4 v16 — real permission to just walk away and free the slot, no cost, no roll."""
        self.state = replace(self.state, director=scrap_project(self.state.director, project_index))

    # ---- attach someone (§7.4 v11) — not necessarily a star, read from the real Rolodex ---------

    def attach_star_target_options(self) -> list[dict]:
        """Every tracked Rolodex NPC (any type — doesn't have to be a costar you've already worked
        with) plus the always-available cold/untracked option. Bankability reads their own Heat (a
        real Standing meter) where they have one tracked; untracked NPCs and the cold option both
        fall back to a neutral 50 — a real number regardless of who they turn out to be."""
        options = [{"id": None, "label": "Someone new — a cold approach", "relationship": "stranger", "bankability": 50.0}]
        for n in self.state.rolodex.tracked():
            bankability = n.standing["heat"] if n.standing is not None else 50.0
            options.append({
                "id": n.npc_id, "label": n.npc_id, "relationship": n.relationship_state, "bankability": round(bankability, 1),
            })
        return options

    @staticmethod
    def attach_star_type_options() -> list[tuple[str, str]]:
        return [
            (director_development.ATTACHMENT_BANKABLE, "Bankable — real fame, real PackageStrength, the fee to match"),
            (director_development.ATTACHMENT_GENRE_FIT, "Good fit — not famous, but right for it; eases the ask itself"),
            (director_development.ATTACHMENT_STUDIO_FAVORITE, "A studio favourite — reliable, modest, not fame-scaled at all"),
        ]

    def choose_attach_star_target(self, npc_id: str | None, attachment_type: str = "bankable") -> None:
        self._director_attach_target_npc_id = npc_id
        self._director_attach_type = attachment_type if attachment_type in director_development.ATTACHMENT_TYPES else director_development.ATTACHMENT_BANKABLE

    @staticmethod
    def adaptation_source_type_options() -> list[tuple[str, str]]:
        """design/part-09 §9.4's own "where scripts come from" table — each source's real rights-
        cost tier and built-in audience, read straight off director_development.ADAPTATION_SOURCE_
        COST_CEILING_FRACTION/ADAPTATION_SOURCE_AUDIENCE_BONUS."""
        labels = {
            "public_domain": "Public domain — free rights, but everyone knows it",
            "foreign_remake": "Foreign remake — low-moderate cost, no built-in audience here",
            "novel": "Novel — moderate cost, a small loyal readership",
            "stage_play": "Stage play — moderate cost, a prestige audience",
            "true_story": "True story — life rights, a moderate real-person risk",
            "comic": "Comic / graphic novel — high cost, a large vocal fanbase",
            "video_game": "Video game — high cost, a large young fanbase",
            "toy_line": "Toy line / brand — very high cost, an enormous built-in audience",
        }
        return [(t, labels[t]) for t in director_development.ADAPTATION_SOURCE_TYPES]

    def choose_adaptation_source_type(self, source_type: str) -> None:
        self._director_adaptation_source_type = (
            source_type if source_type in director_development.ADAPTATION_SOURCE_TYPES else "novel"
        )

    def choose_adaptation_licensing_fraction(self, fraction: float) -> None:
        """v19/v20 — how much of this source's own real option-cost ceiling (adaptation_option_
        cost, scaled by choose_adaptation_source_type's own pick) to actually offer on the next
        "option_adaptation" dev action taken (any project) — a cut-rate option on obscure material
        costs little and moves momentum little; paying closer to the going rate pulls harder. A
        real production cost, added straight onto the project's own budget_ask the moment that
        action is taken (advance_directing) — not a personal expense, the same way a bigger cast or
        longer shoot inflates the real budget rather than coming out of your own pocket directly.
        Resets to the 0.5 default after each use."""
        self._director_licensing_cost_fraction = clamp(fraction, 0.0, 1.0)

    # ---- casting (§7.5) and the shoot's style (§7.6) — set once per project, like script notes --

    @staticmethod
    def director_casting_options() -> list[tuple[str, str]]:
        labels = {
            director_casting.BANKABLE_WRONG_FIT: "The bankable star, wrong for it — budget unlocked, a real fit penalty",
            director_casting.RIGHT_ACTOR_NO_HEAT: "The right actor, no heat — best performance, Difficulty stays high",
            director_casting.DISCOVERY: "The discovery — enormous variance, a real shot at a breakout",
            director_casting.YOUR_ROSTER: "Your roster — reliable, a Chemistry bonus, below quote",
            director_casting.DIFFICULT_GENIUS: "The difficult genius — highest ceiling, real chaos risk",
        }
        return [(c, labels[c]) for c in director_casting.CASTING_CHOICES]

    def choose_director_casting_action(self, project_index: int, choice: str) -> None:
        self.state = replace(self.state, director=choose_director_casting(self.state.director, project_index, choice))

    # ---- the director's own Deal (§7.4 v25) — the actor's choose_deal()/box_office_bonus_
    # available() mirrored onto directing: start_development() already auto-negotiates this
    # project's base fee and, for a high-Standing director, a box-office bonus for free; this is
    # the deliberate ask that trades a lower guaranteed fee for real backend upside instead of
    # waiting on that automatic roll. -------------------------------------------------------------

    def director_deal_available(self, project_index: int) -> bool:
        return director_deal_still_open(self.state.director, project_index)

    def director_box_office_bonus_available(self, bonus_type: str = "net_points") -> bool:
        return director_can_negotiate_box_office_bonus(self.state.director, bonus_type)

    def push_director_deal_for_backend(self, project_index: int, bonus_type: str = "net_points") -> dict:
        """Trades this project's negotiated fee down to the studio range's own floor for a real
        shot at the box-office bonus director_box_office_bonus_available() gates on Standing —
        a no-op (granted: False) if either gate says no, same quiet failure shape as choose_deal()."""
        bonus_type = bonus_type if bonus_type in ("net_points", "first_dollar_gross") else "net_points"
        if not self.director_deal_available(project_index) or not self.director_box_office_bonus_available(bonus_type):
            return {"granted": False}
        self.state = replace(
            self.state, director=negotiate_director_backend_deal(self.state.director, project_index, bonus_type, self.rng),
        )
        project = self.state.director.projects[project_index].project
        return {
            "granted": True,
            "fee_share_pct": round(project.negotiated_fee_share * 100, 1),
            "bonus_type": bonus_type,
            "bonus_share_pct": round(project.box_office_bonus_share * 100, 2),
        }

    @staticmethod
    def director_shoot_style_options() -> list[tuple[str, str]]:
        labels = {
            director_shoot_style.HEAVY_COVERAGE: "Heavy coverage — safer, fixable in the edit",
            director_shoot_style.LONG_TAKES: "Long takes — higher ceiling, real risk if the cast is weak",
            director_shoot_style.MANY_TAKES: "Many takes — rewards real Craft, punishes weak Craft",
            director_shoot_style.IMPROVISATION: "Improvisation — rewards Instinct, script matters less",
            director_shoot_style.LEAN_AND_FAST: "Lean and fast — lower ceiling, real Efficiency reputation",
        }
        return [(s, labels[s]) for s in director_shoot_style.SHOOT_STYLES]

    def choose_director_shoot_style_action(self, project_index: int, style: str) -> None:
        self.state = replace(self.state, director=choose_director_shoot_style(self.state.director, project_index, style))

    # ---- a director's own script notes, release request, and marketing push ------------------
    # Reuses the same underlying formulas as the acting side: script notes (core.script_notes),
    # the release-strategy request (studios.decide_release_strategy), and the marketing push
    # (studios.decide_marketing_spend) — but weighed by director_influence_on_studio_decision()
    # instead of the actor curve, since it's the director's own film either way. On a directed
    # project the director's script note IS the film's primary note (core.script_notes.DIRECTOR_
    # NOTE_WEIGHT, full strength) — there's no separate NPC director sampling one on top, unlike an
    # actor's own film (simulation/career.py's resolve_shoot/resolve_quality).

    @staticmethod
    def director_script_note_options() -> list[tuple[str, str]]:
        labels = {
            "clarity": "Push for clarity — audiences follow it, critics call it obvious",
            "ambiguity": "Push for ambiguity — critics lean in, audiences find it cold",
            "whole_film": "Push for the whole film — no angle, it just gets better",
        }
        return [(o, labels[o]) for o in DIRECTOR_SCRIPT_NOTE_OPTIONS]

    def choose_director_script_note_action(self, project_index: int, choice: str) -> None:
        self.state = replace(self.state, director=choose_director_script_note(self.state.director, project_index, choice, self.rng))

    @staticmethod
    def director_release_options() -> list[tuple[str, str]]:
        return [(s, RELEASE_LABELS[s]) for s in RELEASE_STRATEGIES]

    def request_director_release_strategy(self, project_index: int, strategy: str) -> None:
        self.state = replace(self.state, director=request_director_release(self.state.director, project_index, strategy))

    def request_director_marketing_push_action(self, project_index: int) -> None:
        self.state = replace(self.state, director=request_director_marketing_push(self.state.director, project_index))

    @staticmethod
    def director_dev_action_options() -> list[tuple[str, str]]:
        labels = {
            "rewrite": "Rewrite — improve the script",
            "attach_star": "Attach a star — real bankability, real momentum",
            "cut_budget": "Cut the budget — easier to greenlight, less to work with",
            "new_financier": "Find a new financier",
            "take_to_market": "Take it to market",
            "self_finance": "Self-finance — buy the project out from the studio (or they let it go for "
                            "nothing) and make it entirely your own, on your own money",
            "drawer": "Put it in the drawer — walk away for now",
            "call_in_favour": "Call in a favour — a Rolodex financier owes you one",
            "option_adaptation": "Option an adaptation — pivot onto existing IP",
        }
        return [(a, labels[a]) for a in DEV_ACTIONS]

    def quarters_remaining_this_year(self) -> int:
        return max(0, QUARTERS_PER_YEAR - self._director_quarters_this_year)

    def advance_directing(self, project_index: int, action: str) -> dict:
        """One quarter's directing work, spent on state.director.projects[project_index] — mirrors
        the acting side's one-project-a-year cadence, but directing now runs up to QUARTERS_PER_YEAR
        times a year, once per quarter, so a real triage decision (which project gets *this*
        quarter) sits alongside the dev-action choice itself. Refuses once this year's quarters are
        already spent — call end_year() to reset the count. Does not advance the shared calendar
        itself (see end_year())."""
        if self.quarters_remaining_this_year() <= 0:
            return {"error": "no quarters left this year", "greenlit": False, "dead": False, "frozen": False}
        genre = self.state.director.projects[project_index].genre if 0 <= project_index < len(self.state.director.projects) else None
        demand = world_genre_demand(self.state.genre_heat, genre)

        attach_kwargs = {}
        leverage = self.state.leverage
        if action == "attach_star":
            target_id = self._director_attach_target_npc_id
            target = self.state.rolodex.npcs.get(target_id) if target_id else None
            tier = target.relationship_state if target is not None else "stranger"
            bankability = (target.standing["heat"] if target is not None and target.standing is not None else 50.0)
            rivalry_depth = clamp((target.grudge if target is not None else 0.0) / 100.0, 0.0, 1.0)
            attach_kwargs = {
                "attach_star_target_tier": tier, "attach_star_target_bankability": bankability,
                "attach_star_target_npc_id": target_id, "attach_attachment_type": self._director_attach_type,
                "attach_star_rivalry_depth": rivalry_depth,
            }
            if target is not None and tier in ("loyal", "ally") and target_id is not None:
                # Real, discounted favour cost for a Loyal/Ally attachment — §7.4 v10's own
                # relationship-tiered price, not the flat market rate.
                cost = attach_star_favour_cost(base_cost=2, tier=tier)
                if leverage.favours.can_spend(target_id, cost):
                    leverage = replace(leverage, favours=leverage.favours.spend(target_id, cost))
        has_rival = any(n.relationship_state == "rival" for n in self.state.rolodex.npcs.values())
        # v11 fix — the studio a project already named at start_development()/accept_hire_offer()
        # time (project.financing_studio_id) reads the SAME studio_relations trust ledger the
        # acting track builds, so a real history with that studio actually moves this project's
        # own greenlight odds instead of being scored against a studio picked fresh and unrelated.
        financing_studio_id = None
        if 0 <= project_index < len(self.state.director.projects):
            financing_studio_id = self.state.director.projects[project_index].project.financing_studio_id
        studio_trust = trust_of(self.state.studio_relations, financing_studio_id) if financing_studio_id else TRUST_DEFAULT

        director, info = apply_dev_action_and_advance(
            self.state.director, project_index, action, demand, self.rng,
            available_money=self.state.life.money.net_worth,
            has_tracked_rival_same_genre=has_rival,
            studio_trust=studio_trust,
            licensing_cost_fraction=self._director_licensing_cost_fraction,
            adaptation_source_type=self._director_adaptation_source_type,
            current_year=self.age(),
            franchise_last_release_year={fid: f.last_installment_year for fid, f in self.state.franchises.items()},
            **attach_kwargs,
        )
        self._director_attach_target_npc_id = None
        self._director_attach_type = director_development.ATTACHMENT_BANKABLE
        self._director_licensing_cost_fraction = 0.5
        self._director_adaptation_source_type = "novel"
        self._director_quarters_this_year += 1

        life = self.state.life
        self.state = replace(self.state, leverage=leverage)
        if info.get("self_finance_cost_paid", 0.0) > 0.0:
            # The studio wouldn't just walk away — bought the rights outright, out of your own
            # money, before you've made a dollar back on the film itself.
            life = replace(life, money=replace(life.money, net_worth=life.money.net_worth - info["self_finance_cost_paid"]))
        # §7.4 v16 — limbo buyouts are real money spent too, same as a deliberate self_finance —
        # potentially several in one quarter, one per neglected project that got bought out.
        limbo_cost = sum(e.get("cost_paid", 0.0) for e in info.get("limbo_events", []))
        if limbo_cost > 0.0:
            life = replace(life, money=replace(life.money, net_worth=life.money.net_worth - limbo_cost))

        # v12 — a greenlight no longer means the film is finished; info["greenlit"] here just means
        # "started shooting" (see simulation._director.apply_dev_action_and_advance's own
        # docstring). Every real consequence of an actually-finished film (money, Standing, genre
        # heat, studio trust) now only ever fires once it resolves, in end_year() — see
        # _apply_resolved_directed_film below.
        self.state = replace(self.state, director=director, life=life)

        result = {"greenlit": info["greenlit"], "resolved": info.get("resolved", False),
                  "shooting": info.get("shooting", False),
                  "quarters_remaining_in_shoot": info.get("quarters_remaining_in_shoot"),
                  "dead": info["dead"], "frozen": info.get("frozen", False),
                  "momentum": info["momentum"], "momentum_band": info.get("momentum_band", ""),
                  "dropped_attachments": info.get("dropped_attachments", []),
                  "attachment_offer_accepted": info.get("attachment_offer_accepted"),
                  "limbo_outcome": info.get("limbo_outcome"),
                  "blocked_on_money": info.get("blocked_on_money", False),
                  "shortfall": info.get("shortfall"),
                  "adaptation_cost_added_to_budget": round(info.get("adaptation_cost_added", 0.0), 2),
                  "limbo_events": [
                      {**e, "cost_paid": round(e["cost_paid"], 2)} for e in info.get("limbo_events", [])
                  ]}
        if "self_finance_acquired" in info:
            # An acquisition-only year — the studio either released it for free or you bought it
            # out, but the film itself isn't made yet (that's a separate, later action).
            result.update({
                "self_finance_acquired": info["self_finance_acquired"],
                "self_finance_released_free": info["self_finance_released_free"],
                "self_finance_cost_paid": round(info["self_finance_cost_paid"], 2),
                "self_finance_could_not_afford": info["self_finance_could_not_afford"],
                "self_finance_buyout_cost": round(info["self_finance_buyout_cost"], 2),
            })
        return result

    def _apply_resolved_directed_film(self, info: dict) -> dict:
        """A shooting project's quarters_remaining_in_shoot just hit 0 (simulation._director.
        advance_shoots_and_resolve, called once a year from end_year()) — every real consequence of
        an actually-finished directed film that used to fire inline the instant it was greenlit now
        fires here instead, plus the one genuinely new piece: a real, separate studio-trust penalty
        for blowing past the studio's own original schedule expectation (director.development.
        schedule_trust_penalty), on top of (not instead of) the usual ROI-driven trust update — a
        studio remembers "you took way longer than you told us" as its own real betrayal, not just
        whatever the resulting profit did to the relationship."""
        life = self.state.life
        genre_heat = accumulate_heat(self.state.genre_heat, info["genre"], info["roi"])
        guild = add_residual_stream(self.state.guild, info["roi"], info["budget"])
        if info.get("self_financed"):
            # You took the studio's usual role, including the studio's usual money — the whole
            # budget comes straight out of your own net worth the moment the film is actually
            # made, real risk for the real control request_director_release_strategy()/
            # request_director_marketing_push_action() now genuinely guarantee on this project.
            # §7.4 v23 — this only ever fires once the engine's own affordability gate has
            # already confirmed you can cover it (see apply_dev_action_and_advance's
            # blocked_on_money check) — never pushes net worth negative to make a film happen.
            life = replace(life, money=replace(life.money, net_worth=life.money.net_worth - info["budget"]))
        # §7.4 v23 — real director income, finally: net proceeds on a self-financed film (gross
        # minus the marketing you also covered yourself), a real fee on a studio-backed or hire
        # film. Directing paid literally nothing before this — now it does.
        director_income = info.get("director_income", 0.0)
        if director_income:
            life = replace(life, money=replace(life.money, net_worth=life.money.net_worth + director_income))

        studio_relations = self.state.studio_relations
        financing_studio_id = info.get("financing_studio_id")
        if financing_studio_id is not None:
            # simulation._director never tracked a director-studio relationship at all before this
            # (a real, named gap its own module docstring called out) — reused straight off the
            # same studio_relations ledger the acting track already builds trust in, rather than a
            # second, disconnected number: a studio that ate a bad schedule overrun on a directed
            # film remembers it the same way it'd remember a bad acting deal.
            studio_relations = update_relationship(studio_relations, financing_studio_id, info["budget"], info["roi"], info["gross_millions"])
            expected = info.get("studio_expected_quarters")
            if expected is not None:
                penalty = director_development.schedule_trust_penalty(info.get("quarters_taken", 0), expected)
                if penalty > 0.0:
                    rel = studio_relations[financing_studio_id]
                    studio_relations = {**studio_relations, financing_studio_id: replace(rel, trust=clamp(rel.trust - penalty, 0.0, 100.0))}

        franchises = self.state.franchises
        franchise_id = info.get("franchise_id")
        if franchise_id is not None:
            # v27 — directors write back into the SAME shared franchises pool the actor track
            # reads/writes, via a real function (update_franchise_after_project) that expects a
            # Role — SimpleNamespace duck-types the three attributes it actually reads (franchise_
            # id/genre/studio) rather than forking a director-specific copy of that logic.
            role_like = SimpleNamespace(franchise_id=franchise_id, genre=info["genre"], studio=financing_studio_id or "mid_major")
            franchises = update_franchise_after_project(
                franchises, role_like, spotlight=info["audience_score"], audience_score=info["audience_score"],
                standing_model=self.state.director.standing, current_year=self.age(),
                requested_director_npc_id=PLAYER_DIRECTOR_ID,
            )

        self.state = replace(self.state, genre_heat=genre_heat, guild=guild, life=life, studio_relations=studio_relations, franchises=franchises)

        result = {
            "greenlit": True, "resolved": True,
            "franchise_id": franchise_id, "installment_number": info.get("installment_number"),
            "momentum": info.get("momentum", 1.0), "momentum_band": info.get("momentum_band", ""),
            "critic_band": critic_band(info["film_critic_score"]),
            "critic_score": info["critic_score"],
            "audience_band": audience_band(info["audience_score"]),
            "roi_band": roi_band(info["roi"]),
            "roi": info["roi"],
            "gross_millions": info["gross_millions"],
            "budget_millions": round(info["budget"], 1),
            "budget_ask_millions": info.get("budget_ask", info["budget"]),
            "schedule_overage_pct": info.get("schedule_overage_pct", 0.0),
            "quarters_taken": info.get("quarters_taken"),
            "studio_expected_quarters": info.get("studio_expected_quarters"),
            "marketing_millions": info["marketing_millions"],
            "requested_release": RELEASE_LABELS[info["requested_release"]] if info["requested_release"] else None,
            "release_label": RELEASE_LABELS[info["release_strategy"]],
            "release_overruled": info["release_overruled"],
            "marketing_push_requested": info["marketing_push_requested"],
            "marketing_push_honored": info["marketing_push_honored"],
            "self_financed": info["self_financed"],
            "director_income_millions": round(info.get("director_income", 0.0), 2),
            "box_office_bonus_type": info.get("box_office_bonus_type"),
            "casting_choice": info.get("casting_choice", ""),
            "shoot_style": info.get("shoot_style", ""),
            "rating_band": info.get("rating_band", ""),
            "genre": info["genre"],
        }
        if info["release_strategy"] in ("limited", "festival"):
            self._last_directed_release = DirectedReleaseSnapshot(
                genre=info["genre"], budget_millions=info["budget"], release_strategy=info["release_strategy"],
                rating_band=info.get("rating_band", "PG"), film_critic_score=info["film_critic_score"],
                audience_score=info["audience_score"], opening_millions=info.get("opening_millions", 0.0),
                legs=info.get("legs", 1.0), roi=info["roi"],
            )
        return result

    # ---- lifestyle floor (§11.6) — the correct move almost nobody makes in time -----------------

    def cut_lifestyle_floor(self, new_floor_millions: float) -> dict:
        """Available any time, not gated behind a bad year — deliberately drops your own spending
        floor below where the going-broke ratchet would otherwise hold it. Costs real Affection
        with your own entourage (life.money.CUT_THE_FLOOR_AFFECTION_COST), same felt-cost shape as
        multi_picture_deal's early-break notoriety penalty."""
        old_floor = self.state.life.money.lifestyle_floor
        money = cut_the_floor(self.state.life.money, new_floor_millions)
        standing = self.state.actor.standing.copy()
        standing.add("affection", -CUT_THE_FLOOR_AFFECTION_COST)
        self.state = replace(
            self.state, life=replace(self.state.life, money=money),
            actor=replace(self.state.actor, standing=standing),
        )
        return {
            "old_floor_millions": round(old_floor, 2),
            "new_floor_millions": round(money.lifestyle_floor, 2),
            "affection_cost": CUT_THE_FLOOR_AFFECTION_COST,
        }

    # ---- platform expansion (§7.12 v10) — a director's Limited/Festival hit can earn wider -----

    def platform_expansion_available(self) -> bool:
        return expansion_available(self._last_directed_release)

    def request_platform_expansion(self) -> dict:
        snapshot = self._last_directed_release
        importance = standing_score(self.state.director.standing)
        outcome = resolve_expansion(snapshot, DIRECTOR_STUDIO_TRUST, importance, self.rng)
        self._last_directed_release = replace(snapshot, expansion_used=True)
        if outcome.granted:
            net_gain = outcome.extra_gross_millions - outcome.extra_marketing_millions
            life = replace(self.state.life, money=replace(self.state.life.money, net_worth=self.state.life.money.net_worth + net_gain))
            self.state = replace(self.state, life=life)
        return {
            "granted": outcome.granted,
            "studio_name": STUDIOS[outcome.studio_id].name,
            "extra_gross_millions": round(outcome.extra_gross_millions, 1),
            "extra_marketing_millions": round(outcome.extra_marketing_millions, 1),
        }

    # ---- director-for-hire (§7.13 v10) — the studio comes to you, rarely, by construction -------

    def check_for_hire_offer(self) -> dict | None:
        """Call once per year, before the normal directing menu — a real, pushed notification only
        when the roll actually lands (rare by construction), never a forced yearly prompt. None if
        the slate's already full (§7.4 v16 — MAX_PROJECTS, not Standing-gated) or not yet a
        director at all."""
        if self.state.director is None or not can_start_new_project(self.state.director):
            return None
        genre = self.rng.choice(GENRES)
        heat_signal = world_genre_demand(self.state.genre_heat, genre)
        offer = roll_hire_offer(
            standing_score(self.state.director.standing), genre, heat_signal, TIER_BUDGETS, self.rng,
        )
        self._pending_hire_offer = offer
        if offer is None:
            return None
        return {"genre": offer.genre, "budget_millions": round(offer.budget_millions, 1), "studio_name": STUDIOS[offer.studio_id].name}

    def accept_hire_offer(self) -> dict:
        """Skips development hell outright — greenlit this same quarter, no dev-action prompt
        needed. Appends as a new slate slot (§7.4 v16 — a hire never displaces anything already in
        development). v12 — greenlit no longer means resolved: this starts the shoot (subject to
        the same MAX_CONCURRENT_SHOOTS gate as anything else); the real result comes back from
        end_year() once it actually wraps."""
        offer = self._pending_hire_offer
        self.state = replace(self.state, director=accept_hire_offer(self.state.director, offer, self.rng))
        self._pending_hire_offer = None
        new_index = len(self.state.director.projects) - 1
        return self.advance_directing(new_index, "rewrite")  # inert here — guaranteed_greenlight skips the roll

    def decline_hire_offer(self) -> None:
        self._pending_hire_offer = None

    # ---- the calendar — advances exactly once per year, however much you did in it -----------

    def end_year(self) -> list[dict]:
        """The one point the shared calendar actually moves: aging, Standing decay, Life, the
        Guild, Rolodex re-ranking, franchise dormancy. Call this once per year after resolving
        whatever combination of acting and/or directing you did — choose_release()/decline_board()/
        request_holdout()/disappear() all resolve their own outcome (Standing deltas, money)
        immediately, but none of them touch the calendar anymore, so acting and directing are free
        to both happen in the same year.

        v12 — a directed film no longer resolves the instant it's greenlit (see advance_directing's
        own docstring); a live shoot runs on its own real calendar instead, advanced right here
        (simulation._director.advance_shoots_and_resolve) before anything else this year moves.
        Returns whatever directed films actually wrapped this year (almost always 0 or 1 — only one
        production can ever be shooting at a time) — each a real, fully resolved result exactly
        shaped like advance_directing() used to return inline."""
        resolved_films: list[dict] = []
        if self.state.director is not None:
            new_director, wrapped = advance_shoots_and_resolve(self.state.director, self.state.genre_heat, self.rng)
            self.state = replace(self.state, director=new_director)
            for info in wrapped:
                resolved_films.append(self._apply_resolved_directed_film(info))

        self.state = advance_between_years(
            self.state, self.rng, worked_this_year=self._acting_worked_this_year,
            billing=self._pending_billing, bonus_income=self._pending_bonus_income,
        )
        self._acting_worked_this_year = False
        self._pending_billing = None
        self._pending_bonus_income = 0.0
        self._director_quarters_this_year = 0
        self._actor_quarters_this_year = 0
        return resolved_films

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
