"""Player-facing copy for actor/release.py's release strategies. Kept out of actor/release.py
itself (an engine module — internal keys only, per every other actor/ module's convention) and
out of simulation/session.py (kept lean) so the strings live in exactly one place.
"""
from __future__ import annotations

from callback.engine.actor.release import FESTIVAL, LIMITED, SHELVED, STREAMING, WIDE

RELEASE_LABELS = {
    WIDE: "Wide — full theatrical push",
    LIMITED: "Limited — platform release, word of mouth does the work",
    FESTIVAL: "Festival — you find out if anyone even buys it",
    STREAMING: "Streaming — a flat guaranteed payout, no upside",
    SHELVED: "Shelved — it doesn't come out at all",
}
