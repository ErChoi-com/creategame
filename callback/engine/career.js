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
import { Rolodex } from './rolodex.js';
import { clampAmbition, ambitionReport } from './ambition.js';
import { availableActions, perform } from './leverage.js';
import {
  MOMENT_POOL, momentsAvailable, pickLifeEvent, eventPrompt, LIFE_EVENTS,
} from './events.js';

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

// §5.12 the moments on set. The pool lives in events.js; this is the subset
// that can happen on any production at all.
export const MOMENTS = MOMENT_POOL.filter((m) => m.core);
export { MOMENT_POOL };



const roman = (n) => ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'][clamp(n - 1, 0, 9)];

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
    this.stats = {
      peakHeat: 0, leadCredits: 0, leadsAfter42: 0, yearsActive: 0,
      peakIdentification: 0, voiceYears: 0, coldYears: 0,
    };

    // §0.4 what the obituary will measure you against. Gates nothing.
    this.ambition = clampAmbition(opts.ambition ?? 'work');
    this.ambitionChangedAt = null;

    // Part 6 — the leverage layer. All of it pull, none of it pushed.
    this.rolodex = new Rolodex(this.world);
    this.development = [];        // material you optioned or funded
    this.franchise = null;        // the property you are identified with
    this.approvals = new Set();   // script / costar / director / cut
    this.positions = new Set();   // guild / juror / prodco / teacher / board
    this.mentees = [];
    this.information = [];        // things you know about specific people
    this.scarcity = 0;
    this.hiatus = false;
    this.hiatusUntil = null;   // set when the break is a fixed length
    this.criticSkew = 0;
    this.courtedCritics = 0;
    this.campaignSpend = 0;
    this.categoryFraud = false;
    this.campaignedThisYear = false;
    this.leverageUsed = 0;
    this.noticesHistory = [];
    this.turnedDown = [];         // §0.6 — the obituary remembers these
    this.currentRole = null;      // cast, not yet shot: what project verbs act on

    // The anti-tedium instrumentation. Every time the game stops and asks the
    // player something, it counts here; sim/agency.mjs holds the line.
    this.pushes = 0;
    this.pushesByYear = new Map();

    // Every mutating call, in order. The engine is deterministic from its
    // seed, so this list IS the save file: replaying it rebuilds the exact
    // career, and it doubles as a record of what the player actually did.
    this.journal = [];
    this.replaying = false;

    // At most one life event a year, each fired by something true about your
    // state rather than by a die roll (§0.1, and rule 1: never upkeep).
    this.firedEvents = new Set();
    this.pendingEvent = null;

    // Standing orders — how you work when the game does not need to ask.
    this.standingOrders = {
      prep: 'table',              // default approach
      stance: 'shaped',           // shaped | generous | showy | still
      floor: 'anything',          // anything | supporting | lead
      askWhenInteresting: true,   // false = never ask, run on defaults
    };
  }

  // Everything the interface does to the game goes through here.
  call(name, args = []) {
    if (!this.replaying) this.journal.push([name, args]);
    switch (name) {
      case 'openBoard': return this.openBoard();
      case 'filmFor': return this.filmFor(this.findRole(args[0]));
      case 'pursue': return this.pursue(args[0]);
      case 'decline': return this.decline(args[0]);
      case 'shoot': return this.shoot(this.currentRole, args[0]);
      case 'do': return this.do(args[0], this.resolveCtx(args[1]));
      case 'tickPending': return this.tickPending();
      case 'tickQuarter': return this.world.tickQuarter();
      case 'endYear': return this.endYear();
      case 'orders': Object.assign(this.standingOrders, args[0]); return this.standingOrders;
      case 'ambition': return this.setAmbition(args[0]);
      case 'event': return this.resolveEvent(args[0]);
      default: throw new Error(`unknown call ${name}`);
    }
  }

  findRole(id) {
    return this.board.find((r) => r.id === id) || this.currentRole;
  }

  // Contexts hold live objects; the journal holds ids, and this puts them back.
  resolveCtx(ref = {}) {
    const ctx = {};
    if (ref.role) ctx.role = this.findRole(ref.role);
    if (ref.person) ctx.person = [...this.rolodex.edges.values()].find((e) => e.id === ref.person);
    if (ref.script) ctx.script = this.development.find((sc) => sc.id === ref.script);
    if (ref.project) ctx.project = this.pending.find((p) => p.role.id === ref.project);
    if (ref.scandal) ctx.scandal = this.world.scandals.find((sc) => sc.person.id === ref.scandal);
    return ctx;
  }

  static ctxRef(ctx = {}) {
    const ref = {};
    if (ctx.role) ref.role = ctx.role.id;
    if (ctx.person) ref.person = ctx.person.id;
    if (ctx.script) ref.script = ctx.script.id;
    if (ctx.project) ref.project = ctx.project.role.id;
    if (ctx.scandal) ref.scandal = ctx.scandal.person.id;
    return ref;
  }

  // The film's palette is rolled once, lazily, and remembered — it consumes
  // randomness, so it has to happen at a fixed point in the sequence.
  filmFor(role) {
    if (!role) return null;
    if (!role.palette) {
      role.palette = this.world.randomPalette(this.rng, role.genre, role.budget, role.director.taste);
    }
    return { palette: role.palette, ...M.coherence(role.palette) };
  }

  // A cheap value that must match after a replay if the replay is faithful.
  fingerprint() {
    const a = this.actor;
    return [
      this.year, a.age, a.name, this.credits.length, this.turnedDown.length,
      a.standing.heat.toFixed(4), a.standing.prestige.toFixed(4),
      a.standing.affection.toFixed(4), a.standing.notoriety.toFixed(4),
      a.attrs.craft.toFixed(4), this.money.net.toFixed(4), this.money.lifetime.toFixed(4),
      this.awards.nominations, this.awards.wins, this.favours, this.scarcity,
      this.leverageUsed, this.board.map((r) => r.id).join('/'),
    ].join('|');
  }

  save() {
    return {
      version: 1,
      seed: this.seed,
      background: this.actor.background,
      ambition: this.ambition,
      // The *given* name, not the current one: an unnamed actor draws their
      // name from the world's pool, which consumes randomness, and a replay
      // has to consume it in the same place. A mid-career name change is in
      // the journal already.
      name: this.actor.givenName,
      startYear: this.world.startYear,
      journal: this.journal,
    };
  }

  static load(data) {
    const g = new Game({
      seed: data.seed,
      background: data.background,
      ambition: data.ambition,
      name: data.name,
      startYear: data.startYear,
    });
    g.replaying = true;
    for (const [name, args] of data.journal) g.call(name, args);
    g.replaying = false;
    g.journal = data.journal.slice();
    return g;
  }

  // ------------------------------------------------------------------ pushes
  countPush(kind, n = 1) {
    this.pushes += n;
    const y = this.pushesByYear.get(this.year) || { total: 0 };
    y.total += n;
    y[kind] = (y[kind] || 0) + n;
    this.pushesByYear.set(this.year, y);
  }

  _makeActor(backgroundKey, name) {
    const bg = BACKGROUNDS[backgroundKey] || BACKGROUNDS.conservatory;
    const rng = this.rng;
    const jitter = (v, sd = 7) => clamp(rng.gauss(v, sd), 5, 95);
    const genre = {}; for (const g of GENRES) genre[g] = clamp(rng.gauss(12, 6), 0, 100);
    const archetype = {}; for (const a of ARCHETYPES) archetype[a] = clamp(rng.gauss(12, 6), 0, 100);

    return {
      name: name || this.world.name(),
      givenName: name || null,
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
      genreCredits: {},
      solvedGates: {},
      lastWorkedYear: null,
    };
  }

  // ------------------------------------------------------------------ getters
  get year() { return this.world.year; }
  get quarter() { return this.world.quarter; }
  get standing() { return M.standing(this.actor.standing); }
  get legibility() { return M.legibility(this.actor.persona); }
  get agentTier() { return AGENT_TIERS[this.actor.agent]; }
  get favours() { return this.rolodex.totalFavours(); }

  // The pull surface. Nothing here is ever prompted (§0.3 rule 2b).
  moves(ctx = {}) {
    return availableActions(this, { role: ctx.role, current: this.currentRole, ...ctx });
  }

  do(actionId, ctx = {}) {
    return perform(this, actionId, { role: ctx.role, current: this.currentRole, ...ctx });
  }

  ambitionReport() { return ambitionReport(this); }

  setAmbition(key) {
    if (this.ambitionChangedAt !== null) return false;
    const next = clampAmbition(key);
    if (next === this.ambition) return false;
    this.ambition = next;
    this.ambitionChangedAt = this.year;
    this.say(`You want something else now.`, 'note');
    return true;
  }

  flagCampaign(role) { role.publicCampaign = true; }

  // The season only stops the game when there is something to decide: a
  // performance worth campaigning and the means to campaign it. Otherwise it
  // resolves on its own and you read about it (§4.11, §0.1).
  seasonNeedsYou() {
    if (!this.awards.thisSeason.length) return false;
    const contender = this.awards.thisSeason.some((e) => e.rec.notices > 62);
    const canAfford = this.money.net > 0.4 && this.blocksBooked < 4;
    return contender && canAfford;
  }

  markWorked(billing) {
    this.actor.lastWorkedYear = this.year;
    if (!this.yearBilling || BILLING_WEIGHT[billing] > BILLING_WEIGHT[this.yearBilling]) {
      this.yearBilling = billing;
    }
  }

  // §0.3 rule 3 — options narrow. The three moments are three the first
  // dozen times; after forty pictures a set holds one surprise, not three,
  // and the ones that still fire are the ones that swing hardest. A chaotic
  // production or a director you have never met puts them back.
  // What your standing orders do on set when the game does not stop to ask.
  // The scene still happens either way — you are simply not consulted about
  // the ones you have handled a hundred times.
  defaultMomentChoice(momentId, moment) {
    const stance = this.standingOrders.stance;
    const table = {
      generous: { not_working: 'absorb', adjustment: 'take', discovery: 'offer' },
      showy:    { not_working: 'suggest', adjustment: 'argue', discovery: 'keep' },
      still:    { not_working: 'ask', adjustment: 'take', discovery: 'lose' },
      shaped:   { not_working: 'ask', adjustment: 'both', discovery: 'offer' },
    };
    const named = (table[stance] || table.shaped)[momentId];
    if (named) return named;
    // For the situational moments, standing orders mean: the professional
    // answer, which is the middle one.
    const opts = (moment || MOMENT_POOL.find((m) => m.id === momentId))?.options || [];
    const idx = stance === 'showy' ? 0 : stance === 'generous' ? Math.min(1, opts.length - 1)
      : Math.floor(opts.length / 2);
    return opts[clamp(idx, 0, opts.length - 1)]?.id;
  }

  momentsFor(role) {
    const n = this.credits.length;
    let count = n < 12 ? 3 : n < 26 ? 2 : n < 40 ? 1 : 0;
    if (role.chaos > 80) count += 1;                                  // a bad set is a bad set
    if ((role.director.sharedProjects || 0) === 0 && n < 30) count += 1;   // a stranger directing
    if (role.billing === 'bit') count = Math.min(count, 1);           // you are here for a day
    count = clamp(count, 0, 3);
    if (!count) return [];

    // Which moments this particular production can even produce. The ones
    // specific to this set come first: they are the reason the shoot is not
    // the same nine table cells every time.
    const pool = momentsAvailable({
      role, costar: role.costar, director: role.director, chaos: role.chaos,
    });
    const specific = pool.filter((m) => !m.core);
    const core = pool.filter((m) => m.core);
    const picked = [];
    const rng = this.rng;
    while (picked.length < count && (specific.length || core.length)) {
      const from = specific.length && (picked.length === 0 || rng.chance(0.5)) ? specific : core;
      if (!from.length) break;
      picked.push(from.splice(rng.int(0, from.length - 1), 1)[0]);
    }
    return picked;
  }

  // §4.6 / §5.5 — the game only asks about prep and stance when the answer
  // could reasonably differ. Everything else runs on your standing orders, and
  // that is the whole reason breadth does not become tedium.
  shouldAskPrep(role) {
    if (!this.standingOrders.askWhenInteresting) return false;
    // A gate you cannot clear is worth a conversation the first couple of
    // times. After that you have a dialect coach on speed dial and the answer
    // is not in question — which is why an ageing actor does not get asked
    // about their voice every single picture.
    for (const [gate, req] of Object.entries(role.gates || {})) {
      if ((this.actor.gates[gate] ?? 50) < req && (this.actor.solvedGates[gate] || 0) < 2) return true;
    }
    // Research pays on these, so the answer might differ — but only until you
    // have done enough of them to have a way of working.
    if ((role.genre === 'period' || role.archetype === 'authority')
        && this.actor.persona.genre.period < 55) return true;
    return role.billing === 'lead' && this.credits.length < 12;
  }

  shouldAskStance(role, film) {
    if (!this.standingOrders.askWhenInteresting) return false;
    if ((film.coherence ?? 50) < 42) return true;         // wide open, no shape to read
    // Your first horror picture is a question. Your fourth is not, and by
    // twenty-five credits you have a way of working in anything.
    if (!(this.actor.genreCredits[role.genre] > 0) && this.credits.length < 25) return true;
    // Your first leads are decisions. Your twentieth is a Tuesday, and your
    // standing orders cover it unless the film itself is strange.
    return role.billing === 'lead' && this.stats.leadCredits < 8;
  }

  // The stance your standing orders reach for, spent against your budget.
  autoPositions(role) {
    const budget = M.contrastBudget(this.actor.attrs.craft, role.director.command);
    const pos = { energy: 'with', volume: 'with', warmth: 'with', speed: 'with' };
    const pay = role.genre === 'comedy' ? 'speed'
      : role.genre === 'romance' || role.genre === 'family' ? 'warmth' : 'energy';
    switch (this.standingOrders.stance) {
      case 'generous':
        pos.volume = 'beneath'; if (budget >= 3) pos[pay] = 'beneath';
        break;
      case 'showy':
        if (budget >= 3) pos[pay] = 'against';
        if (budget >= 5) pos.volume = 'beyond';
        break;
      case 'still':
        pos.energy = 'against'; if (budget >= 4.3) pos.volume = 'beneath';
        break;
      case 'shaped':
      default:
        if (budget >= 3) pos[pay] = 'against';
        if (budget >= 4.3) pos[pay === 'energy' ? 'volume' : 'energy'] = 'beneath';
    }
    return pos;
  }

  say(text, kind = 'note') {
    this.log.push({ year: this.year, quarter: this.quarter, kind, text });
    if (this.log.length > 400) this.log.shift();
    return text;
  }

  // ------------------------------------------------------------- offer board
  openBoard() {
    const a = this.actor;
    if (this.hiatus) {
      // +6 a quarter, capped at 40 — two years away is the full effect (§6.6).
      this.scarcity = clamp(this.scarcity + 6, 0, 40);
      // And the industry's picture of you softens while you are gone. This is
      // the real prize of vanishing: you come back readable as something else.
      for (const vec of [a.persona.genre, a.persona.archetype]) {
        const keys = Object.keys(vec);
        const avg = keys.reduce((t, k) => t + vec[k], 0) / keys.length;
        for (const k of keys) vec[k] += (avg - vec[k]) * 0.10;
      }
      this.board = [];
      return this.board;
    }
    a.quote = M.quote(a.standing, a.recentRoi, this.world.eraMultiplier);
    const sp = M.starPower(a.standing);
    // §6.6 — scarcity raises the *tier* of what you are offered, not just the
    // script quality. Being unavailable is a way of being wanted, and without
    // this term disappearing is strictly worse, which would make it a trap
    // rather than a strategy.
    a.standingScalar = M.standing(a.standing) + 0.35 * a.recognition + 0.60 * this.scarcity;
    a.legibilityValue = this.legibility;
    const band = this._ageBand(a.age);
    // Some quarters the phone does not ring. That has to be possible or the
    // career has no downside and every run converges on the same shape.
    // Offers are lumpy. A rate of 1.2 a quarter is one offer most quarters and
    // two sometimes — and a rate of 0.4 is three quarters of nothing, which is
    // what the back half of most careers actually looks like.
    const rate = (0.4 + sp / 10 + a.recognition / 30 + this.agentTier.offers) * band;
    const count = clamp(
      Math.floor(rate) + (this.rng.chance(rate % 1) ? 1 : 0),
      0, 9,
    );

    // §6.6 disappearing. Two years away costs about eighteen Heat and buys
    // materially better material when you come back. Whether that is a good
    // trade depends entirely on what the Heat was buying you.
    const menteePull = this.mentees.filter((m) => m.power > 55).length;

    const listings = [];
    for (let i = 0; i < count + (this.scarcity > 20 ? 1 : 0) + menteePull; i++) {
      const role = this.world.generateRole(a);
      if (this.scarcity > 0) {
        // Two years away buys materially better material when you come back.
        role.scriptQuality = clamp(role.scriptQuality + 0.4 * this.scarcity, 5, 98);
        role.difficulty -= Math.min(12, 0.3 * this.scarcity);
        role.scarcityPremium = this.scarcity;
      }
      // The property comes back around, and it comes back to you.
    if (this.franchise && !this.franchise.writtenOut && this.franchise.identification > 28
        && i === 0 && this.year - (this.franchise.lastOffer || -3) >= 2) {
      this.franchise.lastOffer = this.year;
      role.billing = 'lead';
      role.type = 'tentpole';
      role.genre = this.franchise.genre;
      role.title = `${this.franchise.title} ${roman(this.franchise.installments + 1)}`;
      role.budget = Math.max(role.budget, 120);
      role.budgetForRole = role.budget * 0.14;
      role.blocks = 3;
      role.label = 'Tentpole';
      role.path = 'direct';
      role.difficulty = 0;
      role.franchiseInstallment = true;
    }

    // Someone you taught fifteen years ago is casting something now.
      if (i >= count && menteePull) {
        const m = this.mentees.find((x) => x.power > 55);
        if (m) { role.viaMentee = m.person.name; role.difficulty -= 14; }
      }
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
      const u = M.utility(a, role, rel) + (this.positions.has('board') ? 4 : 0);
      const p = M.offerProbability(u, role.difficulty);
      // Things that come to you rather than being auditioned for: the next
      // installment of your own franchise, and anything you made happen.
      const handed = role.franchiseInstallment || role.yours || role.comeback;
      listings.push({
        ...role,
        utility: handed ? 100 : u,
        chance: handed ? 1 : p,
        path: handed ? 'direct' : M.castingPath(u, role, rel),
        relationshipBonus: rel,
        fit: M.fitScore(a, role),
      });
    }
    // §0.3 rule 3 — an established actor's agent brings them three things, not
    // nine. What reaches you narrows as you rise, which is what stops a
    // sixty-year career becoming sixty years of spreadsheet.
    const reach = clamp(Math.round(6 - M.standing(a.standing) / 22), 2, 7);

    // Your standing orders decide what your agent bothers you with at all.
    const floor = this.standingOrders.floor;
    const passes = (r) => floor === 'anything'
      || (floor === 'supporting' && r.billing !== 'bit')
      || (floor === 'lead' && r.billing === 'lead');
    const shown = listings.filter(passes);

    // The board is sorted the way an agent would present it.
    shown.sort((x, y) => (y.chance * BILLING_WEIGHT[y.billing]) - (x.chance * BILLING_WEIGHT[x.billing]));
    const kept = shown.slice(0, reach);
    this.board = kept;
    return kept;
  }

  // §4.9 role volume by age. The late bands are steep because they are steep:
  // most careers do not end in a decision, they end in a year with no offers
  // in it, and then another one.
  _ageBand(age) {
    return age < 28 ? 1.30 : age < 39 ? 1.45 : age < 49 ? 1.00 : age < 61 ? 0.58 : 0.24;
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
      this.currentRole = role;
      this.say(`${role.director.name} offered you ${role.title} outright.`, 'good');
      return { cast: true, path: 'direct', role };
    }
    if (role.path === 'offer') {
      this.currentRole = role;
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
      this.rolodex.edge(role.castingDirector).affinity += 4;
      this.currentRole = role;
      this.say(`You read for ${role.title} and got it.`, 'good');
      return { cast: true, path: 'audition', role };
    }
    role.castingDirector.affinity = clamp(role.castingDirector.affinity + 1, -100, 100);
    if (role.publicCampaign) {
      this.actor.standing.notoriety = clamp(this.actor.standing.notoriety + 6, 0, 100);
      this.say(`You said publicly that you wanted ${role.title}. You did not get ${role.title}.`, 'bad');
    } else {
      this.say(`You read for ${role.title}. They went another way.`, 'bad');
    }
    return { cast: false, path: 'audition', role };
  }

  // §0.6 — the obituary remembers what you said no to.
  decline(roleId) {
    const role = this.board.find((r) => r.id === roleId);
    if (!role) return null;
    this.board = this.board.filter((r) => r.id !== roleId);
    this.turnedDown.push({
      title: role.title, year: this.year, billing: role.billing,
      genre: role.genre, budget: role.budget, director: role.director.name,
      id: role.id,
    });
    return role;
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
    this.markWorked(role.billing);
    this.currentRole = null;

    let prep = clamp(prepChoice.base * (0.8 + 0.004 * a.attrs.resilience) - (role.prepPenalty || 0), 0, 100);
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

    let chemistry = clamp(this.rng.gauss(58, 16) + 0.2 * Math.max(0, role.costar.affinity)
      - 0.3 * role.costar.ego / 10 + (role.chemistryBonus || 0), 0, 100);
    let condition = clamp(a.condition - 0.25 * role.chaos + 0.3 * a.attrs.resilience - 12 * (this.blocksBooked / 4), 20, 100);
    let perfNudge = 0, ensembleNudge = 0;

    // Which moments you were consulted on, and which ones simply happened.
    // The ordinary days of a shoot always happen — being experienced means
    // nobody asks you about them, not that they stop occurring.
    const asked = choices.momentSet || this.momentsFor(role);
    const prompted = new Set(asked.map((m) => m.id));
    const happening = [];
    const seen = new Set();
    for (const m of [...MOMENT_POOL.filter((x) => x.core), ...asked]) {
      if (seen.has(m.id)) continue;
      seen.add(m.id);
      happening.push(m);
    }
    const momentLog = [];
    for (const moment of happening) {
      const pickId = momentChoices[moment.id] || this.defaultMomentChoice(moment.id, moment);
      const opt = moment.options.find((o) => o.id === pickId) || moment.options[1];
      const e = opt.effect;
      chemistry = clamp(chemistry + (e.chemistry || 0), 0, 100);
      prep = clamp(prep + (e.prep || 0), 0, 100);
      condition = clamp(condition + (e.condition || 0), 0, 100);
      perfNudge += e.perf || 0;
      ensembleNudge += e.ensemble || 0;
      if (e.affinity) director.affinity = clamp(director.affinity + e.affinity, -100, 100);
      if (e.favour) this.rolodex.gain(role.costar, 'generosity', this.year);
      if (e.costarAffinity) {
        const edge = this.rolodex.edge(role.costar);
        edge.affinity = clamp(edge.affinity + e.costarAffinity, -100, 100);
      }
      if (e.costarGrudge) {
        const edge = this.rolodex.edge(role.costar);
        edge.grudge = clamp(edge.grudge + e.costarGrudge, 0, 100);
      }
      if (e.notoriety) a.standing.notoriety = clamp(a.standing.notoriety + e.notoriety, 0, 100);
      if (e.crew) this.crewLoyalty = (this.crewLoyalty || 0) + e.crew;
      if (e.injuryRisk && this.rng.chance(e.injuryRisk)) {
        a.health = clamp(a.health - this.rng.int(6, 20), 0, 100);
        a.gates.physicality = clamp(a.gates.physicality - this.rng.int(0, 6), 5, 98);
        this.say('The fall went wrong. Six weeks, and it never quite goes away.', 'bad');
      }
      momentLog.push({ moment: moment.id, chose: opt.label, asked: prompted.has(moment.id) });
    }

    const palette = role.palette || this.world.randomPalette(this.rng, role.genre, role.budget, director.taste);
    const coh = M.coherence(palette);
    const film = { palette, coherence: coh.value, nearest: coh.nearest };

    const fit = clamp(M.fitScore(a, role) + (role.fitBonus || 0), 0, 100);
    const perf = M.performance(this.rng, {
      actor: a, role, film, prep, chemistry, condition,
      directorSkill: dSkill, fit,
    });
    perf.value = clamp(perf.value + perfNudge, 0, 100);

    // §6.6 improvising against the script: high variance, rewards Instinct,
    // and the director's patience is a real thing you are spending.
    if (role.improvised) {
      const swing = this.rng.gauss(0.35 * (a.attrs.instinct - 52) / 10, 11);
      perf.value = clamp(perf.value + swing, 0, 100);
      role.director.affinity = clamp(role.director.affinity + (swing > 0 ? 3 : -8), -100, 100);
    }

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
    this.credits.push({
      title: role.title, year: this.year, billing: role.billing,
      genre: role.genre, tentpole: role.type === 'tentpole',
    });
    a.genreCredits[role.genre] = (a.genreCredits[role.genre] || 0) + 1;
    if (prepChoice.clearsGate) {
      a.solvedGates[prepChoice.clearsGate] = (a.solvedGates[prepChoice.clearsGate] || 0) + 1;
    }

    // The deal, paid on signature — unless you waived it to be in this at all.
    let income = M.fee(this.rng, a, role, this.agentTier, a.recentRoi, this.world.eraMultiplier);
    if (this.franchise && role.type === 'tentpole' && !this.franchise.writtenOut) {
      // They cannot recast you, and the quote reflects it. This is what
      // indispensability is for: it is the one leverage money cannot buy.
      income *= 1 + this.franchise.identification / 35;
    }
    if (role.scarcityPremium) income *= 1 + 0.010 * role.scarcityPremium;
    if (role.takeScale) {
      income = Math.min(income, 0.02);
      this.rolodex.gain(director, 'scale', this.year);
      a.attrs.craft = clamp(a.attrs.craft + 1.5, 5, 99);
    }
    M.applyLifestyle(this.money, income);
    project.fee = income;

    // Everyone you just spent three months with is now someone you know.
    this.rolodex.contact(director, this.year);
    this.rolodex.contact(role.costar, this.year);
    if (project.resolved.generosity > 0) this.rolodex.gain(role.costar, 'generosity', this.year);
    if (project.resolved.upstaging > 0) {
      const e = this.rolodex.edge(role.costar);
      e.grudge = clamp(e.grudge + 18, 0, 100);
    }
    // Proximity is how you come to know things about people (§6.1).
    if (this.rng.chance(0.12 + director.temperament === 'chaotic' ? 0.1 : 0)) {
      this.information.push({ about: director, kind: 'something from the set' });
    }

    // §6.4 franchises. Identification with a property is built by doing it
    // again, and it is the only leverage that cannot be bought.
    if (role.type === 'tentpole' && role.billing !== 'bit') {
      if (this.franchise && this.franchise.genre === role.genre && !this.franchise.writtenOut) {
        this.franchise.installments += 1;
        this.franchise.identification = clamp(this.franchise.identification + 24, 0, 100);
        // §6.3 approvals arrive with indispensability, not with money.
        if (this.franchise.identification > 55) this.approvals.add('costar');
        if (this.franchise.identification > 75) this.approvals.add('script');
      } else if (!this.franchise || this.franchise.writtenOut) {
        this.franchise = {
          title: role.title, genre: role.genre, installments: 1,
          identification: 34, heldOut: false, writtenOut: false, owned: false,
        };
      }
      this.stats.peakIdentification = Math.max(
        this.stats.peakIdentification, this.franchise.identification,
      );
    }

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

    // A critic you have had lunch with for nine years is still a critic, but
    // the noise term leans (§6.6).
    if (this.criticSkew) rec.filmCritic = clamp(rec.filmCritic + this.criticSkew, 0, 100);

    // §5.4 the loop closing on you: the shape you invented is now a shape
    // everyone uses, and using it yourself reads as tired.
    const cliche = this.world.clicheePenalty(project.palette);
    if (cliche > 0) {
      rec.filmCritic = clamp(rec.filmCritic - cliche, 0, 100);
      rec.clicheHit = cliche;
    }

    // §10.3 a festival premiere trades the opening weekend for the room.
    if (project.festival) {
      rec.filmCritic = clamp(rec.filmCritic + 5, 0, 100);
      rec.notices = clamp(rec.notices + 4, 0, 100);
      rec.roi *= 0.72;
      rec.gross *= 0.72;
    }

    if (project.landmark) {
      rec.filmCritic = clamp(rec.filmCritic + 14, 0, 100);
      rec.notices = clamp(rec.notices + 6, 0, 100);
      const mark = this.world.addShape(project.role.title, project.palette, project.role.genre, this.actor.name);
      rec.landmarkName = mark.name;
      this.say(`Nobody has seen a film shaped like ${project.role.title} before. They will now.`, 'good');
    }

    const deltas = M.applyReception(a.standing, rec, role.billing, this.credits.length, role.realBudget ?? role.budget);
    this.noticesHistory.push(rec.notices);
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
    const heldPoints = (this.franchise && role.type === 'tentpole' && this.franchise.grossPoints) || 0;
    if (heldPoints && rec.gross > 0) {
      // The holdout, paid out. This is what indispensability is actually for.
      const paid = heldPoints * rec.gross * (role.era ?? 1);
      M.applyLifestyle(this.money, paid);
      this.say(`Your holdout points on ${role.title} paid $${paid.toFixed(1)}M.`, 'good');
    }
    if (role.producerShare && rec.gross > 0) {
      const producerTake = role.producerShare * rec.gross * (role.era ?? 1) * 0.5;
      M.applyLifestyle(this.money, producerTake);
      if (producerTake > 1) {
        this.say(`Your producer share on ${role.title} came to $${producerTake.toFixed(1)}M.`, 'good');
      }
    }
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
    if (rec.clicheHit) parts.push(`Two reviews use the word "derivative". The shape is eight years old now (−${rec.clicheHit.toFixed(0)}).`);
    if (p.festival) parts.push('It played a festival first, which is why the critics are warm and the opening was not.');
    if (p.role.improvised) parts.push('Some of what is on screen was not written.');
    if (p.role.rewritten) parts.push('You had the part rewritten. That is your version up there.');
    if (p.role.takeScale) parts.push('You did it for nothing, which is why it exists.');
    if (!parts.length) parts.push('It is what it is: a film, released, absorbed.');
    return parts;
  }

  // ------------------------------------------------------------------ season
  runAwardsSeason(opts = {}) {
    const a = this.actor;
    const results = [];
    const campaignSpend = opts.campaignSpend ?? this.campaignSpend;
    const categoryFraud = opts.categoryFraud ?? this.categoryFraud;
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
        categoryAdvantage: categoryFraud && entry.role.billing === 'lead' ? 18 : 0,
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
        if (categoryFraud && entry.role.billing === 'lead' && this.rng.chance(0.35)) {
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

    // §11.6 the ratchet, charged once: a year of living costs what your life
    // costs, whether or not you worked.
    this.money.floor = Math.max(0.02, this.money.floor * M.K.lifestyleDecay);
    this.money.net -= this.money.floor;
    if (this.money.net < 0 && !a.flags.broke) {
      a.flags.broke = this.year;
      this.say('The accountant calls. Then the accountant stops calling.', 'bad');
    }

    this.stats.coldYears = a.standing.heat < 25 ? (this.stats.coldYears || 0) + 1 : 0;
    if (this.legibility > 70 && a.standing.prestige > 55) this.stats.voiceYears += 1;

    this._tickLeverage(worked);

    if (!worked) {
      this.idleYears += 1;
      // People leave. Most people leave.
      // People leave. Most people leave — and being broke while nobody calls
      // is the specific combination that ends careers.
      const broke = this.money.net < 0 ? 0.10 : 0;
      const giveUp = this.idleYears >= 2
        && this.rng.chance(clamp(0.10 + 0.06 * this.idleYears + broke
          - M.standing(a.standing) / 90, 0, 0.65));
      if (giveUp) this._end('You took the other job. Everyone does, eventually.');
      if (this.idleYears >= 7 && a.age > 34) this._end('The phone simply stopped.');
    } else {
      this.idleYears = 0;
    }
    if (a.age >= 80 || a.health <= 0) this._end('Age, in the end.');

    this.blocksBooked = 0;
    this.yearBilling = null;
  }

  // Everything the pull layer accrued this year, resolved. None of it is a
  // prompt; all of it is consequence.
  _tickLeverage(worked) {
    const a = this.actor;

    // §6.4 you cannot cool off while you are the face of a live property. The
    // audience sees you on a bus shelter whether or not you worked this year,
    // and that is what being indispensable actually feels like.
    if (this.franchise && !this.franchise.writtenOut && this.franchise.identification > 30) {
      const floor = clamp(18 + 0.45 * this.franchise.identification, 0, 82);
      if (a.standing.heat < floor) a.standing.heat = floor;
      this.franchise.identification = clamp(this.franchise.identification - 3.5, 0, 100);
      if (this.franchise.identification < 12) this.franchise = null;
    }

    // A bounded break ends on its own; a vanishing does not.
    if (this.hiatus && this.hiatusUntil !== null && this.year >= this.hiatusUntil) {
      this.hiatus = false;
      this.hiatusUntil = null;
      this.say('You go back to work. Nobody made a thing of it.', 'note');
    }

    // Scarcity — you are worth more when you are not available (§6.6).
    if (!worked && !this.hiatus) this.scarcity = clamp(this.scarcity + 4, 0, 40);
    else this.scarcity = clamp(this.scarcity - 8, 0, 40);

    // People drift, and people die.
    const gone = this.rolodex.tickYear(this.year, this.rng);
    for (const e of gone) {
      this.say(`${e.person.name} died. Whatever you were owed died with them.`, 'bad');
    }

    // Mentees grow into the industry. In twenty years one of them may be the
    // most powerful person you know, and they will remember who taught them.
    for (const m of this.mentees) {
      const years = this.year - m.since;
      m.power = clamp(m.power + this.rng.float(1.5, 5.5) + years * 0.12, 0, 100);
      m.person.heat = clamp(m.person.heat + this.rng.float(0, 3.5), 0, 100);
      if (m.power > 55 && !m.announced) {
        m.announced = true;
        this.say(`${m.person.name}, who you taught, is running things now.`, 'good');
      }
    }
    if (this.mentees.length) this.blocksBooked = Math.min(4, this.blocksBooked + 0);

    // Positions pay in kind, not in prompts.
    if (this.positions.has('guild')) {
      a.standing.affection = clamp(a.standing.affection + 1.2, 0, 100);
      this.money.net += 0.02;
    }
    if (this.positions.has('juror') && this.rng.chance(0.4)) {
      a.standing.prestige = clamp(a.standing.prestige + 1.5, 0, 100);
    }
    if (this.positions.has('teacher')) {
      if (this.rng.chance(0.5)) {
        const student = this.world.makeNewcomer(this.rng);
        this.mentees.push({ person: student, since: this.year, power: 0 });
      }
      a.standing.prestige = clamp(a.standing.prestige + 0.8, 0, 100);
    }
    if (this.positions.has('prodco')) this.money.net -= 0.05;

    // Development. One resolution a year per project — never a slate to tend.
    for (const script of this.development.slice()) {
      if (!script.shopped) continue;
      if (this.rng.chance(script.financingChance)) {
        const role = this.world.generateRole(a, { billing: 'lead' });
        role.title = script.title;
        role.genre = script.genre;
        role.scriptQuality = script.quality;
        role.archetype = script.archetype;
        role.charAge = script.charAge;
        role.path = 'direct';
        role.chance = 1;
        role.yours = true;
        role.difficulty = 0;
        role.fit = M.fitScore(a, role);
        role.utility = 100;
        // You are a producer on it, which means a share of the upside and a
        // stake you do not get back if it does not work.
        role.producerShare = this.positions.has('prodco') ? 0.08 : 0.045;
        const stake = clamp(Math.min(this.money.net * 0.18, role.budget * 0.06), 0, 12);
        if (stake > 0.01) {
          this.money.net -= stake;
          role.producerStake = stake;
          this.say(`Getting ${script.title} made cost you $${stake.toFixed(2)}M of your own.`, 'note');
        }
        this.board.unshift(role);
        this.development = this.development.filter((x) => x.id !== script.id);
        this.say(`${script.title} is financed. You are in it because you made it exist.`, 'good');
      } else {
        script.financingChance *= 0.72;
        if (script.financingChance < 0.04) {
          this.development = this.development.filter((x) => x.id !== script.id);
          this.say(`${script.title} is dead. Four years and it never got made.`, 'bad');
        }
      }
    }

    this.campaignedThisYear = false;
    this.campaignSpend = 0;
    this.categoryFraud = false;
  }

  _end(reason) {
    this.over = true;
    this.endReason = reason;
  }

  // ------------------------------------------------------------------ a life
  // Offered at the turn of the year, answered whenever the player likes.
  rollEvent() {
    if (this.pendingEvent) return this.pendingEvent;
    const event = pickLifeEvent(this);
    if (!event) return null;
    this.pendingEvent = { id: event.id, prompt: eventPrompt(event, this) };
    return this.pendingEvent;
  }

  resolveEvent(index) {
    if (!this.pendingEvent) return null;
    const event = LIFE_EVENTS.find((e) => e.id === this.pendingEvent.id);
    this.pendingEvent = null;
    if (!event) return null;
    const option = event.options[clamp(index, 0, event.options.length - 1)];
    this.firedEvents.add(event.id);
    option.run(this);
    if (option.text) this.say(option.text, 'life');
    return { text: option.text, label: option.label };
  }

  // §11.8 the obituary: the one place the private numbers become public, and
  // §0.6 — it remembers what you turned down.
  obituary() {
    const a = this.actor;
    const best = this.credits.length ? this.credits[Math.floor(this.credits.length / 2)] : null;
    const amb = this.ambitionReport();
    const landmarks = this.world.landmarks.filter((l) => l.author === a.name);
    const bigMiss = this.turnedDown.slice().sort((x, y) => y.budget - x.budget)[0];
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
      `${amb.label}: ${amb.grade.toLowerCase()}. ${amb.measure}, ${amb.value}.`
        + (this.ambitionChangedAt ? ` (They wanted something else until ${this.ambitionChangedAt}.)` : ''),
      landmarks.length
        ? `${landmarks[0].name} changed what films looked like${landmarks[0].cliche ? ', and then everyone did it until it was a joke' : ''}.`
        : null,
      this.favours > 6
        ? `${this.favours} people owed them something at the end. Most of it was never called in.`
        : null,
      this.mentees.some((m) => m.power > 55)
        ? `${this.mentees.filter((m) => m.power > 55).length} of the people they taught run things now.`
        : null,
      bigMiss ? `They turned down ${bigMiss.title} in ${bigMiss.year}. It was a $${bigMiss.budget.toFixed(0)}M picture.` : null,
      this.positions.size ? `Also: ${[...this.positions].join(', ')}.` : null,
      this.endReason || '',
    ];
    this.obituaryText = lines.filter(Boolean);
    return this.obituaryText;
  }
}
