// The game loop. One quarter at a time, forever, until you stop working.
//
// Everything the player touches goes through this class, and the sim harness
// drives the same methods with a policy instead of a person — so the numbers
// in sim/career-sim.mjs are the numbers the game produces.

import { RNG, clamp } from './rng.js';
import { World } from './world.js';
import {
  GENRES, ARCHETYPES, AGENT_TIERS, BILLING_WEIGHT, PERF_DIALS, PROJECT_TYPES,
} from './data.js';
import * as M from './model.js';

// ---------------------------------------------------------------------------
// FIX-5 Character creation. Eight versions of the document never specified how
// a run starts; these are the four openings, and they differ in what they are
// short of, not in how good they are.
// ---------------------------------------------------------------------------
export const BACKGROUNDS = {
  conservatory: {
    label: 'Conservatory',
    blurb: 'Three years of technique and a graduating showcase nobody important came to.',
    age: 24,
    attrs: { craft: 62, instinct: 44, presence: 48, resilience: 50 },
    money: 0.004, agent: 'boutique', unionCredits: 0, recognition: 4,
  },
  discovered: {
    label: 'Discovered',
    blurb: 'A photographer, then a commercial, then a manager who calls constantly. You have never had a lesson.',
    age: 20,
    attrs: { craft: 28, instinct: 52, presence: 70, resilience: 40 },
    money: 0.02, agent: 'midtier', unionCredits: 1, recognition: 14,
  },
  stage: {
    label: 'Regional stage',
    blurb: 'Eleven years of Chekhov in a converted church. Nobody films in this town.',
    age: 33,
    attrs: { craft: 70, instinct: 55, presence: 44, resilience: 62 },
    money: 0.01, agent: 'none', unionCredits: 2, recognition: 8,
  },
  family: {
    label: 'Family money',
    blurb: 'The rent is not a problem. Everyone can tell, including the room.',
    age: 26,
    attrs: { craft: 42, instinct: 48, presence: 55, resilience: 34 },
    money: 1.2, agent: 'midtier', unionCredits: 0, recognition: 6,
  },
};

export const PREP_OPTIONS = {
  table: { label: 'Table work with a coach', weeks: 2, base: 62, craft: 0.4 },
  research: { label: 'Research the world', weeks: 3, base: 58, periodBonus: 16 },
  dialect: { label: 'Dialect coach', weeks: 4, base: 60, clearsGate: 'voice' },
  physical: { label: 'Physical transformation', weeks: 8, base: 72, clearsGate: 'physicality', health: -6, resilience: -1.5, flag: 'transformation' },
  method: { label: 'Live it', weeks: 8, base: 82, resilience: -8, flag: 'transformation', strain: true },
  wing: { label: 'Wing it', weeks: 0, base: 20 },
};

// §5.12 the three moments on set. Each is a real trade, not flavour.
export const MOMENTS = [
  {
    id: 'not_working',
    prompt: 'The scene is not working. Sixth take, and everyone knows.',
    options: [
      { id: 'suggest', label: 'Suggest a change', effect: { chemistry: -4, prep: +8, affinity: -3 }, needs: 'instinct' },
      { id: 'absorb', label: 'Take the note and give them what they asked for', effect: { chemistry: +4, prep: -2, affinity: +4 } },
      { id: 'ask', label: 'Ask the director what they actually want', effect: { prep: +4, condition: -2, affinity: +2 } },
    ],
  },
  {
    id: 'adjustment',
    prompt: 'The adjustment is wrong. You are sure of it, and you might be wrong about that.',
    options: [
      { id: 'take', label: 'Take it', effect: { affinity: +6, perf: -3 } },
      { id: 'argue', label: 'Argue for yours', effect: { affinity: -7, perf: +5, chemistry: -3 } },
      { id: 'both', label: 'Give them both and let the edit decide', effect: { condition: -5, perf: +2, affinity: +1 } },
    ],
  },
  {
    id: 'discovery',
    prompt: 'Something happened in the rehearsal that is not in the script.',
    options: [
      { id: 'keep', label: 'Keep it. Play it in the take.', effect: { perf: +6, ensemble: -2, condition: -2 } },
      { id: 'offer', label: 'Offer it to your scene partner instead', effect: { perf: -1, ensemble: +4, affinity: +8, favour: 1 } },
      { id: 'lose', label: 'Let it go. It was a rehearsal thing.', effect: {} },
    ],
  },
];

