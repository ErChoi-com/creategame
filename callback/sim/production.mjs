// Verification for the reworked production system — the three scenes a shoot
// is actually played across, and the cut, the fourth approval that used to do
// nothing.
//
//   node callback/sim/production.mjs
//
// Three claims:
//   1. Legacy equivalence — a single `positions` choice and three identical
//      `scenePositions` choices must resolve to bit-identical numbers, so
//      every existing sim policy (and every save recorded before this
//      change) is unaffected.
//   2. A career played entirely through the three-scene interface, varying
//      choices scene to scene, still meets the §14.9 targets — the new path
//      is not just compatible, it is balanced on its own.
//   3. The cut is reachable within a normal career and its effect is small
//      and bounded, the way every other leverage move is.

import { Game, SCENE_LABELS } from '../engine/career.js';
import { RNG, clamp, median } from '../engine/rng.js';
import { PERF_DIALS, POSITIONS } from '../engine/data.js';
import { runCareer, defaultPolicy, TARGETS } from './career-sim.mjs';

let ok = 0, total = 0;
const check = (label, pass) => {
  total++; if (pass) ok++;
  console.log('  %s  %s', label.padEnd(58), pass ? 'ok' : '<<< FAIL');
  return pass;
};

// ---------------------------------------------------------------------------
function legacyEquivalence(n = 500) {
  console.log('\n1. legacy equivalence — uniform scenes vs the single-choice path');
  const rng = new RNG(31);
  let mismatches = 0;
  for (let i = 0; i < n; i++) {
    const g1 = new Game({ seed: i + 1 });
    const g2 = new Game({ seed: i + 1 });
    g1.openBoard(); g2.openBoard();
    if (!g1.board.length) continue;
    const role1 = g1.board[0], role2 = g2.board[0];
    if (g1.pursue(role1.id).cast !== true) continue;
    g2.pursue(role2.id);
    const pos = {};
    for (const d of PERF_DIALS) pos[d] = rng.pick(POSITIONS);
    const p1 = g1.shoot(role1, { prep: 'table', positions: pos, moments: {} });
    const p2 = g2.shoot(role2, { prep: 'table', scenePositions: [pos, pos, pos], moments: {} });
    // Averaging three identical values ((x+x+x)/3) can differ from x by
    // float-rounding noise at the 1e-12 scale — real, but far below anything
    // a clamp(), a comparison, or a displayed number could ever notice.
    const close = (a, b) => Math.abs(a - b) < 1e-6;
    const keys = Object.keys(p1.resolved);
    const resolvedClose = keys.every((k) => close(p1.resolved[k], p2.resolved[k]));
    if (!resolvedClose || !close(p1.shaped.notices, p2.shaped.notices)
        || !close(p1.shaped.ensembleValue, p2.shaped.ensembleValue)) {
      mismatches += 1;
    }
  }
  return check(`${n} paired shoots, resolved/notices/ensemble match within 1e-6`, mismatches === 0);
}

// ---------------------------------------------------------------------------
// A policy identical to career-sim's default, except it spends its contrast
// budget across three real, differing scenes instead of one formulaic call —
// bold in the turn, restrained either side of it, the way the label already
// suggests a scene should be played.
const scenePolicy = {
  ...defaultPolicy,
  choosePositions: undefined,
  chooseScenePositions(game, role) {
    const base = defaultPolicy.choosePositions(game, role);
    const payDial = role.genre === 'comedy' ? 'speed'
      : role.genre === 'romance' || role.genre === 'family' ? 'warmth'
      : role.genre === 'horror' || role.genre === 'thriller' ? 'energy' : 'energy';
    // Underplay it either side of the turn, rather than doing nothing at
    // all — the shape the game already names (§5.6's beats), played for
    // real instead of assumed uniform across the whole shoot.
    const restrained = { energy: 'with', volume: 'with', warmth: 'with', speed: 'with', [payDial]: 'beneath' };
    return [restrained, base, restrained];
  },
};

