// Subsystem verification — §14.1 (reception), §5.3–5.6 (palette, positions,
// shape) and §9.3 (genre cycles), re-run against the *unified* model rather
// than against each subsystem in isolation.
//
//   node callback/sim/subsystems.mjs [all|reception|palette|positions|genre]
//
// The design review's finding was that the doc's two flagship subsystems were
// each verified alone and were mutually inconsistent. These checks all run
// through engine/model.js, so they cannot drift apart again.

import { RNG, clamp, mean, median } from '../engine/rng.js';
import * as M from '../engine/model.js';
import { World } from '../engine/world.js';
import {
  GENRES, PERF_DIALS, POSITIONS, DIALS, GENRE_ECON,
} from '../engine/data.js';

const corr = (xs, ys) => {
  const mx = mean(xs), my = mean(ys);
  let sxy = 0, sxx = 0, syy = 0;
  for (let i = 0; i < xs.length; i++) {
    const dx = xs[i] - mx, dy = ys[i] - my;
    sxy += dx * dy; sxx += dx * dx; syy += dy * dy;
  }
  return sxy / Math.sqrt(sxx * syy);
};

const sd = (xs) => {
  const m = mean(xs);
  return Math.sqrt(mean(xs.map((x) => (x - m) ** 2)));
};

const check = (label, value, lo, hi) => {
  const ok = value >= lo && value <= hi;
  console.log('  %s %s  target %s–%s  %s',
    label.padEnd(34), value.toFixed(2).padStart(7), lo, hi, ok ? 'ok' : '<<<');
  return ok;
};

// ---------------------------------------------------------------------------
function reception(n = 30000) {
  console.log('\n§14.1 reception model — 30,000 project resolutions');
  const rng = new RNG(11);
  const world = new World(new RNG(12));
  const P = [], NOT = [], FC = [], AUD = [], ROI = [], ENS = [];
  const LP = [], LFC = [], LROI = [];   // the lead subset

  for (let i = 0; i < n; i++) {
    const genre = rng.pick(GENRES);
    const budget = clamp(GENRE_ECON[genre].budget * rng.float(0.3, 2.2), 1, 320);
    const director = world.directors[rng.int(0, world.directors.length - 1)];
    const palette = world.randomPalette(rng, genre, budget, director.taste);
    const coh = M.coherence(palette);

    const actor = {
      attrs: {
        craft: clamp(rng.gauss(58, 15), 5, 98),
        instinct: clamp(rng.gauss(52, 17), 5, 98),
        presence: clamp(rng.gauss(55, 15), 5, 98),
        resilience: 55,
      },
    };
    const perf = M.performance(rng, {
      actor,
      role: {},
      film: { coherence: coh.value },
      prep: clamp(rng.gauss(58, 18), 0, 100),
      chemistry: clamp(rng.gauss(60, 17), 0, 100),
      condition: clamp(rng.gauss(78, 12), 25, 100),
      directorSkill: world.directorSkill(director),
      fit: clamp(rng.gauss(66, 16), 0, 100),
    });

    const positions = {};
    for (const d of PERF_DIALS) positions[d] = rng.pick(POSITIONS);
    const resolved = M.resolvePositions(positions, {
      genre, craft: actor.attrs.craft, directorCommand: director.command,
    });
    const shaped = M.shapePerformance(perf.value, resolved, actor.attrs.presence);

    const billing = rng.weighted([['lead', 0.3], ['supporting', 0.4], ['bit', 0.3]]);
    const bwSelf = { lead: 1, supporting: 0.55, bit: 0.2 }[billing];
    const otherWeights = billing === 'lead' ? [0.55, 0.25]
      : billing === 'supporting' ? [1.0, 0.55, 0.2] : [1.0, 0.55, 0.55];
    let num = shaped.ensembleValue * bwSelf, den = bwSelf;
    for (const w of otherWeights) { num += clamp(rng.gauss(57, 14), 0, 100) * w; den += w; }
    const ensembleScore = num / den;

    const rec = M.reception(rng, {
      film: {}, genre, budget,
      scriptQuality: clamp(rng.gauss(58, 17), 5, 98),
      directorSkill: world.directorSkill(director),
      directorPrestige: director.prestige,
      castStarPower: clamp(rng.gauss(42, 20), 0, 100),
      genreDemand: world.demand[genre],
      ensembleScore,
      yourNotices: shaped.notices,
      billing,
      palette,
    });

    P.push(perf.value); NOT.push(rec.notices); FC.push(rec.filmCritic);
    AUD.push(rec.audience); ROI.push(rec.roi); ENS.push(ensembleScore);
    if (billing === 'lead') { LP.push(perf.value); LFC.push(rec.filmCritic); LROI.push(rec.roi); }
  }

  console.log('  distributions:');
  for (const [k, xs] of [['Performance', P], ['Notices', NOT], ['FilmCritic', FC], ['Audience', AUD], ['Ensemble', ENS]]) {
    console.log('    %s mean %s sd %s', k.padEnd(12), mean(xs).toFixed(1), sd(xs).toFixed(1));
  }
  console.log('    ROI median %s | %s%% profitable',
    median(ROI).toFixed(2), (100 * ROI.filter((r) => r > 1).length / ROI.length).toFixed(0));

  console.log('  correlations:');
  let ok = 0, total = 0;
  const c = (l, v, lo, hi) => { total++; if (check(l, v, lo, hi)) ok++; };
  c('Performance <-> Notices', corr(P, NOT), 0.60, 0.85);
  // §4.10's signature numbers are stated for a lead ("for a lead this
  // resolves to about 0.80 yours"); a bit player's four lines are correctly
  // near-uncorrelated with whether the film is any good.
  c('Performance <-> FilmCritic (lead)', corr(LP, LFC), 0.25, 0.55);
  c('Performance <-> ROI (lead)', corr(LP, LROI), 0.08, 0.35);
  console.log('    (all billings: P<->FC %s, P<->ROI %s)',
    corr(P, FC).toFixed(2), corr(P, ROI).toFixed(2));
  c('FilmCritic <-> ROI', corr(FC, ROI), 0.15, 0.45);
  c('FilmCritic <-> Audience', corr(FC, AUD), 0.35, 0.60);
  return [ok, total];
}

