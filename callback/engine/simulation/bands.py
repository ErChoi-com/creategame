"""design/ux/05-visual-language-and-feedback.md's "words-not-numbers" pass: every hidden score a
CLI (or any future UI) shows the player renders as a qualitative band, never a raw number.
"""
from __future__ import annotations


def band(value: float, thresholds: list[tuple[float, str]]) -> str:
    """thresholds: ascending list of (lower_bound, label). Returns the label of the highest
    bound the value clears."""
    label = thresholds[0][1]
    for lower, text in thresholds:
        if value >= lower:
            label = text
    return label


PERFORMANCE_BANDS = [
    (0, "a rough one"), (35, "uneven"), (50, "solid"), (65, "strong"), (80, "extraordinary"),
]
CRITIC_BANDS = [
    (0, "savaged"), (35, "cold"), (50, "mixed"), (65, "warm"), (80, "raves"),
]
AUDIENCE_BANDS = [
    (0, "nobody came"), (35, "soft"), (50, "steady"), (65, "a real draw"), (80, "a phenomenon"),
]
ROI_BANDS = [
    (0.0, "a loss"), (0.9, "close to even"), (1.3, "profitable"), (2.0, "a hit"), (3.0, "a runaway hit"),
]
STANDING_BANDS = [
    (0, "unknown"), (20, "working"), (40, "in-demand"), (60, "sought-after"), (80, "a star"),
]
RELATIONSHIP_BANDS = {
    "stranger": "someone you haven't really met",
    "familiar": "someone you know",
    "ally": "someone in your corner",
    "rival": "someone whose career keeps crossing yours",
    "loyal": "someone who'd cast you sight unseen",
    "estranged": "someone who isn't returning your calls",
    "legacy": "someone whose career is over now",
    "severed": "someone who will never work with you again",
}


def performance_band(v: float) -> str: return band(v, PERFORMANCE_BANDS)
def critic_band(v: float) -> str: return band(v, CRITIC_BANDS)
def audience_band(v: float) -> str: return band(v, AUDIENCE_BANDS)
def roi_band(v: float) -> str: return band(v, ROI_BANDS)
def standing_band(v: float) -> str: return band(v, STANDING_BANDS)
def relationship_band(state: str) -> str: return RELATIONSHIP_BANDS.get(state, state)