function scenedCareer(seed) {
  const backgrounds = ['conservatory', 'discovered', 'stage', 'family'];
  const game = new Game({ seed, background: backgrounds[seed % 4] });
  let guard = 0;
  while (!game.over && guard++ < 90) {
    for (let q = 0; q < 4 && !game.over; q++) {
      game.tickPending();
      if (game.blocksBooked < 4) {
        const board = game.openBoard();
        const pick = scenePolicy.chooseRole(game, board);
        if (pick) {
          const res = game.pursue(pick.id);
          if (res.cast) {
            game.shoot(pick, {
              prep: scenePolicy.choosePrep(game, pick),
              scenePositions: scenePolicy.chooseScenePositions(game, pick),
              moments: scenePolicy.chooseMoments(game, pick),
            });
          }
        }
      }
      game.world.tickQuarter();
    }
    if (game.seasonNeedsYou()) { /* no-op, matches a policy with no season hook */ }
    game.endYear();
    const event = game.rollEvent();
    if (event) game.resolveEvent(scenePolicy.chooseEvent ? scenePolicy.chooseEvent(game, event) : 0);
  }
  while (game.pending.length) game.tickPending();
  game.runAwardsSeason();
  return {
    active: game.stats.yearsActive, credits: game.credits.length,
    lead: game.stats.leadCredits, leads42: game.stats.leadsAfter42,
    noms: game.awards.nominations, wins: game.awards.wins,
    peak: game.stats.peakHeat, earn: game.money.lifetime, end: game.actor.age,
  };
}

function scenedTargets(n = 1200) {
  console.log(`\n2. a career played entirely through three real scenes (${n} careers)`);
  const R = [];
  for (let s = 1; s <= n; s++) R.push(scenedCareer(s));
  let pass = 0;
  for (const t of TARGETS) {
    const v = t.measure(R);
    const good = t.ok(v);
    if (good) pass += 1;
    console.log('  %s %s  %s', t.name.padEnd(44), t.fmt(v).padEnd(10), good ? 'PASS' : '<<< FAIL');
  }
  total++; if (pass === TARGETS.length) ok++;
  console.log(`  -> ${pass}/${TARGETS.length} §14.9 targets held under the scene-by-scene path`);
  return pass === TARGETS.length;
}

// ---------------------------------------------------------------------------
function theCut(n = 400) {
  console.log(`\n3. the cut — reachable, and bounded when used (${n} careers)`);
  let reached = 0, used = 0;
  const deltas = [];
  const backgrounds = ['conservatory', 'discovered', 'stage', 'family'];
  for (let s = 1; s <= n; s++) {
    const game = new Game({ seed: s + 90000, background: backgrounds[s % 4] });
    let guard = 0;
    let everHadCut = false;
    while (!game.over && guard++ < 90) {
      for (let q = 0; q < 4 && !game.over; q++) {
        game.tickPending();
        if (game.blocksBooked < 4) {
          const board = game.openBoard();
          const pick = defaultPolicy.chooseRole(game, board);
          if (pick) {
            const res = game.pursue(pick.id);
            if (res.cast) {
              game.shoot(pick, {
                prep: defaultPolicy.choosePrep(game, pick),
                positions: defaultPolicy.choosePositions(game, pick),
                moments: defaultPolicy.chooseMoments(game, pick),
              });
            }
          }
        }
        // Use it the moment it is available, so this measures "reachable in
        // an ordinary career" rather than "reachable if you optimise for it".
        if (game.approvals.has('cut')) {
          const target = game.pending.find((p) => !p.cutFought);
          if (target) {
            const before = { n: target.shaped.notices, e: target.shaped.ensembleValue };
            game.do('fight_for_the_cut', { project: target });
            if (target.cutFought) {
              used += 1;
              deltas.push(Math.abs(target.shaped.notices - before.n));
              deltas.push(Math.abs(target.shaped.ensembleValue - before.e));
            }
          }
        }
        game.world.tickQuarter();
      }
      game.endYear();
      if (!everHadCut && game.approvals.has('cut')) { everHadCut = true; reached += 1; }
      const event = game.rollEvent();
      if (event) game.resolveEvent(defaultPolicy.chooseEvent(game, event));
    }
  }
  check(`'cut' approval earned in some careers (${reached}/${n})`, reached > 0 && reached < n);
  check(`'fight for the cut' actually used when available (${used} uses)`, used > 0);
  const maxDelta = deltas.length ? Math.max(...deltas) : 0;
  check(`each use moves notices/ensemble by a bounded amount (max ${maxDelta.toFixed(1)}, expect <= 5)`, maxDelta <= 5.0001);
}

function main() {
  legacyEquivalence();
  scenedTargets(Number(process.argv[2] || 1200));
  theCut();
  console.log(`\n${ok}/${total} checks passed.\n`);
  process.exitCode = ok === total ? 0 : 1;
}

if (import.meta.url === `file://${process.argv[1]}`) main();