// ---------------------------------------------------------------------------
function palette() {
  console.log('\n§5.3 palette — audience/critic alignment per genre (8,000 palettes each)');
  const rng = new RNG(21);
  let ok = 0, total = 0;
  const expected = { horror: [0.2, 1.0], drama: [-1.0, -0.2], scifi: [-0.4, 0.4], comedy: [-0.1, 0.8], action: [-0.6, 0.3] };
  for (const g of GENRES) {
    const A = [], C = [];
    for (let i = 0; i < 8000; i++) {
      const p = {};
      for (const d of DIALS) p[d] = rng.float(-50, 50);
      const e = M.paletteEffect(p, g);
      A.push(e.aud); C.push(e.crit);
    }
    const r = corr(A, C);
    const bounds = expected[g];
    if (bounds) { total++; if (check(`corr(aud, crit) ${g}`, r, bounds[0], bounds[1])) ok++; }
    else console.log('  %s %s', `corr(aud, crit) ${g}`.padEnd(34), r.toFixed(2).padStart(7));
  }

  console.log('\n§5.4 coherence — 20,000 random palettes');
  const cohs = [];
  for (let i = 0; i < 20000; i++) {
    const p = {};
    for (const d of DIALS) p[d] = rng.float(-50, 50);
    cohs.push(M.coherence(p).value);
  }
  total++; if (check('mean coherence', mean(cohs), 30, 58)) ok++;
  total++; if (check('% below 30', 100 * cohs.filter((c) => c < 30).length / cohs.length, 5, 40)) ok++;
  return [ok, total];
}

