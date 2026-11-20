"""Integrates every system built so far into one playable state: the actor's core loop
(simulation/career.py) plus the Rolodex, Leverage, Life layer, Guild, and the background
industry's genre cycle — the full loop simulation/cli.py drives interactively.

Kept separate from simulation/career.py (which stays a tested, minimal actor-only loop) rather
than rewriting it in place — this module composes those tested pieces instead of duplicating them.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field, replace

from callback.engine.actor.aging import apply_look_curve, role_volume_multiplier
from callback.engine.actor.offers import Role, is_offered_non_union, lane_for_role, sample_role, utility
from callback.engine.actor.series import aggregate_season
from callback.engine.actor.standing import (
    AFFECTION_DECAY, HEAT_KEEP, NOTORIETY_DECAY, PRESTIGE_DECAY,
    delta_affection, delta_heat, delta_prestige, standing_score,
)
from callback.engine.leverage.catalogue import LeverageState, new_leverage_state
from callback.engine.leverage.multi_picture_deal import MultiPictureDeal
from callback.engine.life.family import FamilyState
from callback.engine.life.health import HealthState
from callback.engine.life.money import MoneyState
from callback.engine.life.obituary import DeclinedRoleRecord, Obituary, generate_obituary
from callback.engine.life.state import LifeState, advance_year as advance_life_year
from callback.engine.core.util import clamp
from callback.engine.rolodex.casting import resolve_declined_role
from callback.engine.rolodex.rolodex import Rolodex, new_rolodex, recompute_tracked, register_contact
from callback.engine.simulation.career import ActorState, BILLING_WEIGHT, ProjectResult, new_actor, simulate_project
from callback.engine.simulation._adaptations import maybe_attach_adaptation
from callback.engine.leverage.merchandising import annual_royalty_payout
from callback.engine.simulation._franchises import (
    advance_franchises_without_you,
    apply_exit,
    decay_dormant_franchises,
    decline_continuation_probability,
    exit_notoriety_delta,
    director_continuity_bonus,
    franchise_audience_bonus,
    maybe_attach_franchise,
    resolve_reboots,
    studio_protectiveness,
    update_franchise_after_project,
)
from callback.engine.simulation._director import DirectorState, decay_director_standing
from callback.engine.simulation._relationships import director_skill_bonus_from_trust, update_relationship
from callback.engine.world.genre_cycle import accumulate_heat, decay_all
from callback.engine.world.genre_cycle import genre_demand as world_genre_demand
from callback.engine.world.guild import GuildState, add_residual_stream
from callback.engine.world.guild import advance_year as advance_guild_year
from callback.engine.world.strikes import StrikeState, advance_grievance

# Known gap: actor/offers.py's non-union-substitution check (§4.0) already reads union_credits
# directly rather than going through world.guild.is_eligible() — the two are consistent (both use
# the 3-credit threshold) but not literally wired together. Full guild membership gating of which
# roles even appear is a follow-up, not attempted in this pass.

CONTACT_CHANCE_ON_PROJECT = 0.6  # a project's costar is drawn from your Rolodex this often


@dataclass(frozen=True)
class FullState:
    actor: ActorState
    rolodex: Rolodex
    leverage: LeverageState
    life: LifeState
    guild: GuildState
    strikes: StrikeState
    genre_heat: dict[str, float] = field(default_factory=dict)
    filmography: tuple[ProjectResult, ...] = ()
    declined: tuple[DeclinedRoleRecord, ...] = ()
    franchises: dict = field(default_factory=dict)  # franchise_id -> simulation._franchises.FranchiseEntry
    retired_franchises: dict = field(default_factory=dict)  # franchise_id -> FranchiseEntry — released
    # (simulation._franchises.decay_dormant_franchises) but archived, not discarded, so a reboot
    # (simulation._franchises.resolve_reboots) has something real to roll against later.
    director: DirectorState | None = None  # None until the player crosses into a directing career
    studio_relations: dict = field(default_factory=dict)  # studio_id -> simulation._relationships.Relationship
    director_relations: dict = field(default_factory=dict)  # npc_id -> simulation._relationships.Relationship (requested directors only)
    multi_picture_deal: MultiPictureDeal | None = None  # None until the actor signs one (leverage.multi_picture_deal)
    merchandising_deals: tuple = ()  # leverage.merchandising.MerchandisingDeal — real, ongoing
    # royalty streams the actor has negotiated, resolved once a year in advance_between_years


def new_full_state(rng: random.Random, start_age: int = 22) -> FullState:
    return FullState(
        actor=new_actor(start_age),
        rolodex=recompute_tracked(new_rolodex(rng), current_year=0),
        leverage=new_leverage_state(),
        life=LifeState(health=HealthState(), family=FamilyState(), money=MoneyState()),
        guild=GuildState(),
        strikes=StrikeState(),
    )


def current_year(state: FullState) -> int:
    return state.actor.age  # a simple proxy — the CLI reports it as a calendar year offset


# §4.9's own dot-density ageism table (actor.aging.role_volume_multiplier) was fully written and
# fully documented but never actually consumed anywhere — an 80-year-old actor got exactly as many
# "romantic lead" listings as a 25-year-old. Wired in here for the first time: a role in one of the
# table's three named lanes only survives to the board with real, age-dependent probability.
# Animation ignores this filter entirely (see offers.Role.is_animation's own docstring) — the
# audience never sees your face, so the two things the table is actually measuring (how bankable
# you read on screen at this age) don't apply. Exhausting every reroll at a lane the table has
# genuinely zeroed out (e.g. ingenue_romantic past 48) resolves to a real animated offer instead of
# either an infinite loop or a role the table said shouldn't exist — the honest in-fiction answer
# to "you keep not landing that kind of part anymore."
ROLE_VOLUME_MAX_REROLLS = 4


def offer_this_year(state: FullState, rng: random.Random) -> Role:
    # The fee this listing settles on is a real negotiation, not a blind roll: how big a name the
    # actor already is (standing_score/100) is their actual leverage going in.
    leverage = standing_score(state.actor.standing) / 100.0
    role = sample_role(rng, actor_leverage=leverage)
    for _ in range(ROLE_VOLUME_MAX_REROLLS):
        if role.is_animation:
            break
        lane = lane_for_role(role)
        if lane is None or rng.random() < role_volume_multiplier(state.actor.age, lane):
            break
        role = sample_role(rng, actor_leverage=leverage)
    else:
        role = replace(role, is_animation=True)
    if role.union and is_offered_non_union(state.actor.union_credits, rng):
        role = replace(role, union=False, budget_for_role=role.budget_for_role / 3.0)
    role = maybe_attach_franchise(role, state.franchises, current_year(state), rng)
    role = maybe_attach_adaptation(role, rng)
    return role


def utility_for(state: FullState, role: Role) -> float:
    quote_value = state.actor.quote_value()
    return utility(state.actor.attrs, state.actor.persona, state.actor.standing, role, state.actor.age, quote_value)


def director_terms_for(rolodex: Rolodex, npc_id: str) -> tuple[float, float, float]:
    """A requested (Rolodex-tracked) director's own Standing, read as the three terms
    simulate_project's director_override wants — the same "no second stat block for NPCs"
    reuse §10.0 and director/skill.py's docstring already establish."""
    npc = rolodex.npcs[npc_id]
    if npc.standing is None:
        return 55.0, 55.0, 50.0
    return npc.standing["prestige"], npc.standing["heat"], npc.standing["prestige"]


