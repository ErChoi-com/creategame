"""Shared constants for the one-off report scripts under simulation/ (_full_data_report.py,
_quality_report.py, _smart_report.py, _report_sim.py, _director_report.py). These scripts are
headless policy runners, not the engine — Session takes an arbitrary scene-position dict at
play_scene() time, so this is purely a caller-side default, not something the engine enforces.
"""
from __future__ import annotations

# §5.6 v20 — "Match it" (WITH) on every dial, every scene, was maximizing craft_contribution while
# quietly crushing Spotlight (WITH gives the lowest for_you of any position, 0.5, on every dial) —
# and Spotlight carries more than double the weight critic score does in delta_prestige (0.26 vs
# 0.11). Every sim policy that always picked WITH was silently sabotaging Prestige to near-zero
# regardless of film quality. Setup/resolution stay WITH (craft-safe, low cost); the turn — §5.6's
# own designated emotional peak, the scene resolve_shape's beat-weighting is centred on — spikes
# real personal spotlight on the two highest-payoff dials (Beneath: energy 2.5, volume 3.0, vs
# WITH's flat 0.5 on both) while leaving warmth/speed at WITH. Total scene cost is 2 (Beneath costs
# 1/dial), well under a typical contrast budget (craft+command)/28 at anything but very low
# attributes — a real, bounded trade, not a blind maximization of one stat at the total expense of
# the other.
#
# Any new report script should import this rather than redefining its own copy — a fresh flat-WITH
# copy silently regresses Prestige back to 0 with no error to catch it.
SCENE_POSITIONS = (
    {"energy": "with", "volume": "with", "warmth": "with", "speed": "with"},
    {"energy": "beneath", "volume": "beneath", "warmth": "beneath", "speed": "beneath"},
    {"energy": "with", "volume": "with", "warmth": "with", "speed": "with"},
)