export class Game {
  constructor(opts = {}) {
    const seed = opts.seed ?? Math.floor(Math.random() * 1e9);
    this.seed = seed;
    this.rng = new RNG(seed);
    this.world = new World(new RNG(seed ^ 0x5f3a), opts.startYear ?? 1974);
    this.log = [];
    this.actor = this._makeActor(opts.background ?? 'conservatory', opts.name);
    this.board = [];
    this.pending = [];        // projects shot but not yet released
    this.credits = [];
    this.awards = { nominations: 0, wins: 0, thisSeason: [] };
    this.money = { net: this.actor.money, floor: 0.02, lifetime: 0 };
    this.blocksBooked = 0;    // blocks used in the current year
    this.yearBilling = null;  // best billing worked this year, drives decay
    this.idleYears = 0;
    this.over = false;
    this.obituaryText = null;
    this.stats = { peakHeat: 0, leadCredits: 0, leadsAfter42: 0, yearsActive: 0 };
  }

  _makeActor(backgroundKey, name) {
    const bg = BACKGROUNDS[backgroundKey] || BACKGROUNDS.conservatory;
    const rng = this.rng;
    const jitter = (v, sd = 7) => clamp(rng.gauss(v, sd), 5, 95);
    const genre = {}; for (const g of GENRES) genre[g] = clamp(rng.gauss(12, 6), 0, 100);
    const archetype = {}; for (const a of ARCHETYPES) archetype[a] = clamp(rng.gauss(12, 6), 0, 100);

    return {
      name: name || this.world.name(),
      background: backgroundKey,
      age: bg.age,
      attrs: {
        craft: jitter(bg.attrs.craft),
        instinct: jitter(bg.attrs.instinct, 12),
        presence: jitter(bg.attrs.presence),
        resilience: jitter(bg.attrs.resilience),
      },
      gates: {
        look: clamp(rng.gauss(bg.label === 'Discovered' ? 68 : 52, 16), 5, 98),
        voice: clamp(rng.gauss(52, 15), 5, 98),
        physicality: clamp(rng.gauss(52, 15), 5, 98),
      },
      standing: { heat: 2, prestige: 3, affection: 2, notoriety: 0 },
      persona: { genre, archetype },
      recognition: bg.recognition,
      unionCredits: bg.unionCredits,
      agent: bg.agent,
      health: 92,
      condition: 88,
      money: bg.money,
      favours: 0,
      quote: 0.05,
      recentRoi: 1,
      consecutiveSameLane: 0,
      lastLane: null,
      flags: {},
      lastWorkedYear: null,
    };
  }

  // ------------------------------------------------------------------ getters
  get year() { return this.world.year; }
  get quarter() { return this.world.quarter; }
  get standing() { return M.standing(this.actor.standing); }
  get legibility() { return M.legibility(this.actor.persona); }
  get agentTier() { return AGENT_TIERS[this.actor.agent]; }

  say(text, kind = 'note') {
    this.log.push({ year: this.year, quarter: this.quarter, kind, text });
    if (this.log.length > 400) this.log.shift();
    return text;
  }

