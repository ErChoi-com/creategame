# 03 — THE SEASON LOOP

This is `../design/part-03-design-overview.md` §3.4's core-loop diagram, rendered as screens. Seven
stops, and — matching §0.2's decision-budget table exactly — seven places the game is allowed to
push a prompt at the player in a given project's lifecycle: Accept/Decline, the Deal, Prep, three
on-set moments, and the season wrap. Everything else on every screen below is read-only or pull.

## 1. The Offer Board

**Purpose:** the only screen where the player decides what to work on. Everything downstream is a
consequence of this choice.

```
┌───────────────────────────────┐
│  THIS QUARTER'S OFFERS         │
├───────────────────────────────┤
│  ┌───────────────────────┐    │
│  │ THE LONG WINTER         │    │
│  │ Supporting · Drama       │    │
│  │ "A role that fits how    │    │
│  │  you've been reading      │    │
│  │  lately."                  │    │
│  │ $180K · 2 blocks           │    │
│  │  [ AUDITION ] [ DECLINE ]  │    │
│  └───────────────────────┘    │
│  ┌───────────────────────┐    │
│  │ ...next card             │    │
│  └───────────────────────┘    │
└───────────────────────────────┘
```

Two to seven cards (§4.4's `reach`), never more — a board that scrolls past a screen and a half is
already failing Rule 4. Each card shows the same five things and nothing else: title, billing +
genre, one sentence of *why this role reached you* (a plain-language read of Fit and Persona —
never the words "Fit" or "Legibility"), money, and the calendar cost in blocks against the same
dot-widget from §02. No card shows an audition-odds percentage; the game states outcomes, not
internals, the same rule §10.0 applies to NPC Agendas.

**Why this role reached you** is the line doing the most work on the card, and it's generated, not
static — three or four templates keyed to what actually drove the offer (Persona match, a Rolodex
relationship, pure Standing, a director's loyalty roster) so a player who's paying attention starts
reading their own Persona back through the phrasing over time, without ever seeing the vector.

**Audition** leads to a short resolved beat (not a mini-game — one card, a result, the same
attribution language as every other outcome in this document) rather than a second layer of
sub-decisions; auditioning is a path to a role, not a system unto itself. **Decline** is free,
instant, and — per §10.0 — quietly consequential in a way the game never shows the player at the
moment of declining. That silence is intentional: the payoff for a declined role lives in the
obituary (§11.8), not in a stat ticking down on this screen.

## 2. The Deal

**Purpose:** the one deal-terms decision §0.2 budgets, replacing the nine v3 asked for.

One screen, one real fork, framed as a trade rather than a form:

```
┌───────────────────────────────┐
│  THE LONG WINTER — the deal    │
├───────────────────────────────┤
│  ○ Take the money               │
│    $180K, standard billing       │
│                                   │
│  ○ Take less, get more say       │
│    $126K (−30%), script + co-star│
│    approval                       │
│                                   │
│         [ CONFIRM ]              │
└───────────────────────────────┘
```

Where approvals aren't available at all (Standing below §6.3's thresholds), the second option
doesn't render greyed-out with a lock icon — it simply isn't on the card, because a visibly locked
option a new player can't reach yet is a promise of complexity before it's earned, which is exactly
what Rule 3 (options narrow *and* widen on their own timeline) argues against foregrounding early.
Billing and backend-points variants fold into whichever of the two paths is live for this specific
offer; the screen never shows more than two live choices at once, even when the underlying deal
space (fee, billing, options, approvals, pay-or-play) is larger — the game picks which axis is the
interesting one for *this* offer and asks about that one.

## 3. Prep

**Purpose:** the two decisions §0.2 allots to preparation — setting the palette, and choosing how
you get there.

Two short screens, not one dense one, because they're different *kinds* of choice:

**3a. The palette.** Six dials (§5.3), each a slider between two plain-language poles ("Quiet ↔
Loud," not "Pace" or a number) — the player is composing what the film's finished shape should feel
like, before a frame is shot. This isn't the performance choice (that's the shoot, below); it's
intent. The screen shows the film's *own* leanings alongside the player's dial as a faint second
mark, so a player who wants to fight the film's grain can see exactly how far they're pushing.

**3b. Preparation.** Six methods (coach, research, physical transformation, dialect, a rehearsal
period, showing up cold) as a single row of cards, one pick, each with a one-line cost/benefit in
plain language ("Slower to start. Nothing rattles you once you're there.") rather than a stat
table. This is the last screen before the shoot, and it's deliberately the calm one — the shoot
itself is where the pace picks up.

## 4. The Shoot — three scenes

**Purpose:** §5.6's rework, in full — the shoot is not an event log, it's three real scenes the
player plays, structured as setup / turn / resolution and genre-shaped (a thriller's turn is a
confrontation; a comedy's is a falling-out; a horror's is the first kill — §5.6's own table).

Each scene is the same screen shape, three times, with a short **dailies** beat between them:

```
┌───────────────────────────────┐
│  SCENE 2 OF 3 — THE TURN        │
│  "She finds out."                │
├───────────────────────────────┤
│  How do you play it?             │
│                                   │
│   Match it     Hold back          │
│   Go big       Play against it    │
│                                   │
│  Contrast spent so far: ▓▓▓░░    │
└───────────────────────────────┘
```

The four positions are §5.5's own player-facing labels, never the internal With/Beneath/Beyond/
Against vocabulary. The contrast-budget bar is the *only* numeric-feeling element on this screen,
and it's deliberately abstract (a filled bar, not "4.2 / 6.0") — enough for the player to feel the
constraint tightening without turning it into an optimization target, the exact failure mode §5.5's
own v9 note describes the previous numeric version falling into.

**Between scenes: dailies.** A single short card, bounded and non-committal — a fragment of what
the room is saying, not a scorecard ("The DP keeps replaying take four.") — giving the player just
enough signal to adjust the next scene's read without ever stating the hidden Performance number.
This is §01 Rule 3 in action: the player's *own* read of their work narrows in confidence as Craft
and director-familiarity rise (§4.7's v9 note), and the dailies card's specificity should scale
with that same confidence — vague for a newcomer with a stranger director, sharper for a veteran
with a trusted collaborator.

After scene three, no result renders yet. The shoot ends on a held beat — a wrap card, a date, a
release window — and cuts to the hub. The performance number stays private until reception (below),
which is the entire point of §4.7's "you should be able to walk away convinced you were brilliant
and be wrong."

## 5. Post & Release

**Purpose:** the reveal, and the single most important application of the attribution rule (§01
Rule 2) in the whole game.

One screen, revealed in a fixed order so the causal chain reads top to bottom, never all at once:

```
┌───────────────────────────────┐
│  THE LONG WINTER — reception    │
├───────────────────────────────┤
│  Your work: strong               │
│  The edit: buried you            │
│  Critics: mixed                  │
│  Opening weekend: soft           │
├───────────────────────────────┤
│         [ SEE WHAT PEOPLE      │
│           ARE SAYING ]          │
└───────────────────────────────┘
```

Four lines, four bands (never raw scores — `YourNotices`, `FilmCriticScore`, `AudienceScore`, and
box-office all render through the same words-not-numbers pass as everything else, §05), and the
order is fixed because it's the order of *causes*: your performance came first, the edit acted on
it, critics reacted to the edited film, the audience reacted last. A player who reads this card top
to bottom is reading the causal chain whether or not they consciously register it as one.

Tapping through opens optional detail (actual review pull-quotes, the box-office number if the
player wants it, awards buzz if any) — pull, not push, and skippable entirely by a player who's
already gotten the four lines they came for. If the player earned **a seat in the edit** (§6.3),
one additional small card appears before the reveal, framed as a real but bounded choice — nudge
the cut slightly, or leave it — never framed as control over the outcome, because it isn't.

## 6. The Season

**Purpose:** the two decisions §0.2 reserves for the year's wider context — an awards campaign if
one applies, and Rolodex upkeep.

Not a screen so much as a short sequence of at-most-two cards, each independently optional to
engage with beyond a single tap:

- **Campaign**, if the year's work is buzz-eligible: a single strategic choice (push hard / stay
  quiet / target one category), framed exactly like the Deal — a trade, not a checklist.
- **A relationship moment**, at most one per year and only when it's earned (§04 covers the full
  Rolodex pull-surface; this is the rare *pushed* version — a Loyal collaborator's own crisis, per
  §10.0's budget-capped NPC-initiated events).

A year with neither renders nothing here at all — the season sequence is allowed to be empty, and
an empty season is not a screen the player has to click through to confirm is empty.

## 7. The Reckoning

**Purpose:** closing the year. Not a push — no decision lives here — but the one screen every year
guarantees, so the player always sees where the year left them before the calendar rolls forward.

A single short card: Standing's band-level change (*"Your name carries more weight than it did in
January"* — never a delta number), a one-line Persona note if it shifted meaningfully, and — only
when relevant — a life-layer note (health, money, family) in the same plain-language register as
everything else. Then the calendar dot fills, the quarter advances, and the hub is what's on screen
next. No progress bars, no year-end summary screen with charts — the Reckoning is a sentence, not a
report, because a 40-year career told through forty annual dashboards is the spreadsheet-management
failure mode §0.3 Rule 3 exists specifically to prevent.