def accept_and_play(
    state: FullState,
    role: Role,
    prep_choice: str,
    scene_choices: tuple[dict[str, str], dict[str, str], dict[str, str]],
    rng: random.Random,
    release_strategy: str | None = None,
    script_note=None,
    orientation_npc_id: str | None = None,
    orientation_effect=None,
    requested_director_npc_id: str | None = None,
    streaming_multiplier_override: float | None = None,
    streaming_bid_selector=None,
    festival_bid_selector=None,
    studio_trust: float = 50.0,
    requested_marketing_push: bool = False,
    palette=None,
    requested_rating_stance: str | None = None,
) -> tuple[FullState, ProjectResult]:
    """script_note: core.script_notes.ScriptNoteEffect, from a Session-level script-approval
    push. orientation_npc_id + orientation_effect: the tracked co-star this project centres on
    and positions.generosity()/upstaging()'s resulting ModifierResult. requested_director_npc_id:
    a tracked Rolodex director pulled onto the project in place of the usual random NPC sample —
    the caller (Session) is responsible for having already spent the favour this costs.
    streaming_multiplier_override: the specific competing streaming buyer's own terms
    (simulation._relationships-style — a real choice among multiple bidders, not just the
    financing studio's own default), in place of that studio's own streaming_multiplier_delta.
    festival_bid_selector: simulation.career.resolve_release_schedule's own festival acquisition
    bid-picker, threaded straight through — see that function's docstring for the bid shape.
    studio_trust/requested_marketing_push: fed straight to studios.decide_marketing_spend().
    palette: a pre-generated actor.palette.Palette (Session generates one at accept() time so a
    rating preview is stable and knowable before the shoot — §5.19's RatingScore is fixed the
    moment the palette exists, untouched by prep/the shoot/script notes). requested_rating_stance:
    the player's real "cut for rating" request, only ever consulted on a genuine borderline film
    (rating.near_boundary) — fed straight to resolve_rating() inside simulate_project."""
    # §9.3's GenreHeat, accumulated from every resolved film (yours and the background
    # industry's, §10.0) feeds real GenreDemand back into this project's own box office —
    # a hot genre isn't just trades-digest flavor, it changes what your film actually earns.
    demand = world_genre_demand(state.genre_heat, role.genre)
    director_override = None
    if requested_director_npc_id is not None:
        d_skill, d_command, d_prestige = director_terms_for(state.rolodex, requested_director_npc_id)
        # a director returning to their own franchise reads as investment, mechanically —
        # simulation._franchises.director_continuity_bonus, not just a flavor line. Stacks with
        # simulation._relationships' general "you've made money together before" trust bonus —
        # two different, real reasons a returning director reads sharper.
        continuity = director_continuity_bonus(role, state.franchises, requested_director_npc_id)
        trust_bonus = director_skill_bonus_from_trust(state.director_relations, requested_director_npc_id)
        d_skill = clamp(d_skill + continuity + trust_bonus, 0.0, 100.0)
        director_override = (d_skill, d_command, d_prestige)

    rating_kwargs = {} if requested_rating_stance is None else {"requested_rating_stance": requested_rating_stance}
    existing_franchise = state.franchises.get(role.franchise_id) if role.franchise_id else None
    new_actor_state, result = simulate_project(
        state.actor, role, prep_choice, scene_choices, rng,
        palette=palette,
        genre_demand_override=demand, release_strategy=release_strategy,
        script_note=script_note, orientation_effect=orientation_effect, director_override=director_override,
        franchise_audience_bonus=franchise_audience_bonus(role, state.franchises, current_year(state)),
        franchise_protectiveness=studio_protectiveness(existing_franchise) if existing_franchise else 0.0,
        streaming_multiplier_override=streaming_multiplier_override,
        streaming_bid_selector=streaming_bid_selector,
        festival_bid_selector=festival_bid_selector,
        studio_trust=studio_trust, requested_marketing_push=requested_marketing_push,
        **rating_kwargs,
    )

    franchises = update_franchise_after_project(
        state.franchises, role, result.spotlight, result.audience_score,
        new_actor_state.standing, current_year(state), requested_director_npc_id,
    )

    rolodex = state.rolodex
    costar_id = orientation_npc_id
    if costar_id is None and rng.random() < CONTACT_CHANCE_ON_PROJECT and rolodex.tracked_ids:
        costar_id = rng.choice(rolodex.tracked_ids)
    if costar_id is not None:
        rolodex = register_contact(rolodex, costar_id, current_year(state), shared_project=True)
        if result.npc_affinity_delta:
            from callback.engine.rolodex.rolodex import apply_affinity_grudge
            rolodex = apply_affinity_grudge(rolodex, costar_id, affinity_delta=result.npc_affinity_delta)

    leverage = state.leverage
    if result.favour_gain and costar_id is not None:
        leverage = replace(leverage, favours=leverage.favours.credit(costar_id, int(result.favour_gain)))

    guild = add_residual_stream(state.guild, result.roi, role.film_budget_millions)
    genre_heat = accumulate_heat(state.genre_heat, role.genre, result.roi)

    # The studio that financed this film remembers how it turned out, and so does a director you
    # specifically asked for — both real, both feeding straight back into future casting/skill
    # numbers rather than sitting as an inert P&L ledger nobody reads. net_profit is a real
    # gross-minus-budget reading, so this needs the film's actual production budget, not your fee.
    studio_relations = update_relationship(state.studio_relations, role.studio, role.film_budget_millions, result.roi, result.gross)
    director_relations = state.director_relations
    if requested_director_npc_id is not None:
        director_relations = update_relationship(
            director_relations, requested_director_npc_id, role.film_budget_millions, result.roi, result.gross,
        )

    new_state = replace(
        state, actor=new_actor_state, rolodex=rolodex, leverage=leverage, guild=guild,
        genre_heat=genre_heat, franchises=franchises, filmography=(*state.filmography, result),
        studio_relations=studio_relations, director_relations=director_relations,
    )
    return new_state, result