// ---------------------------------------------------------------------------
function positions() {
  console.log('\n§5.5–5.6 positions — the two currencies, and no dominant allocation');
  const rng = new RNG(31);
  const allocations = {
    'all with': { energy: 'with', volume: 'with', warmth: 'with', speed: 'with' },
    'two beneath': { energy: 'beneath', volume: 'beneath', warmth: 'with', speed: 'with' },
    'one against': { energy: 'against', volume: 'beneath', warmth: 'with', speed: 'with' },
    'against + beyond': { energy: 'against', volume: 'beyond', warmth: 'with', speed: 'beneath' },
  };
  console.log('  %s %s %s %s', 'allocation'.padEnd(20), 'spiky'.padStart(6), 'Notices'.padStart(9), 'Ensemble'.padStart(9));
  const notices = {};
  for (const [label, pos] of Object.entries(allocations)) {
    const N = [], E = [], S = [];
    for (let i = 0; i < 4000; i++) {
      const r = M.resolvePositions(pos, { genre: 'drama', craft: 70, directorCommand: 60 });
      const shaped = M.shapePerformance(clamp(rng.gauss(64, 14), 0, 100), r, 55);
      N.push(shaped.notices); E.push(shaped.ensembleValue); S.push(r.spikiness);
    }
    notices[label] = mean(N);
    console.log('  %s %s %s %s', label.padEnd(20),
      mean(S).toFixed(2).padStart(6), mean(N).toFixed(1).padStart(9), mean(E).toFixed(1).padStart(9));
  }

  // Which of all 256 allocations wins, per build and genre. If one wins
  // everywhere there is a line to memorise and the system is fake.
  const every = [];
  for (const a of POSITIONS) for (const b of POSITIONS) for (const c of POSITIONS) for (const d of POSITIONS) {
    every.push({ energy: a, volume: b, warmth: c, speed: d });
  }
  const key = (p) => PERF_DIALS.map((d) => `${d[0]}:${p[d]}`).join(' ');
  const winners = new Map();
  const combos = [];
  for (const genre of GENRES) {
    for (const craft of [35, 55, 75, 95]) {
      for (const command of [35, 70]) {
        let best = null, bestV = -Infinity;
        for (const pos of every) {
          const r = M.resolvePositions(pos, { genre, craft, directorCommand: command });
          // Expected Notices at a fixed underlying performance: the allocation
          // is what varies, so the noise term would only blur the comparison.
          const v = M.shapePerformance(64, r, 55).notices;
          if (v > bestV) { bestV = v; best = pos; }
        }
        winners.set(key(best), (winners.get(key(best)) || 0) + 1);
        combos.push(best);
      }
    }
  }
  console.log('  optimal allocation across %d build/genre/director combinations:', combos.length);
  const sorted = [...winners.entries()].sort((x, y) => y[1] - x[1]);
  for (const [k, v] of sorted.slice(0, 6)) console.log('    %s %d', k.padEnd(48), v);
  console.log('    (%d distinct optimal allocations)', winners.size);
  const topShare = sorted[0][1] / combos.length;
  const ok = check('most common optimum, share', topShare, 0, 0.5);
  return [ok ? 1 : 0, 1];
}

// ---------------------------------------------------------------------------
function genre() {
  console.log('\n§9.3 genre cycles — 40 years of demand');
  const world = new World(new RNG(41));
  const series = {};
  for (const g of GENRES) series[g] = [];
  for (let q = 0; q < 160; q++) {
    world.tickQuarter();
    for (const g of GENRES) series[g].push(world.demand[g]);
  }
  let ok = 0, total = 0;
  for (const g of ['horror', 'drama', 'action']) {
    const xs = series[g];
    const swing = Math.max(...xs) - Math.min(...xs);
    total++; if (check(`${g} peak-to-trough swing`, swing, 8, 88)) ok++;
  }
  console.log('  final demand:', GENRES.map((g) => `${g} ${world.demand[g].toFixed(0)}`).join(' | '));
  return [ok, total];
}

const which = process.argv[2] || 'all';
const runs = { reception, palette, positions, genre };
let ok = 0, total = 0;
for (const [name, fn] of Object.entries(runs)) {
  if (which !== 'all' && which !== name) continue;
  const [o, t] = fn();
  ok += o; total += t;
}
console.log('\n%d/%d subsystem checks in range.\n', ok, total);
process.exitCode = ok === total ? 0 : 1;
