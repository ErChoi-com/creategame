// One career, written out, so you can read what the game actually produces.
//
//   node callback/sim/transcript.mjs [seed] [policy]
//
// This is the qualitative check: the numbers passing is not the same as the
// years reading like a life.

import { runCareer, defaultPolicy } from './career-sim.mjs';
import { POLICIES } from './agency.mjs';

const seed = Number(process.argv[2] || 3);
const which = process.argv[3];
const policy = which ? POLICIES.find((p) => p.name.toLowerCase().includes(which)) || defaultPolicy
  : defaultPolicy;

const r = runCareer(seed, policy);
const g = r.game;

console.log(`\n${'='.repeat(72)}`);
console.log(`${g.actor.name} — ${policy.name || 'default'} — seed ${seed}`);
console.log(`${g.world.startYear}–${g.year}, ${g.actor.background}, wanted ${g.ambition}`);
console.log('='.repeat(72));

let year = null;
for (const entry of g.log) {
  if (entry.year !== year) {
    year = entry.year;
    console.log(`\n  ${year}`);
  }
  const mark = { good: '+', bad: '-', work: '*', lever: '>', life: '~' }[entry.kind] || ' ';
  console.log(`    ${mark} ${entry.text}`);
}

console.log(`\n${'-'.repeat(72)}`);
for (const line of g.obituary()) console.log(`  ${line}`);
console.log('-'.repeat(72));
console.log(`  credits ${g.credits.length} · leads ${g.stats.leadCredits} · `
  + `noms ${g.awards.nominations} · wins ${g.awards.wins} · `
  + `peak heat ${g.stats.peakHeat.toFixed(0)} · earned $${g.money.lifetime.toFixed(1)}M`);
console.log(`  pull actions used: ${g.leverageUsed} · favours held: ${g.favours}`);
console.log('');