def accept_and_play_season(
    state: FullState,
    role: Role,
    prep_choice: str,
    premiere_scenes: tuple[dict[str, str], dict[str, str], dict[str, str]],
    finale_scenes: tuple[dict[str, str], dict[str, str], dict[str, str]],
    rng: random.Random,
    orientation_npc_id: str | None = None,
    orientation_effect=None,
    studio_trust: float = 50.0,
    requested_marketing_push: bool = False,
    requested_rating_stance: str | None = None,
) -> tuple[FullState, ProjectResult, float | None, dict]:
    """design/part-05 §5.18 — the season-level equivalent of accept_and_play. role.n_episodes/
    role.project_type=="series" is the caller's (Session's) responsibility to have set; this
    function doesn't re-derive them.

    No release_strategy here, deliberately — unlike a film, a season's distribution isn't a
    separate decision layered on top of financing: whichever studio/platform financed it
    (role.studio, already fixed at offer time) IS how it reaches an audience. Money comes from
    series.aggregate_season's own license_value (a ratings-adjusted license fee off the season's
    budget), not box-office gross/opening/legs — reusing that theatrical-distribution machinery for
    something that was never distributed that way was the bug this rewrite fixes. simulate_project
    is still called with release_strategy=None for both episodes purely for its real quality
    (critic/audience/spotlight/craft_contribution) resolution — resolve_release_schedule (and so
    quality_adjusted_bids/apply_release_strategy) never runs for a season at all.

    The premiere and finale are each resolved through the exact same simulate_project pipeline a
    standalone film uses — but against a *scratch* copy of the actor's own state, since a season
    commits exactly one Standing update off the season's own aggregate numbers (series.
    aggregate_season), not two separate per-episode ones. A deliberate, named scope cut this pass:
    prep_choice still shapes both episodes' own craft_contribution/spotlight (and so the season
    aggregate) through the normal shoot resolution, but the actor's own Craft/Resilience/Persona
    self-improvement from prep (ordinarily applied once per project in resolve_standing_update)
    isn't applied for a season — a real, bounded follow-up, not attempted here.

    Returns (new_state, result, renewal_chance, retention_summary) — result is a real ProjectResult
    (season aggregate numbers standing in for a single film's own; result.gross carries the
    season's license_value, not box-office receipts — see the module note above), filed into
    filmography exactly like a film so obituary/CLI/award code needs no special-casing.
    renewal_chance is None unless role.series_renewable, in which case it's series.
    renewal_probability()'s own output — the caller (Session) rolls it and decides whether to spin
    up next year's guaranteed-return listing. retention_summary is always real (final_retention_pct,
    average_retention_pct) regardless of renewability — the audience-retention read that's actually
    native to television, not the ROI framing borrowed from film."""
    n_episodes = role.n_episodes or 4
    demand = world_genre_demand(state.genre_heat, role.genre)
    per_episode_budget = role.film_budget_millions / max(1, n_episodes)
    episode_role = replace(role, film_budget_millions=per_episode_budget)
    rating_kwargs = {} if requested_rating_stance is None else {"requested_rating_stance": requested_rating_stance}

    _, premiere = simulate_project(
        state.actor, episode_role, prep_choice, premiere_scenes, rng,
        genre_demand_override=demand, release_strategy=None,
        orientation_effect=orientation_effect,
        studio_trust=studio_trust, requested_marketing_push=requested_marketing_push, **rating_kwargs,
    )
    _, finale = simulate_project(
        state.actor, episode_role, prep_choice, finale_scenes, rng,
        genre_demand_override=demand, release_strategy=None,
        orientation_effect=orientation_effect,
        studio_trust=studio_trust, requested_marketing_push=requested_marketing_push, **rating_kwargs,
    )
    agg = aggregate_season(
        premiere.spotlight, finale.spotlight,
        premiere.craft_contribution, finale.craft_contribution,
        premiere.film_critic_score, finale.film_critic_score,
        premiere.audience_score, finale.audience_score,
        premiere.budget, finale.budget,
        premiere.marketing, finale.marketing,
        n_episodes,
    )

    # license_value_multiplier is already centred at 1.0 for exactly-average ratings, the same
    # semantics an ROI reading needs (1.0 = broke even against the license the studio committed
    # to); license_value/season_budget recovers that multiplier exactly.
    season_roi = agg.license_value / agg.season_budget if agg.season_budget > 0 else 0.0
    bw = BILLING_WEIGHT[role.billing]
    heat_delta = delta_heat(bw, state.actor.credits, agg.season_budget, season_roi, agg.season_audience)
    prestige_delta = delta_prestige(bw, state.actor.credits, agg.season_critic, agg.season_notices)
    affection_delta = delta_affection(bw, state.actor.credits, agg.season_budget, agg.season_audience)

    standing = state.actor.standing.copy()
    standing.add("heat", heat_delta)
    standing.add("prestige", prestige_delta)
    standing.add("affection", affection_delta)
    new_actor_state = replace(state.actor, standing=standing, credits=state.actor.credits + 1)

    # Both real, played episodes build the relationship — a season with a costar across the whole
    # run earns more than either one scene would alone, the same "more played time together"
    # reading a film's own single npc_affinity_delta/favour_gain already carries.
    npc_affinity_delta = premiere.npc_affinity_delta + finale.npc_affinity_delta
    favour_gain = premiere.favour_gain + finale.favour_gain

    result = ProjectResult(
        role=role, cast_via="project",
        spotlight=agg.season_notices, craft_contribution=agg.season_ensemble, performance=agg.season_notices,
        project_quality=agg.season_ensemble, film_critic_score=agg.season_critic, audience_score=agg.season_audience,
        roi=season_roi, budget=agg.season_budget, marketing=agg.season_marketing,
        gross=agg.license_value,  # the season's real money figure — a license fee, not box office
        opening=0.0, legs=1.0, release_strategy="series",  # theatrical-only fields; series has none
        heat_delta=heat_delta, prestige_delta=prestige_delta, affection_delta=affection_delta,
        npc_affinity_delta=npc_affinity_delta, favour_gain=favour_gain,
        studio_id=role.studio,
        marketing_push_requested=finale.marketing_push_requested, marketing_push_honored=finale.marketing_push_honored,
        # §5.19 — the finale is the real, played rating decision for the whole season (the same
        # "the finale is the number that matters" reasoning renewal already applies), not a second
        # rating system for a season.
        rating_band=finale.rating_band, rating_cut_available=finale.rating_cut_available,
        rating_stance_requested=finale.rating_stance_requested, rating_stance_applied=finale.rating_stance_applied,
        rating_cut_forced=finale.rating_cut_forced, rating_studio_pressure=finale.rating_studio_pressure,
        break_even=agg.season_budget,
    )

    renewal_chance = None
    if role.series_renewable:
        renewal_chance = agg.renewal_chance

    # The one genuinely TV-native read this whole feature computes — how much of the premiere's
    # own audience was still watching by the finale, and on average across the run. Not exposed
    # per-episode (nobody needs a 13-point curve to read at a glance); final_retention_pct is
    # exactly the number renewal_probability itself keys off, so "why was this renewed or not"
    # stays legible from real data instead of an opaque probability.
    retention_summary = {
        "final_retention_pct": round(agg.retention[-1] * 100.0, 1),
        "average_retention_pct": round(100.0 * sum(agg.retention) / len(agg.retention), 1),
    }

    rolodex = state.rolodex
    costar_id = orientation_npc_id
    if costar_id is None and rng.random() < CONTACT_CHANCE_ON_PROJECT and rolodex.tracked_ids:
        costar_id = rng.choice(rolodex.tracked_ids)
    if costar_id is not None:
        rolodex = register_contact(rolodex, costar_id, current_year(state), shared_project=True)
        if result.npc_affinity_delta:
            from callback.engine.rolodex.rolodex import apply_affinity_grudge
            rolodex = apply_affinity_grudge(rolodex, costar_id, affinity_delta=result.npc_affinity_delta)

    leverage = state.leverage
    if result.favour_gain and costar_id is not None:
        leverage = replace(leverage, favours=leverage.favours.credit(costar_id, int(result.favour_gain)))

    guild = add_residual_stream(state.guild, result.roi, agg.season_budget)
    genre_heat = accumulate_heat(state.genre_heat, role.genre, result.roi)
    studio_relations = update_relationship(state.studio_relations, role.studio, agg.season_budget, result.roi, result.gross)

    new_state = replace(
        state, actor=new_actor_state, rolodex=rolodex, leverage=leverage, guild=guild, genre_heat=genre_heat,
        filmography=(*state.filmography, result), studio_relations=studio_relations,
    )
    return new_state, result, renewal_chance, retention_summary


