// Agency audit — the checks that hold the design rules in Part 0.
//
//   node callback/sim/agency.mjs [careers]
//
// Breadth is only free if three things are true, and all three are testable:
//
//   1. §0.3 rule 2b — PULL IS FREE. A player who never opens the leverage menu
//      must still play a complete, viable career. If the plain policy misses
//      §14.9's targets while the leverage policies hit them, then leverage is
//      compulsory and the menu is a chore with forty entries.
//   2. §0.1 the Decision Test — NOTHING DOMINATES. Distinct playstyles must
//      arrive at genuinely different places, and no single one may win on
//      every axis. If one does, it is the optimal line and the rest is
//      decoration.
//   3. §0.3 rule 3 — OPTIONS NARROW, NOT MULTIPLY. Year 45 must not push more
//      prompts at the player than year 15, no matter how many verbs have
//      accumulated.

import { runCareer, defaultPolicy } from './career-sim.mjs';
import { median, quantile, mean, clamp } from '../engine/rng.js';
import * as M from '../engine/model.js';
import { AMBITIONS } from '../engine/ambition.js';

// ---------------------------------------------------------------------------
// Five ways to play. Each is a plausible person, not an optimiser.
// ---------------------------------------------------------------------------
const base = defaultPolicy;

const plain = { ...base, name: 'Plain (never opens the menu)' };

const favourBank = {
  ...base,
  name: 'The Favour Bank',
  chooseRole(game, board) {
    // Chase good directors and good scripts rather than billing.
    let best = null, bestScore = -Infinity;
    for (const r of board) {
      if (game.blocksBooked + r.blocks > 4) continue;
      if (r.union && game.actor.unionCredits < 3) continue;
      const v = r.chance * (game.world.directorSkill(r.director) * 0.8 + r.scriptQuality * 0.5
        + (r.billing === 'bit' ? 0 : 25)) / r.blocks;
      if (v > bestScore) { bestScore = v; best = r; }
    }
    return best;
  },
  chooseMoments: () => ({ not_working: 'absorb', adjustment: 'take', discovery: 'offer' }),
  choosePositions(game, role) {
    game.standingOrders.stance = 'generous';
    return game.autoPositions(role);
  },
  beforePursue(game, role) {
    if (game.world.directorSkill(role.director) > 68) game.do('take_scale', { role });
  },
  beforeBoard(game) {
    if (game.world.scandals.length && game.rng.chance(0.6)) game.do('defend_scandal');
    if (game.mentees.length < 3 && game.actor.age > 34 && game.rng.chance(0.15)) game.do('mentor');
    if (game.board.length < 2 && game.rolodex.creditors(2).length) game.do('call_in_favour');
    if (game.actor.age > 50 && !game.positions.has('teacher') && game.rng.chance(0.2)) game.do('teach');
  },
};

const disappearingAct = {
  ...base,
  name: 'The Disappearing Act',
  beforeBoard(game) {
    // Vanish when you are typecast and hot enough for it to cost something —
    // and not more than once every eight years or so.
    const rested = game.year - (game._lastVanish || -99) > 6;
    if (!game.hiatus && rested && game.legibility > 45 && game.actor.standing.heat > 30) {
      game._lastVanish = game.year;
      game.do('disappear');
    } else if (game.hiatus && game.scarcity >= 30) {
      game.do('end_disappear');
    }
    if (!game.hiatus && game.legibility > 86 && game.actor.standing.heat < 18) game.do('reinvent');
  },
  chooseRole(game, board) {
    if (game.hiatus) return null;
    return base.chooseRole(game, board);
  },
};

