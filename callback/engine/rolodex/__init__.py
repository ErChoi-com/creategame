"""The Rolodex (design/part-04-the-actor.md §4.12) and its relationship layer
(design/part-10-the-world.md §10.0, design/ux/04-pull-systems.md).

Built on core/ (an NPC's own career-facing state reuses core.meters.StandingModel exactly the way
actor/standing.py does) and actor/ (an NPC's casting weight reuses actor.offers' Utility shape).
"""
