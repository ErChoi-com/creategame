// Constant sweep. Mutates engine/model.js's K in place and re-runs careers.
//   node callback/sim/tune.mjs
import { runCareer } from './career-sim.mjs';
import { K } from '../engine/model.js';
import { median, quantile } from '../engine/rng.js';

const N = Number(process.env.N || 220);
function metrics() {
  const R = [];
  for (let s = 1; s <= N; s++) R.push(runCareer(s));
  return {
    active: median(R.map(x => x.active)),
    hot: 100 * R.filter(x => x.peak > 80).length / R.length,
    nonoms: 100 * R.filter(x => x.noms === 0).length / R.length,
    wins: 100 * R.reduce((a, x) => a + x.wins, 0) / R.length,
    earnMed: median(R.map(x => x.earn)),
    earnP90: quantile(R.map(x => x.earn), 0.9),
    lead42: 100 * R.filter(x => x.leads42 > 0).length / R.length,
    peakMed: median(R.map(x => x.peak)),
  };
}
const grid = JSON.parse(process.env.GRID || '[{}]');
for (const g of grid) {
  const saved = {};
  for (const [k, v] of Object.entries(g)) { saved[k] = K[k]; K[k] = v; }
  const m = metrics();
  console.log(JSON.stringify(g), '->',
    `active ${m.active.toFixed(0)} hot ${m.hot.toFixed(0)}% nonoms ${m.nonoms.toFixed(0)}% wins ${m.wins.toFixed(0)} earn ${m.earnMed.toFixed(1)}/${m.earnP90.toFixed(0)} lead42 ${m.lead42.toFixed(0)}% peak ${m.peakMed.toFixed(0)}`);
  for (const [k, v] of Object.entries(saved)) K[k] = v;
}