  // ------------------------------------------------------------- offer board
  openBoard() {
    const a = this.actor;
    a.quote = M.quote(a.standing, a.recentRoi, this.world.eraMultiplier);
    const sp = M.starPower(a.standing);
    a.standingScalar = M.standing(a.standing) + 0.35 * a.recognition;
    const band = this._ageBand(a.age);
    // Some quarters the phone does not ring. That has to be possible or the
    // career has no downside and every run converges on the same shape.
    const count = clamp(
      Math.round((0.4 + sp / 10 + a.recognition / 30 + this.agentTier.offers) * band),
      0, 9,
    );

    const listings = [];
    for (let i = 0; i < count; i++) {
      const role = this.world.generateRole(a);
      // The union catch-22, made passable: non-union work exists, pays badly,
      // and is how the first three credits happen (§10.1, review §4).
      if (role.union && a.unionCredits < 3 && !this.rng.chance(0.25)) {
        role.union = false;
        role.budget *= 0.35;
        role.budgetForRole *= 0.35;
        role.difficulty -= 8;
        role.nonUnionNote = true;
      }
      const rel = this._relationshipBonus(role);
      const u = M.utility(a, role, rel);
      const p = M.offerProbability(u, role.difficulty);
      listings.push({
        ...role,
        utility: u,
        chance: p,
        path: M.castingPath(u, role, rel),
        relationshipBonus: rel,
        fit: M.fitScore(a, role),
      });
    }
    // The board is sorted the way an agent would present it.
    listings.sort((x, y) => (y.chance * BILLING_WEIGHT[y.billing]) - (x.chance * BILLING_WEIGHT[x.billing]));
    this.board = listings;
    return listings;
  }

  _ageBand(age) {
    return age < 28 ? 1.30 : age < 39 ? 1.45 : age < 49 ? 1.05 : age < 61 ? 0.72 : 0.42;
  }

  _relationshipBonus(role) {
    let bonus = 0;
    const d = role.director;
    if (d) bonus += 0.30 * Math.max(0, d.affinity) - 0.55 * d.grudge;
    const c = role.castingDirector;
    if (c) bonus += 0.18 * Math.max(0, c.affinity);
    return clamp(bonus, -30, 40);
  }

  // Attempt a role. Returns { cast, path, role, note }.
  pursue(roleId) {
    const role = this.board.find((r) => r.id === roleId);
    if (!role) return { cast: false, note: 'That listing is gone.' };
    // One shot per listing. You cannot re-audition for the part you lost.
    this.board = this.board.filter((r) => r.id !== roleId);
    if (this.blocksBooked + role.blocks > 4) {
      return { cast: false, note: 'The dates do not work. You are shooting.' };
    }
    if (role.union && this.actor.unionCredits < 3) {
      return { cast: false, note: 'Union production. You need three union credits and you have ' + this.actor.unionCredits + '.' };
    }

    if (role.path === 'direct') {
      this.say(`${role.director.name} offered you ${role.title} outright.`, 'good');
      return { cast: true, path: 'direct', role };
    }
    if (role.path === 'offer') {
      this.say(`An offer, no audition: ${role.title}.`, 'good');
      return { cast: true, path: 'offer', role };
    }
    // You are not the only person who can do this. Every audition is against a
    // field, and the field gets better as the part gets better.
    const field = role.billing === 'lead' ? M.K.fieldLead
      : role.billing === 'supporting' ? M.K.fieldSupporting : M.K.fieldBit;
    const won = this.rng.chance(role.chance * field);
    role.castingDirector.memory[this.actor.name] = (role.castingDirector.memory[this.actor.name] || 0) + 1;
    if (won) {
      role.castingDirector.affinity = clamp(role.castingDirector.affinity + 4, -100, 100);
      this.say(`You read for ${role.title} and got it.`, 'good');
      return { cast: true, path: 'audition', role };
    }
    role.castingDirector.affinity = clamp(role.castingDirector.affinity + 1, -100, 100);
    this.say(`You read for ${role.title}. They went another way.`, 'bad');
    return { cast: false, path: 'audition', role };
  }

