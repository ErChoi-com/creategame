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

const POLICIES = [plain, favourBank, disappearingAct, indispensable, author];

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
  const rows = POLICIES.map((p) => profile(p, n));

  console.log(`\n=== AGENCY AUDIT (${n} careers per playstyle) ===\n`);
  const head = ['playstyle', 'active', 'peakHeat', 'notices', 'prestige', 'earn med', 'earn p90', 'wins/100', 'range', 'favours', 'levers'];
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
      + r.range.toFixed(1).padStart(9)
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
  // Shape axes: the six declared win conditions, plus two the Ambitions do not
  // cover — how many lanes you worked in, and how big your best years got.
  const shapeAxes = [
    ...axes.map((a) => [AMBITIONS[a].label, (r) => val(r, a)]),
    ['range of work', (r) => r.range],
    ['top-end money', (r) => r.earnP90],
  ];
  const divergence = rows.slice(1).map((r) => {
    const diffs = shapeAxes.filter(([, get]) => {
      const base = Math.abs(get(plainRow)) + 1e-6;
      return Math.abs(get(r) - get(plainRow)) / base > 0.25;
    }).map(([label]) => label);
    return { name: r.name, axes: diffs };
  });
  for (const d of divergence) {
    console.log(`   ${d.name.padEnd(30)} differs from plain on: ${d.axes.join(', ') || 'nothing'}`);
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

  const passed = [viable, noDominance, narrows, budgetOk].filter(Boolean).length;
  console.log(`\n${passed}/4 agency rules hold.\n`);
  process.exitCode = passed === 4 ? 0 : 1;
}