const indispensable = {
  ...base,
  name: 'The Indispensable One',
  chooseRole(game, board) {
    // The commitment that defines this playstyle: the property comes first,
    // every time, whatever else is on the board that quarter.
    const installment = board.find((r) => r.franchiseInstallment
      && game.blocksBooked + r.blocks <= 4);
    if (installment) return installment;
    // And once there is a property, the calendar is kept clear for it: this
    // playstyle turns down work that would put it out of the next one.
    if (game.franchise && !game.franchise.writtenOut
        && game.franchise.installments < game.franchise.maxInstallments) {
      const compatible = board.filter((r) => r.blocks <= 1
        && game.blocksBooked + r.blocks <= 2
        && !(r.union && game.actor.unionCredits < 3));
      if (!compatible.length) return null;
      return compatible.sort((x, y) => y.chance - x.chance)[0];
    }
    let best = null, bestScore = -Infinity;
    for (const r of board) {
      if (game.blocksBooked + r.blocks > 4) continue;
      if (r.union && game.actor.unionCredits < 3) continue;
      const franchisey = r.type === 'tentpole' ? 60 : 0;
      const v = r.chance * ({ lead: 100, supporting: 34, bit: 7 }[r.billing] + franchisey
        + Math.min(30, r.budgetForRole)) / r.blocks;
      if (v > bestScore) { bestScore = v; best = r; }
    }
    return best;
  },
  beforeBoard(game) {
    if (game.franchise && game.franchise.identification > 45) game.do('holdout');
    if (game.money.net > 120) game.do('buy_back_ip');
  },
  beforeShoot(game, role) {
    if (game.approvals.has('costar') && role.costar.ego > 72) game.do('block_costar', { current: role });
  },
};

const author = {
  ...base,
  name: 'The Author',
  beforeBoard(game) {
    if (!game.positions.has('prodco') && game.actor.standing.prestige > 45) game.do('production_company');
    if (game.development.length < 2 && game.money.net > 2 && game.rng.chance(0.5)) game.do('option_material');
    const unshopped = game.development.find((s) => !s.shopped);
    if (unshopped && game.blocksBooked < 3) game.do('attach_and_shop', { script: unshopped });
    if (game.money.net > 25 && game.rng.chance(0.2)) game.do('fund_indie');
    if (game.pending.some((p) => p.role.type === 'indie' && !p.festival)) game.do('festival_premiere');
  },
  beforeShoot(game, role) {
    if (role.fit < 55) game.do('request_rewrite', { current: role });
    if (game.actor.attrs.instinct > 62) game.do('improvise', { current: role });
  },
};

// Two bounding agents, in the spirit of the automated-playtesting literature:
// hand-written playstyles tell you what happens when someone plays *a way*,
// but they cannot tell you where the edges are. A random agent bounds the
// bottom (does the game hold up for someone who is not really trying?) and a
// greedy optimiser bounds the top (can the obvious line run away with it?).
const drifter = {
  ...base,
  name: 'Random (barely paying attention)',
  chooseRole(game, board) {
    const takeable = board.filter((r) => game.blocksBooked + r.blocks <= 4
      && !(r.union && game.actor.unionCredits < 3));
    if (!takeable.length || game.rng.chance(0.3)) return null;
    return takeable[game.rng.int(0, takeable.length - 1)];
  },
  choosePrep: (game) => ['table', 'research', 'dialect', 'physical', 'method', 'wing'][game.rng.int(0, 5)],
  choosePositions(game, role) {
    const pos = {};
    for (const d of ['energy', 'volume', 'warmth', 'speed']) {
      pos[d] = ['with', 'beneath', 'beyond', 'against'][game.rng.int(0, 3)];
    }
    void role;
    return pos;
  },
  chooseMoments: () => ({}),
  chooseEvent: (game) => game.rng.int(0, 2),
};

// Between the two: someone who takes whatever comes but works properly when
// they are there. If this one has no career either, the fault is in the offer
// economy; if it does, then playing badly is what costs the random agent, which
// is the game working.
const jobbing = {
  ...base,
  name: 'Takes what comes (but works properly)',
  chooseRole(game, board) {
    const takeable = board.filter((r) => game.blocksBooked + r.blocks <= 4
      && !(r.union && game.actor.unionCredits < 3));
    if (!takeable.length) return null;
    return takeable[game.rng.int(0, takeable.length - 1)];
  },
};