  // ------------------------------------------------------------------- shoot
  // Books the calendar, resolves prep, the three moments and the performance,
  // then queues the film for release. Positions are the player's creative call.
  shoot(role, choices = {}) {
    const a = this.actor;
    const prepChoice = PREP_OPTIONS[choices.prep] || PREP_OPTIONS.table;
    const positions = choices.positions || { energy: 'with', volume: 'with', warmth: 'with', speed: 'with' };
    const momentChoices = choices.moments || {};

    this.blocksBooked += role.blocks;
    a.lastWorkedYear = this.year;
    this.stats.yearsActive = this.stats.yearsActive; // set at year end
    if (!this.yearBilling || BILLING_WEIGHT[role.billing] > BILLING_WEIGHT[this.yearBilling]) {
      this.yearBilling = role.billing;
    }

    let prep = clamp(prepChoice.base * (0.8 + 0.004 * a.attrs.resilience), 0, 100);
    if (prepChoice.periodBonus && (role.genre === 'period' || role.archetype === 'authority')) {
      prep += prepChoice.periodBonus;
    }
    if (prepChoice.craft) a.attrs.craft = clamp(a.attrs.craft + prepChoice.craft, 5, 99);
    if (prepChoice.resilience) a.attrs.resilience = clamp(a.attrs.resilience + prepChoice.resilience, 5, 99);
    if (prepChoice.health) a.health = clamp(a.health + prepChoice.health, 0, 100);
    if (prepChoice.flag) a.flags[prepChoice.flag] = this.year;

    const director = role.director;
    const dSkill = this.world.directorSkill(director);
    const command = clamp(director.command + 0.25 * Math.max(0, director.affinity), 0, 100);

    let chemistry = clamp(this.rng.gauss(58, 16) + 0.2 * Math.max(0, role.costar.affinity) - 0.3 * role.costar.ego / 10, 0, 100);
    let condition = clamp(a.condition - 0.25 * role.chaos + 0.3 * a.attrs.resilience - 12 * (this.blocksBooked / 4), 20, 100);
    let perfNudge = 0, ensembleNudge = 0;

    const momentLog = [];
    for (const moment of MOMENTS) {
      const pickId = momentChoices[moment.id] || moment.options[1].id;
      const opt = moment.options.find((o) => o.id === pickId) || moment.options[1];
      const e = opt.effect;
      chemistry = clamp(chemistry + (e.chemistry || 0), 0, 100);
      prep = clamp(prep + (e.prep || 0), 0, 100);
      condition = clamp(condition + (e.condition || 0), 0, 100);
      perfNudge += e.perf || 0;
      ensembleNudge += e.ensemble || 0;
      if (e.affinity) director.affinity = clamp(director.affinity + e.affinity, -100, 100);
      if (e.favour) a.favours += e.favour;
      momentLog.push({ moment: moment.id, chose: opt.label });
    }

    const palette = role.palette || this.world.randomPalette(this.rng, role.genre, role.budget, director.taste);
    const coh = M.coherence(palette);
    const film = { palette, coherence: coh.value, nearest: coh.nearest };

    const fit = M.fitScore(a, role);
    const perf = M.performance(this.rng, {
      actor: a, role, film, prep, chemistry, condition,
      directorSkill: dSkill, fit,
    });
    perf.value = clamp(perf.value + perfNudge, 0, 100);

    const resolved = M.resolvePositions(positions, {
      genre: role.genre,
      craft: a.attrs.craft,
      directorCommand: command,
      partnerPositions: this._costarPositions(role),
    });
    resolved.forFilm += ensembleNudge;

    const shaped = M.shapePerformance(perf.value, resolved, a.attrs.presence);

    // §5.4 a landmark rewrites what films are, permanently.
    const skill = (a.attrs.craft + director.vision) / 2;
    const landmark = this.rng.chance(M.landmarkChance(coh.value, skill));
    if (landmark) this.world.addShape(`${role.title.toLowerCase().replace(/\s+/g, '_')}`, palette);

    // Condition and health carry out of the shoot.
    a.condition = clamp(condition + 6, 10, 100);
    if (role.genre === 'action' && this.rng.chance(0.06 + 0.002 * (60 - a.gates.physicality))) {
      a.health = clamp(a.health - this.rng.int(4, 16), 0, 100);
      this.say('An injury on the second unit. It will be fine. It is mostly fine.', 'bad');
    }

    const project = {
      role, film, palette, prep, chemistry, condition, positions, resolved, shaped,
      perf, landmark, directorSkill: dSkill, director,
      releaseIn: this.rng.int(2, 5),
      prepFlag: prepChoice.flag || null,
      momentLog,
    };
    this.pending.push(project);
    a.unionCredits += role.union ? 1 : 0;
    this.credits.push({ title: role.title, year: this.year, billing: role.billing, genre: role.genre });

    // The deal, paid on signature.
    const income = M.fee(this.rng, a, role, this.agentTier, a.recentRoi, this.world.eraMultiplier);
    M.applyLifestyle(this.money, income);
    project.fee = income;

    this.say(
      `${role.title} — ${role.billing}, ${role.label}, ${director.name} directing. ` +
      `${this._qualitativeRead(perf.value, director)}`,
      'work',
    );
    return project;
  }