def decline_and_resolve(state: FullState, role: Role, rng: random.Random) -> FullState:
    demand = world_genre_demand(state.genre_heat, role.genre)
    # Blacklist/Recommend (design/part-06 §6.6) were previously implemented in three places —
    # casting.py accepted them, catalogue.py stored them — but never actually connected: this
    # call is where that connection was missing. Without it, blacklisting or recommending
    # someone had zero effect on who ever got cast.
    rolodex, cast_result = resolve_declined_role(
        role, state.rolodex, current_year(state), rng, genre_demand_override=demand,
        blacklisted=state.leverage.blacklisted, recommended=state.leverage.recommended,
    )
    genre_heat = accumulate_heat(state.genre_heat, role.genre, cast_result.reception.roi)
    declined = (*state.declined, DeclinedRoleRecord(role_genre=role.genre, year=current_year(state), result=cast_result))

    franchises = state.franchises
    merchandising_deals = state.merchandising_deals
    standing = state.actor.standing
    existing = state.franchises.get(role.franchise_id) if role.franchise_id else None
    # Declining isn't just a solo pass — a sequel to a franchise you already lead can proceed
    # without you, the same real "the studio owns the property" logic a lost holdout already
    # resolves through apply_exit. A brand-new (never-yet-cast) franchise offer has nothing to
    # recast out of, so this only ever fires on an existing entry you were still leading.
    if existing is not None and existing.you_are_current_lead:
        protectiveness = studio_protectiveness(existing)
        if rng.random() < decline_continuation_probability(protectiveness):
            exited = apply_exit(existing, current_year(state), rng)
            franchises = {**franchises, role.franchise_id: exited}
            merchandising_deals = tuple(d for d in merchandising_deals if d.franchise_id != role.franchise_id)
            standing = standing.copy()
            standing.add("notoriety", exit_notoriety_delta(exited.exit_type, existing.installments_starred, rng))

    return replace(
        state, rolodex=rolodex, genre_heat=genre_heat, declined=declined,
        franchises=franchises, merchandising_deals=merchandising_deals,
        actor=replace(state.actor, standing=standing),
    )


