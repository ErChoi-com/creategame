# CALLBACK — GAMEPLAY, UX & UI DESIGN
### A companion document: not what the systems compute, but what the player actually sees and does

The document in `../design/` specifies the systems — the formulas, the meters, the things that are
true underneath the game. It deliberately says almost nothing about screens, taps, layout, or copy.
That was the right call while the mechanics were still moving; it's the wrong state to ship in.
This document is the other half: **the exact sequence of screens a player moves through, what's on
each one, what they can touch, and what it says back to them.**

Nothing in here changes a formula. Where a screen shows a number, it's a number `../design/` already
defines. Where a screen hides a number and shows words instead, it's applying a rule `../design/`
already states (§15's "too many meters," §0.3's attribution rule) rather than inventing a new one.
This document's job is to make those rules concrete: which words, in which screen, in which order.

## Scope

**This covers the actor spine only** — character creation through a full season loop, the pull
systems (leverage, the Rolodex, the trades), and the visual/feedback language that ties them
together. That's Parts 0, 3, 4, 5, and 6 of the mechanics doc — the same scope Part 13's build plan
calls "a complete, shippable game" on its own (Phases 0–5). The director and studio layers reuse
every pattern established here (same calendar widget, same offer-board layout with a different
gatekeeper, same pull-menu shell) rather than inventing their own — exactly the way §3.3's one-spine
rule requires the *systems* to be shared, this document requires the *screens* to be shared too. A
UX pass for those layers is a follow-up, not a rewrite.

## Platform and posture

Portrait, one hand, short sessions — the same posture as the BitLife-style game this whole document
supersedes (`../design/part-01-bitlife-teardown.md`), because that posture is right; what BitLife
gets wrong is what fills the sessions, not the shape of them. Single-column screens, no dashboards,
no screen that requires scrolling to find the thing you came for. If a screen needs a legend to be
readable, the screen is wrong.

## Contents

0. [00 — This index](00-index.md)
1. [01 — Principles, and the first session](01-principles-and-first-session.md) — the four UX rules this document adds on top of `../design/`'s four design rules; character creation; the opening hour
2. [02 — Home and the calendar](02-home-and-calendar.md) — the hub screen, persistent chrome, how the player always knows where they are in the year
3. [03 — The season loop](03-the-season-loop.md) — Offer Board → The Deal → Prep → The Shoot → Post & Release → The Season → The Reckoning, screen by screen, the spine of every single play session
4. [04 — The pull systems](04-pull-systems.md) — Leverage, the Rolodex, the trades digest: everything the player goes looking for, and why none of it costs anything against the push budget
5. [05 — Visual language and feedback](05-visual-language-and-feedback.md) — how "shown as words, not numbers" actually renders; the attribution pattern; notification and pacing rules

## The one rule that generated most of this document

**§0.2's decision budget (~15–20 pushed prompts a year) is a UI constraint before it's anything
else.** A push is a screen that stops the player and waits for an answer. A pull is a screen the
player opened on their own. Count the push screens in this document and there are seven — Accept/
Decline, the Deal, Prep, three on-set moments, and the season wrap — matching §0.2's table exactly.
Everything else in here — the Rolodex, the leverage menu, the trades — is reachable, never required,
and that distinction is drawn in the layout itself: pull screens live behind a tab bar the game
never auto-opens; push screens are the only ones that can interrupt what the player was doing.