  _costarPositions(role) {
    // Ego decides how much space your scene partner takes.
    const p = {};
    for (const d of PERF_DIALS) {
      p[d] = role.costar.ego > 70
        ? this.rng.pick(['beyond', 'against', 'with'])
        : this.rng.pick(['with', 'with', 'beneath']);
    }
    return p;
  }

  // §4.7 you never see the number. You see what the director's face did.
  _qualitativeRead(value, director) {
    const noisy = value + this.rng.gauss(0, director.temperament === 'remote' ? 16 : 9);
    if (noisy > 80) return 'The room went quiet after the last take.';
    if (noisy > 66) return 'They printed it and moved on, which is the compliment.';
    if (noisy > 50) return 'You got there by take nine.';
    if (noisy > 36) return 'They shot a lot of coverage on you.';
    return 'They started asking the other actor for reactions.';
  }

  // ----------------------------------------------------------------- release
  releaseDue() {
    return this.pending.filter((p) => p.releaseIn <= 0);
  }

  tickPending() {
    const out = [];
    for (const p of this.pending) {
      p.releaseIn -= 1;
      if (p.releaseIn <= 0) out.push(p);
    }
    this.pending = this.pending.filter((p) => p.releaseIn > 0);
    return out.map((p) => this.release(p));
  }

