# 02 — HOME AND THE CALENDAR

## The hub

One screen the player returns to between every pushed decision — never a menu they have to
navigate through, always the same layout, so "where am I" is never a question. Four regions, top to
bottom, none of them scrolling past a single screen height:

```
┌───────────────────────────────┐
│  [portrait]  Maya Okonkwo      │  ← identity strip: face, name, age,
│  32 · Working actor            │     one-line Standing read (§05)
├───────────────────────────────┤
│  ● ● ● ○   Q3, 2041            │  ← the calendar: four blocks, this
│  On set: "The Long Winter"     │     year's four quarters, what's
│                                 │     filling each one right now
├───────────────────────────────┤
│  [ what's happening card ]     │  ← exactly one card: the single
│                                 │     most relevant thing right now
├───────────────────────────────┤
│  Rolodex   Leverage   Trades   │  ← the pull tab bar (§04)
└───────────────────────────────┘
```

**The identity strip never shows a raw number.** "Working actor" is a Standing band, not a
Standing score — the same translation §05 defines for every hidden meter. Tapping the strip opens
a single detail screen with the actor's attributes as words (§4.1's gates and cores, described
qualitatively) and the four numeric meters §15 permits to be numeric. That detail screen is pull,
reachable, never pushed.

**The calendar is the single most important widget in the game**, because §0.6 names the calendar
as the best mechanic in the design and a widget the player never looks at can't deliver on that.
Four dots per year, filled left to right as quarters resolve. A filled-in quarter that's occupied
shows what's occupying it (a project's title, an interim state like "recovering," "on strike," or
just "open" for a quarter with nothing booked yet). This is the entire opportunity-cost mechanic
made visible: a player looking at three filled dots and one open one is looking at exactly how much
of this year is already spent, at a glance, before a single offer is on screen.

**The "what's happening" card is one card, never a stack.** If two things are simultaneously true
(an offer is waiting *and* a trades digest just refreshed), the card shows whichever is time-
sensitive — an open offer, because it can expire; a digest never expires, because it's pull. This
is Rule 4 from §01 in miniature: the home screen never asks the player to triage a list, because a
list is exactly the kind of "remember to check this" surface §0.3's no-upkeep rule exists to kill.

## What a quarter looks like when nothing is pushed

Most quarters, most years, the home screen has nothing waiting — no red dot, no badge, no pulsing
icon. This is deliberate and worth stating plainly, because it's the single easiest thing for an
implementation to get wrong under pressure to "increase engagement": **an idle home screen is not
a bug to be papered over with notifications.** §0.2 budgets roughly 15–20 pushed moments across an
entire year; a screen that manufactures busywork between them (streaks, daily rewards, anything
that decays if unchecked) is reintroducing the exact chore-treadmill §0.1's Decision Test was
written to kill. The correct feeling on an empty quarter is calm, not anxiety that something's been
missed — because nothing has been. The pull tab bar is always there for a player who wants to go
looking.

## The push interrupt

The one time the hub screen is *not* what the player sees on open: an offer has arrived, or a
pushed decision is waiting (the Deal, Prep, an on-set moment, the season wrap). These render as a
full-screen card *on top of* the hub, not as a notification the player dismisses to get back to the
hub — because a push, by definition, is the thing the player is supposed to be doing right now.
Backing out of a push screen without deciding is possible (nothing in this design traps a player on
a screen), but it returns to the hub with the same card still waiting, unchanged, exactly where it
was — never silently resolved by a default, never re-ordered behind something else.

## Persistent chrome, and what's deliberately absent

Beyond the tab bar, there is no navigation drawer, no settings gear on the main screen, no
notification bell with a badge count. A game whose entire pitch is "you control what you say yes
to" (§3.1) shouldn't visually compete with itself for the player's attention. The only persistent
elements besides the hub's own four regions are a back gesture (always returns to the hub) and a
single settings entry point tucked into the identity strip's detail screen, where it belongs and
where it will never be mistaken for content.
