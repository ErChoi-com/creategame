// End-to-end career simulation — the test the design document never ran.
//
//   node callback/sim/career-sim.mjs [careers]
//
// Runs complete careers through the same engine the game runs, and checks them
// against the targets in §14.9 of callback-design-doc-v8.md. The Python version
// in callback/docs fails all seven. This one is the reason the constants in
// engine/model.js are what they are — change one and re-run this.

import { Game, PREP_OPTIONS } from '../engine/career.js';
import { BILLING_WEIGHT, PERF_DIALS } from '../engine/data.js';
import { median, quantile, clamp } from '../engine/rng.js';
import * as M from '../engine/model.js';

// ---------------------------------------------------------------------------
// A competent-but-not-optimal player. Takes the best role it can get, preps
// sensibly, plays mostly restraint with one strong idea (§5.6).
// ---------------------------------------------------------------------------
export const defaultPolicy = {
  chooseRole(game, board) {
    const a = game.actor;
    let best = null, bestScore = -Infinity;
    for (const r of board) {
      if (game.blocksBooked + r.blocks > 4) continue;
      if (r.union && a.unionCredits < 3) continue;
      // Value per calendar block: the whole point of the calendar is that a
      // bit part in Q2 is a lead you did not take.
      const tierValue = { lead: 100, supporting: 34, bit: 7 }[r.billing];
      const standing = M.standing(a.standing);
      const beneathYou = r.billing === 'bit' && standing > 28 ? 0.15 : 1;
      const expected = beneathYou * r.chance
        * (tierValue + r.scriptQuality * 0.25 + game.world.directorSkill(r.director) * 0.2
           + Math.min(30, r.budgetForRole)) / r.blocks;
      if (expected > bestScore) { bestScore = expected; best = r; }
    }
    return best;
  },

  choosePrep(game, role) {
    const a = game.actor;
    if (role.gates.voice && a.gates.voice < role.gates.voice) return 'dialect';
    if (role.gates.physicality && a.gates.physicality < role.gates.physicality) return 'physical';
    if (role.genre === 'period') return 'research';
    if (role.billing === 'bit') return 'wing';
    return 'table';
  },

  choosePositions(game, role) {
    // One against on the dial the genre pays best for, restraint elsewhere.
    const budget = M.contrastBudget(game.actor.attrs.craft, role.director.command);
    const pos = { energy: 'with', volume: 'with', warmth: 'with', speed: 'with' };
    const payDial = role.genre === 'comedy' ? 'speed'
      : role.genre === 'romance' || role.genre === 'family' ? 'warmth'
      : role.genre === 'horror' || role.genre === 'thriller' ? 'energy' : 'energy';
    if (budget >= 3) pos[payDial] = 'against';
    if (budget >= 4.3) pos[payDial === 'energy' ? 'volume' : 'energy'] = 'beneath';
    return pos;
  },

  chooseMoments() {
    return { not_working: 'ask', adjustment: 'both', discovery: 'offer' };
  },

  // Life events: take the first option unless money says otherwise.
  chooseEvent(game, event) {
    void event;
    return game.money.net < 0 ? 1 : 0;
  },
};

export function runCareer(seed, policy = defaultPolicy, opts = {}) {
  const backgrounds = ['conservatory', 'discovered', 'stage', 'family'];
  const game = new Game({
    seed,
    background: opts.background || backgrounds[seed % 4],
  });

  let guard = 0;
  while (!game.over && guard++ < 90) {
    for (let q = 0; q < 4 && !game.over; q++) {
      game.tickPending();
      // Pull actions, if this policy uses any at all. A policy with no hooks
      // never opens the menu — which is the case sim/agency.mjs holds to the
      // same §14.9 targets as every other.
      if (policy.beforeBoard) policy.beforeBoard(game);
      if (game.blocksBooked < 4) {
        const board = game.openBoard();
        const pick = policy.chooseRole(game, board);
        if (pick) {
          if (policy.beforePursue) policy.beforePursue(game, pick);
          const res = game.pursue(pick.id);
          if (res.cast) {
            if (policy.beforeShoot) policy.beforeShoot(game, pick);
            game.countPush('offer');
            if (game.shouldAskPrep(pick)) game.countPush('prep');
            if (game.shouldAskStance(pick, { coherence: 50 })) game.countPush('stance');
            game.countPush('moments', game.momentsFor(pick).length);
            game.shoot(pick, {
              prep: policy.choosePrep(game, pick),
              positions: policy.choosePositions(game, pick),
              moments: policy.chooseMoments(game, pick),
            });
          }
        }
      }
      if (policy.afterBoard) policy.afterBoard(game);
      game.world.tickQuarter();
    }
    if (game.seasonNeedsYou()) game.countPush('season');
    game.endYear();
    const event = game.rollEvent();
    if (event) {
      game.countPush('life');
      game.resolveEvent(policy.chooseEvent ? policy.chooseEvent(game, event) : 0);
    }
  }
  // Flush anything still in post.
  while (game.pending.length) game.tickPending();
  game.runAwardsSeason();

  return {
    active: game.stats.yearsActive,
    credits: game.credits.length,
    lead: game.stats.leadCredits,
    leads42: game.stats.leadsAfter42,
    noms: game.awards.nominations,
    wins: game.awards.wins,
    peak: game.stats.peakHeat,
    earn: game.money.lifetime,
    net: game.money.net,
    end: game.actor.age,
    game,
  };
}