  release(project) {
    const a = this.actor;
    const role = project.role;

    // §4.2 staleness — critics punish repetition, audiences do not.
    const lane = `${role.genre}:${role.archetype}`;
    a.consecutiveSameLane = lane === a.lastLane ? a.consecutiveSameLane + 1 : 0;
    a.lastLane = lane;
    const staleness = Math.min(12, Math.max(0, 2 * (a.consecutiveSameLane - 2)));

    // The ensemble is the billing-weighted mean of everyone's contribution,
    // and yours is the Part 5 number — one Ensemble, one Notices (FIX-2).
    const bw = BILLING_WEIGHT[role.billing];
    // Who else is in it. §4.10's "0.80 of the ensemble is yours" is only true
    // of a two-hander; a lead still carries most of it, and a bit player is one
    // voice in a room, which is exactly the asymmetry the review asked for.
    const others = role.billing === 'lead'
      ? [{ v: clamp(this.rng.gauss(58, 14), 0, 100), w: 0.55 },
         { v: clamp(this.rng.gauss(56, 14), 0, 100), w: 0.25 }]
      : role.billing === 'supporting'
        ? [{ v: clamp(this.rng.gauss(59, 14), 0, 100), w: 1.0 },
           { v: clamp(this.rng.gauss(56, 14), 0, 100), w: 0.55 },
           { v: clamp(this.rng.gauss(54, 14), 0, 100), w: 0.2 }]
        : [{ v: clamp(this.rng.gauss(59, 14), 0, 100), w: 1.0 },
           { v: clamp(this.rng.gauss(57, 14), 0, 100), w: 0.55 },
           { v: clamp(this.rng.gauss(55, 14), 0, 100), w: 0.55 }];
    let num = project.shaped.ensembleValue * bw, den = bw;
    for (const o of others) { num += o.v * o.w; den += o.w; }
    const ensembleScore = num / den;

    // Everyone else in the cast is somebody too, and a studio pays for that.
    const castStarPower = clamp(
      0.42 * M.starPower(a.standing) * bw + 0.34 * role.costar.heat
        + 0.24 * clamp(14 + 26 * Math.log10(Math.max(1, role.realBudget ?? role.budget)), 0, 100),
      0, 100,
    );

    // Quality and reach read the film's real budget; money reads the nominal
    // one. Otherwise a 2010 mid-budget drama looks like a 1974 epic.
    const realBudget = role.realBudget ?? role.budget;
    const rec = M.reception(this.rng, {
      film: project.film,
      genre: role.genre,
      budget: realBudget,
      scriptQuality: role.scriptQuality,
      directorSkill: project.directorSkill,
      directorPrestige: project.director.prestige,
      castStarPower,
      genreDemand: this.world.demand[role.genre],
      ensembleScore,
      yourNotices: project.shaped.notices,
      billing: role.billing,
      stalenessPenalty: staleness,
      palette: project.palette,
    });

    if (project.landmark) {
      rec.filmCritic = clamp(rec.filmCritic + 14, 0, 100);
      rec.notices = clamp(rec.notices + 6, 0, 100);
    }

    const deltas = M.applyReception(a.standing, rec, role.billing, this.credits.length, role.realBudget ?? role.budget);
    M.updateRecognition(a, rec.notices, role.billing);
    M.updatePersona(a.persona, role.genre, role.archetype, role.billing, rec.audience);
    a.recentRoi = 0.6 * a.recentRoi + 0.4 * rec.roi;
    this.stats.peakHeat = Math.max(this.stats.peakHeat, a.standing.heat);
    if (role.billing === 'lead') {
      this.stats.leadCredits += 1;
      if (a.age >= 42) this.stats.leadsAfter42 += 1;
    }

    // §4.5 backend. Net points are an accounting joke; gross points are the
    // real prize, and only a high-Bankability lead is ever offered them. This
    // is where the top of the market separates from the middle.
    const bank = M.bankability(a.standing, a.recentRoi);
    if (role.billing === 'lead' && bank > 44) {
      const points = clamp((bank - 44) / M.K.grossPointsDivisor, 0, M.K.grossPointsMax);
      const gross = rec.gross * (role.era ?? 1);
      if (gross > 0) {
        M.applyLifestyle(this.money, points * gross);
        if (points * gross > 4) {
          this.say(`Your points on ${role.title} paid $${(points * gross).toFixed(1)}M.`, 'good');
        }
      }
    } else if (rec.roi > 1.6) {
      M.applyLifestyle(this.money, 0.06 * role.budgetForRole * (rec.roi - 1.6));
    }
    project.director.affinity = clamp(
      project.director.affinity + (rec.notices > 66 ? 9 : rec.notices > 52 ? 4 : -2), -100, 100,
    );
    project.director.sharedProjects += 1;

    const card = {
      project, rec, deltas, staleness,
      landmark: project.landmark,
      headline: this._headline(rec, project),
      attribution: this._attribute(rec, project),
    };
    this.say(card.headline, rec.roi > 1.2 || rec.notices > 68 ? 'good' : 'note');

    // Awards eligibility is banked for the season.
    if (role.billing !== 'bit') {
      this.awards.thisSeason.push({ project, rec, role });
    }
    return card;
  }

  _headline(rec, p) {
    const t = p.role.title;
    if (rec.roi > 2.2 && rec.notices > 66) return `${t} is a hit and you are the reason people say they liked it.`;
    if (rec.roi > 2.2) return `${t} made a great deal of money. Nobody mentions you.`;
    if (rec.roi < 0.6 && rec.notices > 68) return `${t} died on release. Your reviews are the best of your life.`;
    if (rec.roi < 0.6) return `${t} came and went in eleven days.`;
    if (rec.notices > 72) return `${t} opened modestly. Two critics single you out.`;
    if (rec.notices < 42) return `${t} opened. You are mentioned once, in a list.`;
    return `${t} opened to roughly what everyone expected.`;
  }