const optimiser = {
  ...base,
  name: 'Greedy (always the best number)',
  chooseRole(game, board) {
    // Rank by immediate expected standing and money, and use every pull verb
    // that is available every single quarter.
    let best = null, bestScore = -Infinity;
    for (const r of board) {
      if (game.blocksBooked + r.blocks > 4) continue;
      if (r.union && game.actor.unionCredits < 3) continue;
      const v = r.chance * (r.budgetForRole * 2
        + { lead: 120, supporting: 40, bit: 8 }[r.billing]
        + r.scriptQuality * 0.4 + game.world.directorSkill(r.director) * 0.4) / r.blocks;
      if (v > bestScore) { bestScore = v; best = r; }
    }
    return best;
  },
  beforeBoard(game) {
    for (const { action } of game.moves()) {
      if (['disappear', 'reinvent', 'refuse_scene', 'start_feud'].includes(action.id)) continue;
      game.do(action.id);
    }
  },
  beforePursue(game, role) {
    for (const { action } of game.moves({ role })) {
      if (['turn_down_publicly'].includes(action.id)) continue;
      if (['campaign_for_role', 'screen_test_free', 'take_scale'].includes(action.id)) {
        game.do(action.id, { role });
      }
    }
  },
  beforeShoot(game, role) {
    for (const { action } of game.moves({ current: role })) {
      if (action.id === 'refuse_scene') continue;
      game.do(action.id, { current: role });
    }
  },
};

const POLICIES = [plain, favourBank, disappearingAct, indispensable, author, drifter, jobbing, optimiser];

// ---------------------------------------------------------------------------
function profile(policy, n) {
  const R = [];
  for (let s = 1; s <= n; s++) R.push(runCareer(s, policy));
  const games = R.map((r) => r.game);
  return {
    name: policy.name,
    active: median(R.map((x) => x.active)),
    peak: median(R.map((x) => x.peak)),
    hot: (100 * R.filter((x) => x.peak > 80).length) / R.length,
    notices: mean(games.map((g) => mean(g.noticesHistory.length ? g.noticesHistory : [0]))),
    prestige: mean(games.map((g) => g.actor.standing.prestige)),
    earnMed: median(R.map((x) => x.earn)),
    earnP90: quantile(R.map((x) => x.earn), 0.9),
    wins: (100 * R.reduce((a, x) => a + x.wins, 0)) / R.length,
    nonoms: (100 * R.filter((x) => x.noms === 0).length) / R.length,
    leads: median(R.map((x) => x.lead)),
    lead42: (100 * R.filter((x) => x.leads42 > 0).length) / R.length,
    favours: mean(games.map((g) => g.favours)),
    // Career shape, not size: how many lanes did this person actually work in?
    range: mean(games.map((g) => Object.values(g.actor.genreCredits)
      .filter((n) => n >= 2).length)),
    // How typecast you end up. Not an Ambition, but it is the thing a
    // vanishing is actually for — you come back readable as something else —
    // and no other axis records it.
    legibility: mean(games.map((g) => g.legibility)),
    // The six things §0.4 says a career can be for. Scoring the playstyles
    // against the game's own declared win conditions is the only fair test of
    // whether they are really different careers.
    ambitions: Object.fromEntries(Object.keys(AMBITIONS).map((k) => [
      k, mean(games.map((g) => AMBITIONS[k].score(g))),
    ])),
    credits: median(R.map((x) => x.credits)),
    pushes15: pushesAtAge(games, 15),
    pushes45: pushesAtAge(games, 45),
    levers: mean(games.map((g) => g.leverageUsed)),
  };
}

// Pushed prompts in the career-year closest to a given age.
function pushesAtAge(games, age) {
  const vals = [];
  for (const g of games) {
    const startYear = g.world.startYear;
    const startAge = g.actor.age - (g.year - startYear);
    const targetYear = startYear + Math.max(0, age - startAge);
    const rec = g.pushesByYear.get(targetYear);
    if (rec) vals.push(rec.total);
  }
  return vals.length ? mean(vals) : 0;
}

export { POLICIES };

