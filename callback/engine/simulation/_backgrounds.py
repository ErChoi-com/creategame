"""design/ux/01-principles-and-first-session.md's four backgrounds — pure data, used only by
simulation/session.py's character creation. Kept out of session.py itself to keep that file
readable as "the API," not "the API plus a content table."
"""
from __future__ import annotations

from callback.engine.actor.attributes import Attributes
from callback.engine.life.money import MoneyState

REGIONAL_STAGE_START_AGE = 33

# key -> (name, tagline, starting Attributes, starting MoneyState or None for the default)
BACKGROUND_TABLE = {
    "conservatory": ("Conservatory", "Trained. Broke. Unknown.",
                      Attributes(craft=62, instinct=45, presence=35, resilience=50), None),
    "discovered": ("Discovered", "A manager, momentum, and no technique yet.",
                   Attributes(craft=28, instinct=55, presence=70, resilience=45), None),
    "regional_stage": ("Regional stage", "Years of range. No union credits. Not young anymore.",
                        Attributes(craft=70, instinct=50, presence=45, resilience=55), None),
    "family_money": ("Family money", "The rent's solved. The room can tell.",
                      Attributes(craft=45, instinct=45, presence=35, resilience=35), MoneyState(net_worth=2.0)),
}