  // §0.3 Rule 2: every outcome ships with an attribution.
  _attribute(rec, p) {
    const parts = [];
    if (rec.wrecked) parts.push('The cut is not the film you shot.');
    if (rec.blessed) parts.push('Someone in post did you an enormous favour.');
    if (p.shaped.floorBound) parts.push('You did almost nothing and the camera stayed on you anyway.');
    if (p.resolved.overspend > 0) parts.push('You were holding more ideas than you could carry; one review says "mannered".');
    if (p.resolved.generosity > 0) parts.push('You gave your scene partner the moment. They know.');
    if (p.resolved.upstaging > 0) parts.push('You took the scene. They know that too.');
    if (rec.palette.crit < -3 && rec.palette.aud > 3) parts.push('The film is exactly what audiences wanted and exactly what critics distrust.');
    if (p.film.coherence < 35) parts.push(`It never decided what it was (coherence ${p.film.coherence.toFixed(0)}).`);
    if (p.landmark) parts.push('And people are going to be copying this for a decade.');
    if (!parts.length) parts.push('It is what it is: a film, released, absorbed.');
    return parts;
  }

  // ------------------------------------------------------------------ season
  runAwardsSeason(opts = {}) {
    const a = this.actor;
    const results = [];
    const campaignSpend = opts.campaignSpend || 0;
    if (campaignSpend > 0) {
      this.money.net -= campaignSpend;
      this.blocksBooked = Math.min(4, this.blocksBooked + 1);
    }

    for (const entry of this.awards.thisSeason) {
      const flags = {
        due: this.awards.nominations >= 3 && this.awards.wins === 0,
        transformation: entry.project.prepFlag === 'transformation',
        comeback: this._wasCold(),
        finalBow: a.age >= 70,
        newcomer: this.awards.nominations === 0 && a.age < 28,
        tooCommercial: this._recentTentpoles() >= 2,
        overexposed: this.awards.thisSeason.length >= 4,
      };
      const buzz = M.buzzScore(this.rng, {
        notices: entry.rec.notices,
        filmCritic: entry.rec.filmCritic,
        campaignSpend,
        prestige: a.standing.prestige,
        flags,
        categoryAdvantage: opts.categoryFraud && entry.role.billing === 'lead' ? 18 : 0,
      });
      if (this.rng.chance(M.nominationChance(buzz.value))) {
        this.awards.nominations += 1;
        const won = this.rng.chance(clamp(M.K.winBase + (buzz.value - 70) / 260, 0.05, 0.45));
        if (won) {
          this.awards.wins += 1;
          a.standing.prestige = clamp(a.standing.prestige + 9, 0, 100);
          a.standing.heat = clamp(a.standing.heat + 7, 0, 100);
        }
        results.push({ title: entry.project.role.title, won, narratives: buzz.narratives });
        this.say(
          won ? `You won for ${entry.project.role.title}.`
              : `Nominated for ${entry.project.role.title}.`,
          'good',
        );
        if (opts.categoryFraud && entry.role.billing === 'lead' && this.rng.chance(0.35)) {
          a.standing.notoriety = clamp(a.standing.notoriety + 6, 0, 100);
          this.say('The trades call out the category. It is not a good look.', 'bad');
        }
      }
    }
    this.awards.thisSeason = [];
    return results;
  }

  _wasCold() {
    return this.stats.coldYears >= 4;
  }

  _recentTentpoles() {
    return this.credits.filter((c) => this.year - c.year <= 3 && c.tentpole).length;
  }

