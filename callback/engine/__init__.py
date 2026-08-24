"""CALLBACK engine — the primary system and mechanics, implemented from ../docs/design/.

Layout (see ../docs and the plan this was built from):
    core/        generic, career-agnostic abstractions (Meter, StandingModel, the Stage protocol)
    actor/       the actor career's formulas, built only on core/
    simulation/  orchestration (career.py) and verification (verify.py) against Part 14's targets
"""
