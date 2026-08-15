// The world the career happens inside: genre demand cycles, a persistent
// Rolodex of directors and casting directors who age and have their own
// careers, and the project generator that fills the offer board.

import { RNG, clamp } from './rng.js';
import {
  GENRES, GENRE_ECON, ARCHETYPES, DIALS, PROJECT_TYPES, GATEKEEPERS,
  BILLING_DIFFICULTY, FIRST_NAMES, LAST_NAMES, TITLE_A, TITLE_B, SHAPES,
} from './data.js';

let uid = 0;
const nextId = () => `id${++uid}`;

export class World {
  constructor(rng, startYear = 1974) {
    this.rng = rng;
    this.year = startYear;
    this.startYear = startYear;
    this.quarter = 1;
    this.demand = {};
    this.momentum = {};
    this.greenlightQueue = {};
    for (const g of GENRES) {
      this.demand[g] = GENRE_ECON[g].demand;
      this.momentum[g] = 0;
      this.greenlightQueue[g] = [];
    }
    this.shapes = { ...SHAPES };
    this.directors = [];
    this.castingDirectors = [];
    this.costars = [];
    this._populate();
  }

  _populate() {
    for (let i = 0; i < 12; i++) this.directors.push(this._makeDirector());
    for (let i = 0; i < 6; i++) this.castingDirectors.push(this._makeCastingDirector());
    for (let i = 0; i < 10; i++) this.costars.push(this._makeCostar());
  }

  name() {
    return `${this.rng.pick(FIRST_NAMES)} ${this.rng.pick(LAST_NAMES)}`;
  }

  title() {
    return `${this.rng.pick(TITLE_A)} ${this.rng.pick(TITLE_B)}`;
  }

  _makeDirector() {
    const rng = this.rng;
    return {
      id: nextId(),
      kind: 'director',
      name: this.name(),
      age: rng.int(28, 66),
      craft: clamp(rng.gauss(58, 15), 10, 98),
      vision: clamp(rng.gauss(55, 18), 5, 98),
      taste: clamp(rng.gauss(55, 16), 5, 98),
      command: clamp(rng.gauss(52, 16), 5, 98),
      prestige: clamp(rng.gauss(48, 20), 2, 98),
      temperament: rng.pick(['generous', 'exacting', 'chaotic', 'remote']),
      lane: rng.pick(GENRES),
      affinity: 0,
      grudge: 0,
      sharedProjects: 0,
      retired: false,
    };
  }

  _makeCastingDirector() {
    const rng = this.rng;
    return {
      id: nextId(),
      kind: 'casting',
      name: this.name(),
      // What this room rewards. You learn it by being in it.
      prefers: rng.pick(['bold', 'restrained', 'exact', 'warm']),
      memory: {},
      affinity: 0,
    };
  }

  _makeCostar() {
    const rng = this.rng;
    return {
      id: nextId(),
      kind: 'costar',
      name: this.name(),
      age: rng.int(22, 58),
      craft: clamp(rng.gauss(55, 16), 10, 96),
      instinct: clamp(rng.gauss(52, 18), 5, 96),
      presence: clamp(rng.gauss(55, 16), 5, 96),
      ego: clamp(rng.gauss(50, 22), 0, 100),
      heat: clamp(rng.gauss(30, 20), 0, 95),
      affinity: 0,
      grudge: 0,
      sharedProjects: 0,
    };
  }

  // §10.6 eras. Budgets and fees are held in start-year dollars throughout, so
  // a forty-year career's earnings mean one thing end to end; the era curve is
  // reserved for the technology shifts in §10.6 rather than for inflation.
  get eraMultiplier() {
    return 1;
  }

  // §7.3 the bridge from the director's attributes to the actor's model.
  directorSkill(d) {
    return clamp(0.45 * d.craft + 0.30 * d.vision + 0.25 * d.command, 0, 100);
  }

  // §7.7 how well the film comes together in post. The doc's version made the
  // average NPC director worse than the blind N(52,14) roll the reception model
  // was tuned against; re-centred so the population mean lands on 52.
  postSkill(d) {
    return clamp(52 + 0.30 * (d.craft - 58) + 0.25 * (d.taste - 55), 0, 100);
  }

  // §9.3 genre cycles. Greenlights lag demand by eight quarters, which is where
  // the overshoot comes from — the boom is always being fed by decisions made
  // two years ago.
  tickQuarter() {
    for (const g of GENRES) {
      const econ = GENRE_ECON[g];
      const queued = this.greenlightQueue[g];
      const arriving = queued.shift() || 0;
      const supplyPressure = arriving * 0.9;
      const pull = 0.06 * (econ.demand - this.demand[g]);
      this.momentum[g] = clamp(
        0.82 * this.momentum[g] + pull - supplyPressure + this.rng.gauss(0, 1.1) * econ.vol,
        -12, 12,
      );
      this.demand[g] = clamp(this.demand[g] + this.momentum[g], 8, 96);
      while (queued.length < 8) queued.push(0);
      // What the market greenlights now shows up in two years.
      queued[7] = clamp((this.demand[g] - econ.demand) / 18, -1.5, 2.5);
    }
    this.quarter += 1;
    if (this.quarter > 4) { this.quarter = 1; this.year += 1; this._ageWorld(); }
  }

