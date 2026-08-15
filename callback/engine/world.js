// The world the career happens inside: genre demand cycles, a persistent
// Rolodex of directors and casting directors who age and have their own
// careers, and the project generator that fills the offer board.

import { RNG, clamp } from './rng.js';
import {
  GENRES, GENRE_ECON, ARCHETYPES, DIALS, PROJECT_TYPES, GATEKEEPERS,
  BILLING_DIFFICULTY, FIRST_NAMES, LAST_NAMES, TITLE_A, TITLE_B, TITLE_SOLO, SHAPES,
} from './data.js';

// Instance-scoped so a replayed world hands out exactly the same ids.
const makeIds = () => { let n = 0; return () => `id${++n}`; };

export class World {
  constructor(rng, startYear = 1974) {
    this.rng = rng;
    this.nextId = makeIds();
    this.usedTitles = new Set();
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
    this.scandals = [];
    this.landmarks = [];
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

  // Two films in one career must never share a title, or the log reads as if
  // a picture was reviewed before it was cast.
  title() {
    for (let attempt = 0; attempt < 24; attempt++) {
      const t = this.rng.chance(0.12)
        ? this.rng.pick(TITLE_SOLO)
        : `${this.rng.pick(TITLE_A)} ${this.rng.pick(TITLE_B)}`;
      if (!this.usedTitles.has(t)) { this.usedTitles.add(t); return t; }
    }
    const t = `${this.rng.pick(TITLE_A)} ${this.rng.pick(TITLE_B)} ${this.rng.int(2, 4)}`;
    this.usedTitles.add(t);
    return t;
  }

  _makeDirector() {
    const rng = this.rng;
    return {
      id: this.nextId(),
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
      id: this.nextId(),
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
      id: this.nextId(),
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
    if (this.quarter > 4) {
      this.quarter = 1;
      this.year += 1;
      this._ageWorld();
      this.tickLandmarks();
      this.tickScandals(this.rng);
    }
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

  // A landmark permanently adds its palette to the world's coherence set, the
  // copies that follow feed the genre boom, and in about eight years the thing
  // you invented is a cliche you have to work against (§5.4). You get to watch
  // that happen to your own film.
  addShape(name, palette, genre, author) {
    const key = name.toLowerCase().replace(/[^a-z]+/g, '_');
    this.shapes[key] = { ...palette };
    this.momentum[genre] = (this.momentum[genre] || 0) + 2.5;
    const landmark = {
      key, name, genre, author, year: this.year, copies: 0, cliche: false,
    };
    this.landmarks.push(landmark);
    return landmark;
  }

  // Other directors copy what worked, then keep copying it.
  tickLandmarks() {
    for (const l of this.landmarks) {
      const age = this.year - l.year;
      if (age > 0 && age <= 10 && this.rng.chance(0.35)) {
        l.copies += 1;
        this.momentum[l.genre] += 0.35;
      }
      if (!l.cliche && (age >= 8 || l.copies >= 7)) {
        l.cliche = true;
        l.clicheYear = this.year;
      }
    }
  }

  // Is this palette now a tired copy of something? Critics can tell.
  clicheePenalty(palette) {
    let worst = 0;
    for (const l of this.landmarks) {
      if (!l.cliche) continue;
      const shape = this.shapes[l.key];
      if (!shape) continue;
      let sum = 0;
      for (const d of DIALS) sum += (palette[d] - shape[d]) ** 2;
      const dist = Math.sqrt(sum / DIALS.length);
      if (dist < 16) worst = Math.max(worst, 7 * (1 - dist / 16));
    }
    return worst;
  }

  // §9.4 the script market. Material exists whether or not anyone is making it.
  generateScript(rng, actor, opts = {}) {
    const genre = opts.genre || rng.pick(GENRES);
    const quality = clamp(rng.gauss(opts.quality ?? 60, 14), 20, 98);
    return {
      id: this.nextId(),
      title: this.title(),
      genre,
      quality,
      source: rng.pick(['original', 'novel', 'play', 'true story', 'short story']),
      charAge: clamp(Math.round(actor.age + rng.gauss(1, 5)), 14, 88),
      archetype: rng.pick(ARCHETYPES),
      askingBudget: clamp(GENRE_ECON[genre].budget * rng.float(0.4, 1.4), 1, 180),
      optioned: this.year,
      shopped: false,
      financingChance: 0,
      attachedDirector: null,
    };
  }

  // What the trades would print at the end of a year. No decisions in here —
  // it exists so the world is legible as something moving on its own, which is
  // most of what makes a simulation feel inhabited.
  tradePaper(game, seedRng) {
    // Its own stream: the trades are read whenever the player feels like it,
    // and anything the interface can call at will must not touch the sequence
    // the save file replays.
    const rng = new RNG((game.seed ^ (this.year * 2654435761)) >>> 0);
    void seedRng;
    const lines = [];
    const sorted = GENRES.slice().sort((a, b) => this.demand[b] - this.demand[a]);
    const hot = sorted[0];
    const cold = sorted[sorted.length - 1];
    const mom = this.momentum[hot];
    lines.push(mom > 1.5
      ? `Everyone is making ${hot} pictures. Demand ${this.demand[hot].toFixed(0)} and climbing, and the greenlights from two years ago are still arriving.`
      : mom < -1.5
        ? `The ${hot} boom is over. Four of them opened this year and three of them lost money.`
        : `${hot[0].toUpperCase()}${hot.slice(1)} is what sells this year. Nobody will finance ${cold}.`);

    const recent = this.landmarks.filter((l) => this.year - l.year <= 3);
    if (recent.length) {
      const l = recent[recent.length - 1];
      lines.push(l.author === game.actor.name
        ? `${l.name} has been copied ${l.copies} times since you made it.`
        : `Everyone is trying to shoot like ${l.name} now. ${l.copies} of them so far.`);
    }
    const tired = this.landmarks.filter((l) => l.cliche && this.year - (l.clicheYear || 0) <= 2);
    if (tired.length) {
      lines.push(`Critics have started using "${tired[0].name}-ish" as an insult.`);
    }

    for (const s of this.scandals) {
      lines.push(`${s.person.name} ${s.kind}${s.defendedBy ? `, and ${s.defendedBy} said so out loud` : ''}.`);
    }

    const retiring = this.directors.filter((d) => d.retired);
    if (retiring.length && rng.chance(0.5)) {
      lines.push(`${rng.pick(retiring).name} is not making another one.`);
    }

    const rising = this.costars.filter((c) => c.heat > 70).sort((a, b) => b.heat - a.heat)[0];
    if (rising) lines.push(`${rising.name} is suddenly in everything.`);

    return lines.slice(0, 5);
  }

  makeNewcomer(rng) {
    const c = this._makeCostar();
    c.age = rng.int(19, 25);
    c.heat = rng.float(0, 6);
    c.newcomer = true;
    this.costars.push(c);
    return c;
  }

  // Somebody is always in trouble. You can say something, or not.
  tickScandals(rng) {
    this.scandals = this.scandals.filter((s) => this.year - s.year < 2);
    if (this.scandals.length < 2 && rng.chance(0.16)) {
      const pool = [...this.directors.filter((d) => !d.retired), ...this.costars];
      const person = pool[rng.int(0, pool.length - 1)];
      this.scandals.push({
        person,
        year: this.year,
        kind: rng.pick([
          'is being sued by a former assistant',
          'said something unforgivable in a magazine',
          'walked off a picture and will not say why',
          'is being written about by four reporters at once',
        ]),
      });
    }
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
    const ageLead = clamp(1 - Math.max(0, (actor.age - 40)) * 0.14, 0.04, 1) + 0.18 * s;
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
    // §4.2 the typecasting engine, on the offer side. The more legible you are,
    // the more the board is just your lane again — which is the flood of work
    // and the cage, in one number. An illegible actor gets a varied board and
    // fewer offers on it.
    const leg = clamp(actor.legibilityValue ?? 0, 0, 100);
    const inLane = rng.chance(0.18 + 0.006 * leg);
    const genre = inLane
      ? rng.weighted(GENRES.map((g) => [g, 0.4 + (actor.persona?.genre?.[g] ?? 10) / 12]))
      : rng.weighted(GENRES.map((g) => [g, 0.5 + this.demand[g] / 40]));
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
    const archetype = inLane
      ? rng.weighted(ARCHETYPES.map((x) => [x, 0.4 + (actor.persona?.archetype?.[x] ?? 10) / 12]))
      : rng.pick(ARCHETYPES);
    const share = billing === 'lead' ? 0.14 : billing === 'supporting' ? 0.06 : 0.015;

    return {
      id: this.nextId(),
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