const TARGETS = [
  {
    name: 'Median career length (years active)',
    target: '26 yrs',
    measure: (R) => median(R.map((x) => x.active)),
    fmt: (v) => `${v.toFixed(0)} yrs`,
    ok: (v) => v >= 20 && v <= 34,
  },
  {
    name: 'Careers reaching Heat > 80',
    target: '~18%',
    measure: (R) => (100 * R.filter((x) => x.peak > 80).length) / R.length,
    fmt: (v) => `${v.toFixed(0)}%`,
    ok: (v) => v >= 10 && v <= 28,
  },
  {
    name: 'Careers with zero nominations',
    target: '~55%',
    measure: (R) => (100 * R.filter((x) => x.noms === 0).length) / R.length,
    fmt: (v) => `${v.toFixed(0)}%`,
    ok: (v) => v >= 42 && v <= 68,
  },
  {
    name: 'Award wins per 100 careers',
    target: '21',
    measure: (R) => (100 * R.reduce((a, x) => a + x.wins, 0)) / R.length,
    fmt: (v) => v.toFixed(0),
    ok: (v) => v >= 10 && v <= 40,
  },
  {
    name: 'Median lifetime earnings',
    target: '$6-11M',
    measure: (R) => median(R.map((x) => x.earn)),
    fmt: (v) => `$${v.toFixed(1)}M`,
    ok: (v) => v >= 4 && v <= 14,
  },
  {
    name: 'Top-decile lifetime earnings',
    target: '$90M+',
    measure: (R) => quantile(R.map((x) => x.earn), 0.90),
    fmt: (v) => `$${v.toFixed(0)}M`,
    ok: (v) => v >= 70,
  },
  {
    name: 'Careers with a lead role after 42',
    target: '~30%',
    measure: (R) => (100 * R.filter((x) => x.leads42 > 0).length) / R.length,
    fmt: (v) => `${v.toFixed(0)}%`,
    ok: (v) => v >= 20 && v <= 44,
  },
];

function main() {
  const n = Number(process.argv[2] || 1200);
  // An independent population, for checking that a result is not an artefact
  // of one seed range: OFFSET=5000 node callback/sim/career-sim.mjs 3000
  const offset = Number(process.env.OFFSET || 0);
  const R = [];
  for (let s = 1 + offset; s <= n + offset; s++) R.push(runCareer(s));

  console.log(`\n=== CALLBACK — FULL CAREER SIMULATION (${n} careers) ===\n`);
  console.log('%s %s %s', 'metric'.padEnd(44), 'target (14.9)'.padEnd(14), 'measured');
  let passed = 0;
  for (const t of TARGETS) {
    const v = t.measure(R);
    const ok = t.ok(v);
    if (ok) passed++;
    console.log('%s %s %s  %s',
      t.name.padEnd(44), t.target.padEnd(14), t.fmt(v).padEnd(9), ok ? 'PASS' : '<<< FAIL');
  }

  const neverLead = (100 * R.filter((x) => x.lead === 0).length) / R.length;
  console.log('\nshape:');
  console.log('  median credits %s | p90 credits %s | median end-age %s',
    median(R.map((x) => x.credits)).toFixed(0),
    quantile(R.map((x) => x.credits), 0.9).toFixed(0),
    median(R.map((x) => x.end)).toFixed(0));
  console.log('  never got started (0 credits): %s%%',
    ((100 * R.filter((x) => x.credits === 0).length) / R.length).toFixed(0));
  console.log('  never played a lead: %s%%', neverLead.toFixed(0));
  console.log('  median peak Heat %s | p90 peak Heat %s',
    median(R.map((x) => x.peak)).toFixed(0), quantile(R.map((x) => x.peak), 0.9).toFixed(0));
  console.log('  p99 lifetime earnings $%sM', quantile(R.map((x) => x.earn), 0.99).toFixed(0));
  console.log('\n%d/%d targets met.\n', passed, TARGETS.length);
  process.exitCode = passed === TARGETS.length ? 0 : 1;
}

if (import.meta.url === `file://${process.argv[1]}`) main();
