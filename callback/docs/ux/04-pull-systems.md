# 04 — THE PULL SYSTEMS

Three tabs, reachable from the hub's bottom bar at all times, none of them ever auto-opened,
none of them ever badged with a number the way a notification inbox would be. §0.3 Rule 2b — pull
is free — is the reason these three screens can hold roughly forty leverage verbs, a living
Rolodex, and a running industry history without touching the ~15/year push budget at all. The UI's
job is to keep that promise visible: nothing in this file interrupts anything in §03.

## Rolodex

**Purpose:** the people, not the favours ledger — this is where `../design/part-10-the-world.md`
§10.0's relationship layer actually lives on screen.

A single scrollable list, eight named people pinned at the top (§4.12's tracked eight), a "people
you've worked with" section below for anyone with `sharedProjects ≥ 1` who hasn't risen into the
tracked eight. Each row shows a face, a name, their role (director / agent / co-star, etc.), and
**one relationship word** — never a number, never a percentage:

```
┌───────────────────────────────┐
│  ROLODEX                        │
├───────────────────────────────┤
│  [pic]  Dana Reyes                │
│         Director · Loyal          │
│  [pic]  Theo Marsh                │
│         Producer · Estranged      │
│  [pic]  Priya Okafor               │
│         Co-star · Familiar         │
└───────────────────────────────┘
```

The word is one of §10.0's own relationship-arc states (Stranger / Familiar / Ally / Rival / Loyal
/ Estranged / Legacy / Severed), rendered exactly as-is — these already read as plain English, so
this is the one place in the whole document where an internal state name and the player-facing word
are the same string, deliberately, because renaming a word that already works would just be
inventing a second vocabulary for no reason.

**Tapping a person** opens their detail screen: a short relationship history in prose (drawn from
shared projects and flagged moments — *"You held the line together during the '39 strike."*), and a
row of interaction actions pulled straight from §10.0's table — **Check in**, **Show up for them**,
**Read their Agenda**, **Vouch for them** — each rendered as a single tappable action with a short
description, never a cost breakdown. Their Agenda is never shown as a label ("Legacy," "Ascent");
per §10.0's own rule it's discoverable only through the pattern of what they've asked for over time,
so the detail screen's history text is doing real interpretive work here, not just flavor —
a player who reads three years of "asked you to help her get the strange, unprofitable one made"
should be able to guess Legacy on their own, the way they'd read a real person.

**A dead or retired relationship (Legacy state)** stays in the list, greyed slightly, tappable only
to read the history — no actions render, because there's nothing left to do, only something to
remember. This is the screen the obituary (§03's closing note in a full career, §11.8) is quietly
building toward the entire game.

## Leverage

**Purpose:** the ~40-verb action catalogue (`../design/part-06-leverage.md` §6.6), organized so
forty options never feel like forty options at once.

Not a flat list — five collapsed sections matching §6.6's own grouping (**Get work that wasn't
offered you**, **Change a project you're on**, **Change your own standing**, **Change other
people**, **Change the market**), each collapsed to its section title until tapped open. This is
the single biggest UI decision in this document for keeping breadth from reading as clutter: a
player opens the one section relevant to what they're trying to do and never sees the other four.

```
┌───────────────────────────────┐
│  LEVERAGE                       │
├───────────────────────────────┤
│  ▸ Get work that wasn't offered │
│  ▸ Change a project you're on   │
│  ▾ Change your own standing     │
│     Disappear                    │
│     A season of theatre          │
│     Publicly turn down something │
│  ▸ Change other people          │
│  ▸ Change the market            │
└───────────────────────────────┘
```

Each verb, tapped, opens a single confirmation card — what it costs, what it does, in the same
plain-language register as everything else (never "Notoriety +12," always "people will notice, and
some of them will mind") — with an explicit confirm step, because every one of these forty actions
is a real, sometimes irreversible choice and none of them should be a misclick away.

**Availability, not visibility, gates these.** An action the player can't currently afford (not
enough favours, Standing too low) still appears in its section, dimmed, with the one-line reason
why — *"Requires Standing 65"* — rather than being hidden. This is the opposite choice from the
Deal screen in §03, deliberately: the Deal hides unavailable paths because it's a push screen and
clutter there costs a decision-budget slot; the Leverage screen is pull, has no such budget, and a
player exploring what's *coming* is part of what makes a forty-verb catalogue feel like a real
horizon instead of a random-access junk drawer.

**The holdout, and other franchise-specific verbs**, don't live in this flat catalogue at all —
per §6.5, they surface contextually, as a conversation prompt attached to the specific franchise
project when the option genuinely comes up (a contract about to lapse), never as a menu item a
player has to remember exists. `../design/`'s own note makes this explicit and the UI follows it
exactly: **"the holdout appears as a conversation with your agent when your option is up, not as a
menu item you might miss."**

## The trades

**Purpose:** §10.0's once-a-year digest — the cheapest, highest-return screen in this document,
because it's the only place the background industry (every film the player wasn't in) becomes
visible at all.

Five lines, once a year, never more, laid out as a simple scroll of short headlines rather than a
feed:

```
┌───────────────────────────────┐
│  THE TRADES — 2041              │
├───────────────────────────────┤
│  Horror's still climbing. Every  │
│  studio wants one.               │
│                                   │
│  "Late August" is the film        │
│  everyone's talking about.        │
│                                   │
│  Theo Marsh is out at Reliant.    │
│                                   │
│  A stunt record fell on          │
│  "Redline."                       │
│                                   │
│  Priya Okafor just won her        │
│  second festival in a row.        │
└───────────────────────────────┘
```

No line links anywhere or opens a detail screen — the trades are texture, not a database the player
is expected to investigate, matching §10.0's own framing exactly: *"the world doesn't need the
player to track it, it needs the player to be able to check in on it and find something has
genuinely moved."* A new digest replaces the old one entirely; there's no archive to scroll back
through, because the point isn't research, it's the feeling that a year passed somewhere the player
wasn't looking.

**A small unread indicator** — the only badge anywhere in this document's pull surfaces — marks a
fresh digest on the tab bar, and only the trades tab ever gets one. Rolodex and Leverage are
always-available menus with nothing to "catch up on"; the trades are the one pull screen with an
actual once-a-year cadence, so a light, dismissible signal that something changed is earned there
and nowhere else.
