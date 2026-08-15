# CALLBACK

A playable film-industry career simulator, built from the design bundle in `docs/`.

You are an actor. Each quarter an offer board arrives; the year is four blocks and every job
eats some of them, so the two scripts you want are always in the same window. You choose the
part, how you prepare, and — the actual game — what you play against the film the director is
making: with it, beneath it, beyond it, or against it, on four dials, up to whatever your craft
and the director's trust will carry. Then it shoots, it is cut without you, and eleven months
later the industry decides what it meant. You never see your own performance number.

The document this comes from had eight versions, sixty-five simulated subsystems and no
character creation, no interface, and no career: run end to end, 80% of its simulated actors
never played a lead and nobody ever became a star. `DESIGN-DELTA.md` lists every change made to
fix that and the check that holds each one in place.

## Play it

```bash
python3 -m http.server 8777        # from the repo root
# open http://localhost:8777/callback/web/index.html
```

No build step and no dependencies — the page loads the engine as ES modules.

## Run the verification

```bash
node callback/sim/career-sim.mjs 3000    # §14.9 whole-career targets — 7/7
node callback/sim/subsystems.mjs         # §14.1, §5.3-5.6, §9.3 — 16/16
node callback/sim/subsystems.mjs positions
node callback/sim/tune.mjs               # constant sweeps (GRID=... N=...)
node callback/sim/smoke-ui.mjs           # headless play-through, needs `npm i`
```

`career-sim.mjs` is the test the design document never ran. It plays complete careers through
the same engine the browser runs, with a policy where a person would be, and checks the
population against the document's own targets:

```
metric                                       target (14.9)  measured
Median career length (years active)          26 yrs         32 yrs     PASS
Careers reaching Heat > 80                   ~18%           15%        PASS
Careers with zero nominations                ~55%           46%        PASS
Award wins per 100 careers                   21             12         PASS
Median lifetime earnings                     $6-11M         $9.2M      PASS
Top-decile lifetime earnings                 $90M+          $101M      PASS
Careers with a lead role after 42            ~30%           42%        PASS
```

Every constant in `engine/model.js` is tuned against these two harnesses. Several trade off
sharply — the earnings tail and the share of careers that reach Heat 80 pull against each other
directly — so change one and re-run both.

## Layout

| Path | What it is |
|---|---|
| `engine/model.js` | Every formula. Standing, casting, palette, coherence, the performance and its two currencies, reception, awards, money. No DOM, no game loop |
| `engine/career.js` | The game loop: character creation, the offer board, prep, the three on-set moments, release, the year, the obituary |
| `engine/world.js` | Genre demand cycles with the eight-quarter greenlight lag, directors and casting directors who age and retire, the project generator |
| `engine/data.js` | Genres, per-genre palette weights, archetypal film shapes, the position read table, name pools |
| `engine/rng.js` | Seeded PRNG — every career is reproducible from its seed |
| `sim/` | The harnesses above |
| `web/` | The interface |
| `docs/` | The original bundle: design doc v8, the review, and the two Python harnesses |

The engine is the same code in both places. A number you see in the browser is a number
`career-sim.mjs` can measure across three thousand lifetimes.
