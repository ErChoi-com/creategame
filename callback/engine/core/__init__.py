"""Generic, career-agnostic abstractions. Nothing in this package knows what an "actor" is.

A future director or studio engine reuses this package the same way callback.engine.actor does —
that reuse is the point: design/part-03-design-overview.md §3.3 requires one Standing model, one
Legibility engine, one Rolodex, one calendar shared across every career. meters.StandingModel and
pipeline.Stage are what make that a property of the code, not just a rule stated in prose.
"""