  _ageWorld() {
    for (const d of this.directors) {
      d.age += 1;
      if (d.age > 70 && this.rng.chance(0.12)) d.retired = true;
      d.prestige = clamp(d.prestige - 0.6, 0, 100);
      if (d.retired && this.rng.chance(0.3)) {
        Object.assign(d, this._makeDirector(), { id: d.id });
      }
    }
    for (const c of this.costars) {
      c.age += 1;
      c.heat = clamp(c.heat * 0.92 + this.rng.gauss(3, 6), 0, 100);
    }
  }

  // A landmark permanently adds its palette to the world's coherence set, and
  // the copies that follow feed the genre boom (§5.4).
  addShape(name, palette) {
    this.shapes[name] = { ...palette };
    this.momentum[palette.genre] = (this.momentum[palette.genre] || 0) + 2;
  }

  randomPalette(rng, genre, budget, directorTaste) {
    // Directors gravitate toward a shape and then push it. Money constrains
    // scale: a $5M film cannot be epic.
    const shape = rng.pick(Object.values(this.shapes));
    const spread = clamp(34 - 0.22 * directorTaste, 8, 34);
    const p = {};
    for (const d of DIALS) p[d] = clamp(shape[d] + rng.gauss(0, spread), -50, 50);
    p.scale = clamp(Math.min(p.scale, -40 + 26 * Math.log10(Math.max(1, budget))), -50, 50);
    return p;
  }

  generateRole(actor, opts = {}) {
    const rng = this.rng;
    // What the board offers you tracks who the industry thinks you are. Nobody
    // sends a star a bit part, and nobody sends an unknown a lead.
    const s = clamp(actor.standingScalar ?? 0, 0, 100) / 100;
    // §4.9 the cliff. Lead offers thin out from the early forties, and only
    // standing buys you past it — which is what makes the pivot to character
    // and authority roles a real strategic problem rather than a mood.
    const ageLead = clamp(1 - Math.max(0, (actor.age - 40)) * 0.058, 0.14, 1) + 0.42 * s;
    const billing = opts.billing || rng.weighted([
      ['lead', (0.04 + 1.30 * Math.pow(s, 1.8)) * ageLead],
      ['supporting', 0.34 + 0.30 * s],
      ['bit', Math.max(0.05, 0.60 - 0.55 * s)],
    ]);
    // Scale tracks standing too. Nobody hands a $180M film to a stranger, and
    // the tentpole board is where the game's money actually is.
    const type = rng.weighted([
      ['indie', Math.max(0.06, 0.28 - 0.18 * s)],
      ['studio', 0.30],
      ['tentpole', 0.02 + 0.40 * Math.pow(s, 1.5)],
      ['streaming', 0.14], ['tv_season', 0.08],
      ['theatre', 0.06], ['voice', 0.06],
    ]);
    const genre = rng.weighted(GENRES.map((g) => [g, 0.5 + this.demand[g] / 40]));
    const econ = GENRE_ECON[genre];
    // Budgets are nominal, so they inflate with the era exactly as fees do.
    const era = this.eraMultiplier;
    const budget = clamp(
      econ.budget * PROJECT_TYPES[type].budgetMult * rng.float(0.5, 1.7), 0.4, 400,
    ) * era;
    const gatekeeper = type === 'tentpole' ? 'tentpole'
      : type === 'indie' ? (rng.chance(0.45) ? 'auteur' : 'indie')
      : type === 'streaming' ? 'streamer'
      : type === 'tv_season' ? 'network'
      : rng.chance(0.2) ? 'franchise' : 'tentpole';

    const director = rng.pick(this.directors.filter((d) => !d.retired)) || this.directors[0];
    const charAge = clamp(
      Math.round(actor.age + rng.gauss(billing === 'bit' ? 0 : 2, 7)), 8, 88,
    );
    const archetype = rng.pick(ARCHETYPES);
    const share = billing === 'lead' ? 0.14 : billing === 'supporting' ? 0.06 : 0.015;

    return {
      id: nextId(),
      title: this.title(),
      genre, type, billing, gatekeeper, archetype, charAge,
      blocks: PROJECT_TYPES[type].blocks,
      label: PROJECT_TYPES[type].label,
      budget,
      budgetForRole: Math.max(0.05, budget * share),
      difficulty: BILLING_DIFFICULTY[billing]
        + (type === 'tentpole' ? 6 : type === 'indie' ? -6 : 0),
      typeStrictness: clamp(rng.gauss(0.55, 0.22), 0.1, 1.0),
      scriptQuality: clamp(rng.gauss(58, 17), 5, 98),
      chaos: clamp(rng.gauss(45, 20), 0, 100),
      director,
      castingDirector: rng.pick(this.castingDirectors),
      costar: rng.pick(this.costars),
      gates: this._gatesFor(genre, archetype, rng),
      union: type !== 'indie' || rng.chance(0.5),
      demand: this.demand[genre],
      era,
      realBudget: budget / era,
    };
  }

  _gatesFor(genre, archetype, rng) {
    const g = {};
    if (genre === 'action' || genre === 'period') g.physicality = rng.int(45, 80);
    if (genre === 'musical' || genre === 'period') g.voice = rng.int(45, 80);
    if (archetype === 'romantic_lead' || archetype === 'ingenue') g.look = rng.int(50, 82);
    return g;
  }
}

export function makeWorld(seed, startYear) {
  return new World(new RNG(seed ^ 0x5f3a), startYear);
}

export { GATEKEEPERS };
