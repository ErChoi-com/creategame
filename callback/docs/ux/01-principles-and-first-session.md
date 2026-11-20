# 01 — PRINCIPLES, AND THE FIRST SESSION

## The four UX rules

`../design/part-00-design-rules-and-cut-list.md` sets four rules for what a *system* is allowed to
be. These are the four rules for what a *screen* is allowed to be — the same document, read for
layout instead of formulas.

**1. A push screen ends with a choice, not a form.** If a screen's only job is to collect
information the game already has an obvious use for (confirm your name, review these terms, tap
next), it isn't a decision and it shouldn't cost one of the ~15 pushed prompts a year. Every push
screen in this document was checked against §0.1's Decision Test before it earned a place in
§03's loop: two options, both defensible, on screen.

**2. One glance tells you why.** §0.3's attribution rule — *"always show the causal chain"* — is a
UI requirement, not a writing tip. Every screen that reports an outcome (a review lands, an offer
falls through, an award is lost) shows the three or four things that produced it, in plain
language, without the player having to ask. If a player can be surprised by a result *and* unable
to explain it in the next five seconds, the screen failed, independent of whether the underlying
formula was right.

**3. Numbers are for the game; words are for the player.** §15's rule restricts numeric UI to four
meters — Heat, Prestige, Affection, Notoriety — and states everything else "as words." This
document is where that rule gets a shape: a stat never renders as `74`, it renders as the
qualitative band it falls in, and the band is written like something a person would actually say
("actors love working with her," not "Command: 84"). §05 specifies exactly how each hidden number
becomes a sentence.

**4. Nothing the player didn't choose to see shows up twice.** No screen re-asks a question another
screen already answered, and nothing decays visibly for lack of a tap (§0.3 Rule 1 — no upkeep).
Late-career screens have *fewer* elements than early-career ones, not more, mirroring §0.3 Rule 3 —
the offer board itself narrows in on-screen density as Persona sharpens (§02).

## First launch

**Screen 1 — the pitch, in one line.** No splash logo animation, no tutorial video. A single line
of text over a still frame (a soundstage, dark, one work light on): *"You do not control whether
the film is good."* Tap to continue. That sentence is the entire pitch (`../design/part-03-design-
overview.md` §3.1) and it's the first thing anyone sees, because it sets the expectation the whole
game is built to satisfy — the player is not here to win a slot machine, they're here to make
choices inside one.

**Screen 2 — background.** Four cards, one screen, no scrolling. Each card is a name, one
sentence of flavour, and two short stat lines — what you start with, what you're short of — pulled
directly from `../design/part-04-the-actor.md` §4.0's table:

```
┌─────────────────────────┐
│  CONSERVATORY            │
│  Trained. Broke. Unknown.│
│                           │
│  Starts with: real craft │
│  Short of: money,        │
│    connections, a face   │
│    anyone recognises     │
│                           │
│         [ CHOOSE ]       │
└─────────────────────────┘
```

Four of these, swipeable, none labelled "recommended" or "hard mode" — `../design/`'s own framing
is that none of the four backgrounds is ranked against the others, and the UI has to hold that
line as hard as the text does. No stat is shown as a raw number here either: "Craft 62" renders as
"real craft"; "Craft 28" renders as "has never had a lesson." The player is choosing a *story*,
not optimizing a build, and the screen should never make optimizing feel available.

**Screen 3 — Ambition.** Six cards, same shape, pulled from §0.4's table. Each is a single
sentence written as a want, not a metric: The Work reads *"You want to be undeniable, whether or
not anyone's watching."* The Prize reads *"You want the statue."* The screen states once, in small
type at the bottom, that this can change later and gates nothing — because the two things a new
player is most likely to misread about this screen are "is this permanent" and "is this locking me
out of something," and both answers are no.

**Screen 4 — the face, briefly.** A short appearance pass (hair, build, a handful of preset
looks) feeding `Look` — kept deliberately short, three taps, because character-appearance
customization is not a system this design invests in past the gate it needs to feed. No slider
reads as a number here either; the options are named ("striking," "approachable," "unusual") and
the player picks a read, not a value.

**Screen 5 — the name, and cut to the calendar.** One text field. On submit, no tutorial overlay —
the game cuts straight to the home screen (§02) with a single pushed prompt already waiting: the
player's first offer, non-union, exactly as §4.0 specifies. The opening hour's entire onboarding
budget is the four screens above; everything else is taught by the first three real decisions, not
by a wizard explaining them in advance.

## Why there's no tutorial mode

A separate walkthrough that explains the offer board before the player has an offer to evaluate is
the "form, not a choice" problem from Rule 1 applied to the first hour instead of a single screen.
Every mechanic a new player needs is small enough to be legible from context the first time it's
used — the offer board explains itself because the first offer is one card with three numbers a
new player already knows how to read (money, a schedule, "will this get me noticed"). Complexity is
introduced by the game's own structure (§0.3 Rule 3, run in reverse: options start narrow and open
up), not by a menu of explanations nobody asked for.

## The non-union first act, on screen

§4.0's mechanic — the first three credits are quietly non-union, a third the pay, easier to land —
needs exactly one piece of UI to read correctly: the offer card for a non-union role looks
identical to every other offer card, with one small tag (*"Non-union — your first few, don't worry
about it"*) instead of a warning. The game never frames this as a penalty on screen, because it
isn't one in the design — it's how a career starts. The moment the third union-eligible credit
lands, a single non-pushed toast confirms it (*"You're eligible for union work now"*) and the tag
disappears from every future card. No screen, no prompt, no decision spent — the player simply
notices the offers changed shape.
