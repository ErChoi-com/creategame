"""CLI verification harness — reproduces design/part-14-tuning-targets.md's §14.1 (reception
model) and §14.6 (creative decisions) checks against this engine, the same shape as the existing
(v8, stale) docs/callback-sim.py: run a check, print target vs. measured.

    python3 -m callback.engine.simulation.verify reception
    python3 -m callback.engine.simulation.verify creative
    python3 -m callback.engine.simulation.verify all

This exercises the actor/ Stages exactly as simulation/career.py composes them — no formulas are
reimplemented here, only sampled and measured.
"""
from __future__ import annotations

import math
import random
import statistics as st
import sys

from callback.engine.actor.attributes import Attributes
from callback.engine.actor.offers import sample_role
from callback.engine.actor.persona import GENRES, Persona
from callback.engine.actor.positions import contrast_budget
from callback.engine.actor.prep import PREP_OPTIONS, WING_IT
from callback.engine.actor.standing import new_standing_model
from callback.engine.core.util import clamp
from callback.engine.simulation.career import ActorState, default_scene_policy, simulate_project


def corr(xs: list[float], ys: list[float]) -> float:
    mx, my = st.mean(xs), st.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return num / den if den else 0.0


def _sample_actor(rng: random.Random) -> ActorState:
    attrs = Attributes(
        craft=clamp(rng.gauss(58, 20), 0, 100),
        instinct=clamp(rng.gauss(58, 20), 0, 100),
        presence=clamp(rng.gauss(58, 20), 0, 100),
        voice=clamp(rng.gauss(58, 20), 0, 100),
        physicality=clamp(rng.gauss(58, 20), 0, 100),
        look=clamp(rng.gauss(58, 20), 0, 100),
        resilience=clamp(rng.gauss(58, 20), 0, 100),
    )
    standing = new_standing_model(
        heat=rng.uniform(10, 70), prestige=rng.uniform(10, 70),
        affection=rng.uniform(10, 70), notoriety=rng.uniform(0, 40),
    )
    return ActorState(age=rng.randrange(20, 55), attrs=attrs, persona=Persona(),
                       standing=standing, credits=rng.randrange(0, 20))


def _one_project(rng: random.Random, genre: str | None = None):
    state = _sample_actor(rng)
    role = sample_role(rng)
    if genre is not None:
        from dataclasses import replace
        role = replace(role, genre=genre)
    scene_choices = default_scene_policy(rng)
    prep_choice = rng.choice([c for c in PREP_OPTIONS if c != WING_IT])
    _, result = simulate_project(state, role, prep_choice, scene_choices, rng)
    return result


def reception(n: int = 20000, seed: int = 3) -> None:
    print("=== §14.1 RECEPTION MODEL ===")
    rng = random.Random(seed)
    perf, fc, notices, aud, roi = [], [], [], [], []
    for _ in range(n):
        r = _one_project(rng)
        perf.append(r.performance)
        fc.append(r.film_critic_score)
        notices.append(r.notices)
        aud.append(r.audience_score)
        roi.append(r.roi)

    print(f"Performance   mean {st.mean(perf):6.1f}  sd {st.pstdev(perf):5.1f}")
    print(f"FilmCritic    mean {st.mean(fc):6.1f}  sd {st.pstdev(fc):5.1f}")
    print(f"Notices       mean {st.mean(notices):6.1f}  sd {st.pstdev(notices):5.1f}")
    print(f"AudienceScore mean {st.mean(aud):6.1f}  sd {st.pstdev(aud):5.1f}")
    print(f"ROI           median {st.median(roi):.2f}  profitable {100*sum(1 for x in roi if x>1)/len(roi):.0f}%")
    print()

    checks = [
        ("Performance <-> Notices", corr(perf, notices), (0.70, 0.80)),
        ("Performance <-> FilmCritic", corr(perf, fc), (0.40, 0.48)),
        ("Performance <-> ROI", corr(perf, roi), (0.20, 0.30)),
        ("FilmCritic <-> ROI", corr(fc, roi), (0.20, 0.30)),
        ("FilmCritic <-> Audience", corr(fc, aud), (0.40, 0.50)),
    ]
    for label, value, (lo, hi) in checks:
        ok = "OK " if lo <= value <= hi else "<<<"
        print(f"{ok} corr({label:26s}) = {value:5.2f}   target {lo:.2f}-{hi:.2f}")


def creative_decisions(n_per_genre: int = 4000, seed: int = 7) -> None:
    print("=== §14.6 CREATIVE DECISIONS ===")
    rng = random.Random(seed)

    print("\n-- corr(audience, critic) by genre --")
    orthogonal = 0
    for genre in GENRES:
        aud, crit = [], []
        for _ in range(n_per_genre):
            r = _one_project(rng, genre=genre)
            aud.append(r.audience_score)
            crit.append(r.film_critic_score)
        c = corr(aud, crit)
        if abs(c) < 0.15:
            orthogonal += 1
        print(f"  {genre:10s} corr = {c:+.2f}")
    print(f"  genres near-orthogonal (|corr|<0.15): {orthogonal}  (target >= 2)")

    print("\n-- contrast budget spread (Craft, DirectorCommand) -> budget --")
    for label, craft, command in [
        ("limited actor / no support", 30, 30),
        ("skilled / neutral director", 60, 60),
        ("skilled / director-with-them", 70, 84),
        ("great actor / director-with-them", 90, 84),
    ]:
        print(f"  {label:34s} budget = {contrast_budget(craft, command):.1f}")

    print("\n-- showiest allocation must NOT maximise Notices --")
    named_allocations = {
        "steady (mostly with)": ({"energy": "with", "volume": "with", "warmth": "with", "speed": "with"},) * 3,
        "shaped (one against)": (
            {"energy": "with", "volume": "with", "warmth": "with", "speed": "with"},
            {"energy": "against", "volume": "with", "warmth": "with", "speed": "with"},
            {"energy": "with", "volume": "with", "warmth": "with", "speed": "with"},
        ),
        "showy (against + beyond)": (
            {"energy": "against", "volume": "beyond", "warmth": "with", "speed": "with"},
            {"energy": "against", "volume": "with", "warmth": "beyond", "speed": "with"},
            {"energy": "with", "volume": "beyond", "warmth": "with", "speed": "against"},
        ),
    }
    means = {}
    for label, allocation in named_allocations.items():
        totals = []
        for _ in range(2000):
            state = _sample_actor(rng)
            role = sample_role(rng)
            _, result = simulate_project(state, role, "table_work", allocation, rng)
            totals.append(result.notices)
        means[label] = st.mean(totals)
        print(f"  {label:26s} mean Notices = {means[label]:6.1f}")
    ok = means["shaped (one against)"] > means["showy (against + beyond)"]
    print(f"  {'OK ' if ok else '<<<'} shaped > showy: {ok}")


def all_checks() -> None:
    reception()
    print()
    creative_decisions()


COMMANDS = {"reception": reception, "creative": creative_decisions, "all": all_checks}


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] not in COMMANDS:
        print(__doc__)
        return 1
    COMMANDS[argv[1]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