  // ------------------------------------------------------------------- year
  endYear() {
    const a = this.actor;
    const worked = this.yearBilling !== null;
    if (worked) this.stats.yearsActive += 1;

    this.runAwardsSeason();

    M.decayStanding(a.standing, this.yearBilling);
    a.recognition = clamp(a.recognition * M.K.recognitionKeep, 0, 100);

    // Aging (§4.9): the look curve, the attribute curves, the cliff.
    a.age += 1;
    if (a.age > 32) a.gates.look = clamp(a.gates.look - (a.age < 45 ? 0.9 : a.age < 60 ? 1.6 : 2.2), 5, 98);
    if (a.age > 45) a.gates.physicality = clamp(a.gates.physicality - 2, 5, 98);
    if (a.age > 60) a.gates.voice = clamp(a.gates.voice - 1, 5, 98);
    if (a.age > 55) a.attrs.presence = clamp(a.attrs.presence - 0.5, 5, 99);
    else if (worked) a.attrs.presence = clamp(a.attrs.presence + 0.4, 5, 99);
    if (worked) a.attrs.craft = clamp(a.attrs.craft + this.rng.float(0.5, 2.0), 5, 99);

    // Condition, health, burnout.
    if (this.blocksBooked >= 4) {
      a.condition = clamp(a.condition - 12, 10, 100);
      if (a.condition < 40) this.say('You are running on nothing and everyone can see it.', 'bad');
    } else {
      a.condition = clamp(a.condition + 8 * (1 - this.blocksBooked / 4), 10, 100);
    }
    a.health = clamp(a.health - Math.max(0, (a.age - 45) * 0.22) + (this.blocksBooked <= 2 ? 1.5 : -0.5), 0, 100);

    // §10.1 the health-plan cliff: you qualify by working enough in a year.
    a.insured = this.blocksBooked >= 1 && this.money.lifetime > 0.02;

    // §11.6 the ratchet. The floor falls slowly and the income does not.
    this.money.floor *= 0.94;
    this.money.net -= this.money.floor * 0.6;
    if (this.money.net < 0 && !a.flags.broke) {
      a.flags.broke = this.year;
      this.say('The accountant calls. Then the accountant stops calling.', 'bad');
    }

    this.stats.coldYears = a.standing.heat < 25 ? (this.stats.coldYears || 0) + 1 : 0;

    if (!worked) {
      this.idleYears += 1;
      // People leave. Most people leave.
      const giveUp = this.idleYears >= 2
        && this.rng.chance(clamp(0.10 + 0.06 * this.idleYears - M.standing(a.standing) / 90, 0, 0.6));
      if (giveUp) this._end('You took the other job. Everyone does, eventually.');
      if (this.idleYears >= 7 && a.age > 34) this._end('The phone simply stopped.');
    } else {
      this.idleYears = 0;
    }
    if (a.age >= 80 || a.health <= 0) this._end('Age, in the end.');

    this.blocksBooked = 0;
    this.yearBilling = null;
  }

  _end(reason) {
    this.over = true;
    this.endReason = reason;
  }

  // §11.8 the obituary: the one place the private numbers become public.
  obituary() {
    const a = this.actor;
    const best = this.credits.length ? this.credits[Math.floor(this.credits.length / 2)] : null;
    const lines = [
      `${a.name}, ${a.age}. ${this.credits.length} credits over ${this.stats.yearsActive} working years.`,
      this.awards.wins > 0
        ? `${this.awards.wins} win${this.awards.wins > 1 ? 's' : ''} from ${this.awards.nominations} nomination${this.awards.nominations > 1 ? 's' : ''}.`
        : this.awards.nominations > 0
          ? `Nominated ${this.awards.nominations} time${this.awards.nominations > 1 ? 's' : ''}. Never won.`
          : 'Never nominated.',
      `Lifetime earnings $${this.money.lifetime.toFixed(1)}M. ${this.money.net < 0 ? 'Died owing money.' : `Left $${this.money.net.toFixed(1)}M.`}`,
      best ? `The obituaries all lead with ${best.title} (${best.year}).` : 'The obituaries are short.',
      this.stats.leadCredits === 0
        ? 'Never carried a film. Was in a great many of them.'
        : `Carried ${this.stats.leadCredits} film${this.stats.leadCredits > 1 ? 's' : ''}.`,
      this.endReason || '',
    ];
    this.obituaryText = lines.filter(Boolean);
    return this.obituaryText;
  }
}