def advance_between_years(
    state: FullState, rng: random.Random, worked_this_year: bool, billing: str | None = None, bonus_income: float = 0.0,
) -> FullState:
    """End-of-year housekeeping. simulate_project() (called from accept_and_play) resolves a
    single project's Standing *deltas* but — unlike simulation/career.py's own simulate_year —
    does not age the actor or apply Standing's yearly decay; those are exactly this function's
    job, run once per year regardless of whether a project was played. Also: life-layer advance,
    guild bookkeeping, genre-heat decay, Rolodex re-ranking, strikes.

    bonus_income: a negotiated box-office bonus (leverage/approvals.box_office_bonus_earned) —
    real money on top of the year's quote, credited to net worth the same as any other income, but
    kept separate through to life/money.py's own windfall handling — a one-time bonus shouldn't
    ratchet the lifestyle floor the same way a sustained acting quote does (see that module's own
    note). Merchandising royalties (leverage/merchandising.py) are folded into that same windfall
    bucket rather than a third income category — an ongoing stream is still irregular year to year
    (it rides a franchise's own indispensability, which can spike on a reboot or fade to zero), the
    same real-but-not-a-salary shape a box-office bonus already has."""
    active_franchises, newly_retired = decay_dormant_franchises(state.franchises, current_year(state))
    # Any franchise the player was recast out of keeps moving off-screen — sequeled, cast, and
    # released without them, the same way the background industry's own genre cycle (world/
    # genre_cycle.py) already runs independent of anything the player personally does.
    active_franchises = advance_franchises_without_you(active_franchises, current_year(state), rng)
    retired_pool = {**state.retired_franchises, **newly_retired}
    still_retired, revived = resolve_reboots(retired_pool, current_year(state), rng)
    franchises = {**active_franchises, **revived}

    merch_income = sum(
        annual_royalty_payout(deal.royalty_share, franchises[deal.franchise_id].indispensability)
        for deal in state.merchandising_deals if deal.franchise_id in franchises
    )

    gross_income = state.actor.quote_value() if worked_this_year else 0.0
    life, life_deltas = advance_life_year(
        state.life, rng, gross_income, worked_this_year, age=state.actor.age,
        windfall_income_millions=bonus_income + merch_income,
    )

    standing = state.actor.standing.copy()
    for meter, delta in life_deltas.items():
        if meter in standing.meters:
            standing.add(meter, delta)
    heat_tier = billing if (worked_this_year and billing) else "idle"
    standing.decay({
        "heat": HEAT_KEEP.get(heat_tier, HEAT_KEEP["idle"]),
        "prestige": PRESTIGE_DECAY,
        "affection": AFFECTION_DECAY,
        "notoriety": NOTORIETY_DECAY,
    })

    new_age = state.actor.age + 1
    aged_attrs = state.actor.attrs.age_decay(new_age)
    aged_attrs = replace(aged_attrs, look=apply_look_curve(aged_attrs.look, new_age)).clamped()
    # §11.4's resilience floor (partner, children, close friends) was computed but never
    # actually applied anywhere — the whole point of a floor is that Resilience can't be pushed
    # below it by everything else this function does.
    floor = life.family.resilience_floor()
    if aged_attrs.resilience < floor:
        aged_attrs = replace(aged_attrs, resilience=floor).clamped()
    actor = replace(state.actor, standing=standing, age=new_age, attrs=aged_attrs)

    guild = advance_guild_year(state.guild, gross_income)
    genre_heat = decay_all(state.genre_heat)
    rolodex = recompute_tracked(state.rolodex, current_year(state))
    strikes = advance_grievance(state.strikes, rng)
    director = decay_director_standing(state.director) if state.director is not None else None

    return replace(state, actor=actor, life=life, guild=guild, genre_heat=genre_heat,
                   rolodex=rolodex, strikes=strikes, franchises=franchises,
                   retired_franchises=still_retired, director=director)


def obituary(state: FullState) -> Obituary:
    return generate_obituary(list(state.filmography), list(state.declined), state.rolodex)
