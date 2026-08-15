// Save/load verification: a save file is the journal, and replaying it must
// rebuild the identical career.
//
//   node callback/sim/replay-test.mjs [careers]

import { Game } from '../engine/career.js';
import { defaultPolicy } from './career-sim.mjs';

// Plays a career entirely through Game.call(), the way the interface does.
function play(seed, quarters = 120) {
  const g = new Game({ seed, background: ['conservatory', 'discovered', 'stage', 'family'][seed % 4] });
  const marks = [];
  let q = 0;
  while (!g.over && q < quarters) {
    g.call('tickPending');
    if (g.blocksBooked < 4) {
      const board = g.call('openBoard');
      const pick = defaultPolicy.chooseRole(g, board);
      if (pick) {
        // Exercise the pull layer too, so the journal covers leverage.
        if (q % 7 === 0) {
          const moves = g.moves({ role: pick });
          if (moves.length) g.call('do', [moves[0].action.id, Game.ctxRef({ role: pick })]);
        }
        if (q % 5 === 0) g.call('decline', [pick.id]);
        else {
          const res = g.call('pursue', [pick.id]);
          if (res.cast) {
            g.call('filmFor', [pick.id]);
            g.call('shoot', [{
              prep: defaultPolicy.choosePrep(g, pick),
              positions: defaultPolicy.choosePositions(g, pick),
              moments: defaultPolicy.chooseMoments(g, pick),
            }]);
          }
        }
      }
    }
    g.call('tickQuarter');
    if (g.world.quarter === 1) g.call('endYear');
    if (q % 11 === 0) g.call('orders', [{ stance: q % 22 === 0 ? 'generous' : 'showy' }]);
    marks.push(g.fingerprint());
    q += 1;
  }
  return { game: g, marks };
}

const n = Number(process.argv[2] || 25);
let ok = 0;
const failures = [];
for (let seed = 1; seed <= n; seed++) {
  const { game, marks } = play(seed);
  const data = JSON.parse(JSON.stringify(game.save()));
  const loaded = Game.load(data);
  if (loaded.fingerprint() === game.fingerprint()) ok += 1;
  else {
    failures.push({
      seed,
      journal: data.journal.length,
      original: game.fingerprint(),
      replayed: loaded.fingerprint(),
    });
  }
  // A save is also expected to survive a second round trip.
  if (seed === 1) {
    const again = Game.load(JSON.parse(JSON.stringify(loaded.save())));
    if (again.fingerprint() !== game.fingerprint()) {
      failures.push({ seed, note: 'second round trip diverged' });
    }
  }
  void marks;
}

console.log(`\nsave / replay — ${ok}/${n} careers rebuilt identically`);
for (const f of failures.slice(0, 3)) {
  console.log('  seed %s (%s calls)\n    was %s\n    got %s',
    f.seed, f.journal, f.original, f.replayed);
}
console.log('');
process.exitCode = failures.length ? 1 : 0;