// Only audit when run directly; transcript.mjs imports the playstyles.
if (import.meta.url === `file://${process.argv[1]}`) {
  const n = Number(process.argv[2] || 400);
  const STYLES = POLICIES.slice(0, 5);
  const BOUNDS = POLICIES.slice(5);   // random, jobbing, greedy
  const rows = STYLES.map((p) => profile(p, n));
  const bounds = BOUNDS.map((p) => profile(p, n));

  console.log(`\n=== AGENCY AUDIT (${n} careers per playstyle) ===\n`);
  const head = ['playstyle', 'active', 'peakHeat', 'notices', 'prestige', 'earn med', 'earn p90', 'wins/100', 'legible', 'favours', 'levers'];
  console.log(head[0].padEnd(30) + head.slice(1).map((h) => h.padStart(9)).join(''));
  for (const r of rows) {
    console.log(
      r.name.padEnd(30)
      + r.active.toFixed(0).padStart(9)
      + r.peak.toFixed(0).padStart(9)
      + r.notices.toFixed(1).padStart(9)
      + r.prestige.toFixed(0).padStart(9)
      + `$${r.earnMed.toFixed(1)}`.padStart(9)
      + `$${r.earnP90.toFixed(0)}`.padStart(9)
      + r.wins.toFixed(0).padStart(9)
      + r.legibility.toFixed(0).padStart(9)
      + r.favours.toFixed(1).padStart(9)
      + r.levers.toFixed(1).padStart(9),
    );
  }

  // --- 1. Pull is free ------------------------------------------------------
  console.log('\n1. PULL IS FREE — the plain policy never opens the menu (§0.3 rule 2b)');
  const p0 = rows[0];
  const viable = p0.active >= 20 && p0.earnMed >= 4 && p0.hot >= 8 && p0.lead42 >= 18;
  console.log(`   plain: ${p0.active.toFixed(0)} active years, $${p0.earnMed.toFixed(1)}M median, `
    + `${p0.hot.toFixed(0)}% reach Heat 80, ${p0.lead42.toFixed(0)}% lead after 42, ${p0.levers.toFixed(1)} actions used`);
  console.log(`   ${viable ? 'ok' : '<<<'} a career that ignores Part 6 entirely is still a complete career`);

  // --- 2. Nothing dominates, and every style is a different career ----------
  console.log('\n2. NOTHING DOMINATES — no optimal line, and the styles are actually different (§0.1, §6.8)');
  const axes = Object.keys(AMBITIONS);
  const val = (row, axis) => row.ambitions[axis];
  const winners = {};
  for (const axis of axes) {
    const best = rows.reduce((a, b) => (val(b, axis) > val(a, axis) ? b : a));
    winners[axis] = best.name;
  }
  console.log('   scored against the six Ambitions the game declares in §0.4:');
  for (const axis of axes) {
    console.log(`   ${AMBITIONS[axis].label.padEnd(16)} ${winners[axis].padEnd(30)}`
      + rows.map((r) => val(r, axis).toFixed(0).padStart(8)).join(''));
  }

  // (a) nobody wins everything, and nobody loses everything
  const dominators = rows.filter((r) => axes.every((a) => winners[a] === r.name));
  const alsoRans = rows.filter((r) => axes.every((a) => {
    const worst = rows.reduce((x, y) => (val(y, a) < val(x, a) ? y : x));
    return worst.name === r.name;
  }));

  // (b) each style is viable on its own terms — a real career, not a trap
  const viableStyles = rows.filter((r) => r.active >= 18 && r.earnMed >= 3 && r.notices >= 40);

  // (c) and each is a materially different career from the plain one
  const plainRow = rows[0];
  // Shape axes: the six declared win conditions, plus three the Ambitions do
  // not cover — how many lanes you worked in, how typecast you ended up (the
  // thing a vanishing is actually for), and how big your best years got.
  const shapeAxes = [
    ...axes.map((a) => [AMBITIONS[a].label, (r) => val(r, a)]),
    ['range of work', (r) => r.range],
    ['how typecast', (r) => r.legibility],
    ['top-end money', (r) => r.earnP90],
  ];
  // "Materially different" is a fifth: a playstyle that moves an outcome by
  // less than that is a preference, not a strategy.
  const MATERIAL = 0.20;
  const divergence = rows.slice(1).map((r) => {
    const diffs = shapeAxes.filter(([, get]) => {
      const base = Math.abs(get(plainRow)) + 1e-6;
      return Math.abs(get(r) - get(plainRow)) / base > MATERIAL;
    }).map(([label]) => label);
    return { name: r.name, axes: diffs };
  });
  console.log(`   materially different (>${(MATERIAL * 100).toFixed(0)}%) from a career that just takes the best job going:`);
  for (const d of divergence) {
    console.log(`   ${d.name.padEnd(30)} ${d.axes.join(', ') || 'nothing'}`);
  }
  const allDiverge = divergence.every((d) => d.axes.length >= 2);
  const noDominance = dominators.length === 0 && alsoRans.length === 0
    && viableStyles.length === rows.length && allDiverge;
  console.log(`   ${noDominance ? 'ok' : '<<<'} ${dominators.length} dominate every axis, `
    + `${alsoRans.length} lose every axis, ${viableStyles.length}/${rows.length} viable, `
    + `${divergence.filter((d) => d.axes.length >= 2).length}/${divergence.length} play out differently`);

  // --- 3. Options narrow ----------------------------------------------------
  console.log('\n3. OPTIONS NARROW, NOT MULTIPLY — pushed prompts at 15 vs 45 (§0.3 rule 3)');
  let narrows = true;
  for (const r of rows) {
    const ok = r.pushes45 <= r.pushes15 + 1;
    if (!ok) narrows = false;
    console.log(`   ${r.name.padEnd(30)} year 15: ${r.pushes15.toFixed(1)}  year 45: ${r.pushes45.toFixed(1)}  ${ok ? 'ok' : '<<<'}`);
  }
  const budgetOk = rows.every((r) => Math.max(r.pushes15, r.pushes45) <= 20);
  console.log(`   ${budgetOk ? 'ok' : '<<<'} everyone stays inside §0.2's ~20 pushed decisions a year`);

  // --- 4. The edges ---------------------------------------------------------
  // Hand-written playstyles say what happens when someone plays a way. They
  // cannot say where the edges are, so three agents bound the band: one who
  // takes whatever comes but does the work, one who does everything at random,
  // and one who pulls every available lever every quarter.
  console.log('\n4. THE EDGES — bounding agents');
  const [rand, jobber, greedy] = bounds;
  for (const b of bounds) {
    console.log(`   ${b.name.padEnd(38)} ${b.active.toFixed(0)} active yrs · `
      + `$${b.earnMed.toFixed(1)}M median · ${b.wins.toFixed(0)} wins/100 · `
      + `${b.levers.toFixed(0)} actions used`);
  }

  // The floor is not the random agent — it is the person who is not
  // optimising. If they have no career, the offer economy is broken.
  const floorOk = jobber.active >= 15 && jobber.earnMed >= 2;
  // And playing badly has to cost something, or the creative layer is decoration.
  // Same materiality bar as check 2, rather than a threshold invented here.
  const badPlayCosts = rand.active < jobber.active * (1 - MATERIAL)
    && rand.earnMed < jobber.earnMed * (1 - MATERIAL);
  // The ceiling: an agent that uses everything may be very good at one thing.
  // It must not be best at all six of the things a career can be for.
  const greedyWins = axes.filter((a) => val(greedy, a) > Math.max(...rows.map((r) => val(r, a))));
  const ceilingOk = greedyWins.length < axes.length;

  console.log(`   ${floorOk ? 'ok' : '<<<'} taking what comes and doing the work is a career `
    + `(${jobber.active.toFixed(0)} yrs, $${jobber.earnMed.toFixed(1)}M)`);
  console.log(`   ${badPlayCosts ? 'ok' : '<<<'} playing badly costs: random gets `
    + `${rand.active.toFixed(0)} yrs and $${rand.earnMed.toFixed(1)}M against that`);
  console.log(`   ${ceilingOk ? 'ok' : '<<<'} the everything-agent beats every playstyle on `
    + `${greedyWins.length}/${axes.length} ambitions`
    + (greedyWins.length ? ` (${greedyWins.map((a) => AMBITIONS[a].label).join(', ')})` : ''));

  const passed = [viable, noDominance, narrows, budgetOk,
    floorOk && badPlayCosts && ceilingOk].filter(Boolean).length;
  console.log(`\n${passed}/5 agency rules hold.\n`);
  process.exitCode = passed === 5 ? 0 : 1;
}
