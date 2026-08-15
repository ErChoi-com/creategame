// Distribution diagnostics — the per-film numbers behind the career results.
// Not a pass/fail check; this is what you read when a target moves and you need
// to know which subsystem moved it.
//
//   node callback/sim/diagnose.mjs [careers]
import { runCareer, defaultPolicy } from './career-sim.mjs';
import { median, quantile, mean } from '../engine/rng.js';

const N = Number(process.argv[2] || 250);
const billing = { lead: 0, supporting: 0, bit: 0 };
const rois = [], auds = [], notices = [], crits = [], fees = [], heats = [], quotes = [];
const budgets = [];

for (let s = 1; s <= N; s++) {
  const r = runCareer(s, defaultPolicy);
  const g = r.game;
  for (const c of g.credits) billing[c.billing]++;
  heats.push(r.peak);
  quotes.push(g.actor.quote);
}

// Re-run one career with instrumentation on release.
import { Game } from '../engine/career.js';
for (let s = 1; s <= N; s++) {
  const g = new Game({ seed: s, background: ['conservatory', 'discovered', 'stage', 'family'][s % 4] });
  const origRelease = g.release.bind(g);
  g.release = (p) => {
    const card = origRelease(p);
    rois.push(card.rec.roi); auds.push(card.rec.audience);
    notices.push(card.rec.notices); crits.push(card.rec.filmCritic);
    budgets.push(p.role.budget);
    return card;
  };
  let guard = 0;
  while (!g.over && guard++ < 90) {
    for (let q = 0; q < 4 && !g.over; q++) {
      g.tickPending();
      if (g.blocksBooked < 4) {
        const board = g.openBoard();
        const pick = defaultPolicy.chooseRole(g, board);
        if (pick) {
          const res = g.pursue(pick.id);
          if (res.cast) {
            const pr = g.shoot(pick, {
              prep: defaultPolicy.choosePrep(g, pick),
              positions: defaultPolicy.choosePositions(g, pick),
              moments: defaultPolicy.chooseMoments(g, pick),
            });
            fees.push(pr.fee);
          }
        }
      }
      g.world.tickQuarter();
    }
    g.endYear();
  }
}

const line = (label, xs) => console.log(
  '%s  mean %s  med %s  p10 %s  p90 %s  p99 %s',
  label.padEnd(12), mean(xs).toFixed(2), median(xs).toFixed(2),
  quantile(xs, 0.1).toFixed(2), quantile(xs, 0.9).toFixed(2), quantile(xs, 0.99).toFixed(2),
);

console.log('\nbilling mix:', billing,
  '\n  lead share', (billing.lead / (billing.lead + billing.supporting + billing.bit)).toFixed(2));
line('ROI', rois);
line('Audience', auds);
line('Notices', notices);
line('Critic', crits);
line('fee $M', fees);
line('budget $M', budgets);
line('peak Heat', heats);
line('end quote', quotes);
