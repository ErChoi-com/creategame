"""design/part-06-leverage.md §6.2 — Favours: countable debts specific people owe you.

A ledger keyed by npc_id (favours die with the person, per §6.2 — deleting an entry when an NPC
goes to Legacy/Severed is the caller's job, not this module's, since that's a Rolodex-side event).
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

RECOMMEND_FOR_JOB_THEY_GET = 2
ROSTER_FAVOUR_COST = 2
MENTOR_FAVOUR_COST = 1
BROKER_RECONCILIATION_COST = 2
BROKER_RECONCILIATION_PAYOUT = 3  # both parties owe you this many afterward


@dataclass(frozen=True)
class FavourLedger:
    owed: dict[str, int] = field(default_factory=dict)

    def balance(self, npc_id: str) -> int:
        return self.owed.get(npc_id, 0)

    def credit(self, npc_id: str, amount: int) -> "FavourLedger":
        owed = dict(self.owed)
        owed[npc_id] = owed.get(npc_id, 0) + amount
        return replace(self, owed=owed)

    def spend(self, npc_id: str, amount: int) -> "FavourLedger":
        if self.balance(npc_id) < amount:
            raise ValueError(f"insufficient favours owed by {npc_id}: have {self.balance(npc_id)}, need {amount}")
        return self.credit(npc_id, -amount)

    def can_spend(self, npc_id: str, amount: int) -> bool:
        return self.balance(npc_id) >= amount

    def clear(self, npc_id: str) -> "FavourLedger":
        """Favours die with the person — called when an NPC's relationship state becomes
        Legacy or Severed (rolodex.npc.LEGACY_STATE / SEVERED)."""
        owed = dict(self.owed)
        owed.pop(npc_id, None)
        return replace(self, owed=owed)
