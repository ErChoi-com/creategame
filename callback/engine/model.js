// CALLBACK — the model.
//
// Every formula the game resolves against lives here, and nothing here touches
// the DOM or the game loop, so `sim/career-sim.mjs` and `web/app.js` are running
// the identical system.
//
// Where this departs from callback-design-doc-v8.md, it is because the design
// review found the doc's version does not produce a career. Each departure is
// marked FIX-n and explained in callback/DESIGN-DELTA.md.

import { clamp, sig } from './rng.js';
import {
  PALETTE_WEIGHTS, GENRE_ECON, SHAPES, DIALS, PERF_DIALS, READ,
  POSITION_COST, GENRE_DIAL_WEIGHT, BILLING_WEIGHT, GATEKEEPERS,
} from './data.js';

// ---------------------------------------------------------------------------
// Tuned constants. Changing one of these means re-running sim/career-sim.mjs;
// several trade off sharply against each other.
// ---------------------------------------------------------------------------
export const K = {
  // FIX-1 the ladder. Gains carry a base term (working at all is worth
  // something), are re-centred below the median outcome, and decay is
  // proportional rather than a flat −9 so the meters find an equilibrium.
  heatBase: 7.9,
  heatRoiCoef: 9.0,
  heatRoiCentre: 0.90,
  heatAudCoef: 0.20,
  heatAudCentre: 52,
  heatKeepIdle: 0.80,     // a year with no work
  heatKeepBit: 0.865,     // FIX-1b decay is billing-aware: the tier you can
  heatKeepSupporting: 0.888, // reach must be able to outrun the decay on it
  heatKeepLead: 0.925,

  prestigeCriticCoef: 0.11,
  prestigeCriticCentre: 57,
  prestigeNoticesCoef: 0.26,
  prestigeNoticesCentre: 54,
  prestigeKeep: 0.985,

  affectionCoef: 0.10,
  affectionCentre: 55,
  affectionKeep: 0.96,

  notorietyKeep: 0.84,

  // FIX-1c the on-ramp. Your first credits count for more than they should,
  // because a new face is news and a known quantity is not.
  discoveryCredits: 9,
  discoveryPeak: 2.4,

  // FIX-1d the bridge out of bit parts, which is deliberately NOT Standing.
  // Casting directors remember a good five minutes. Recognition is what gets
  // a nobody read for a supporting part; it does nothing for leads.
  recognitionGain: 0.42,        // per point of Notices over the centre
  recognitionCentre: 51,
  recognitionKeep: 0.90,
  recognitionUtility: 0.30,     // weight in Utility for supporting/bit roles
  recognitionFadesBy: 45,       // standing at which being remembered stops mattering
  recognitionTier: 0.20,        // how much being remembered raises the tier you are offered

  openingBase: 0.92,          // box office: opening multiple on budget
  reachBase: 0.35,
  reachCoef: 0.50,
  fieldLead: 0.34,            // audition competition, by tier
  fieldSupporting: 0.48,
  fieldBit: 0.45,

  lifestyleShare: 0.22,       // of your best single payday
  lifestyleDecay: 0.90,       // how fast the way you live comes back down

  scaleFeeBase: 0.03,         // union scale, roughly
  scaleFeeCoef: 0.038,       // and what the film's size adds to it

  grossPointsDivisor: 52,
  grossPointsMax: 0.20,      // first-dollar gross, stars only
  quoteExp: 0.070,            // steepness of the top of the market
  buzzCentre: 63,
  winBase: 0.22,

  paletteScale: 0.32,
  franchiseKeepDecay: 1.2,    // identification lost per year while you keep doing them
  franchiseSkipDecay: 6.5,    // and per year while you do not

  contrastBudgetDivisor: 28,
  landmarkCoherenceGate: 60,
};

// ---------------------------------------------------------------------------
// Standing
// ---------------------------------------------------------------------------

export function starPower(s) {
  return 0.45 * s.heat + 0.30 * s.affection + 0.25 * s.prestige;
}

// FIX-3 "Standing" is used throughout Parts 6 and 8 as a scalar that the doc
// never defines. It is defined here, once, as StarPower net of scandal, and
// every threshold in the game reads this function.
export function standing(s) {
  return clamp(starPower(s) - 0.20 * Math.max(0, s.notoriety - 55), 0, 100);
}

export function bankability(s, recentRoi = 1) {
  return clamp(
    0.60 * s.heat + 0.25 * clamp(40 * recentRoi, 0, 100) + 0.15 * s.affection
      - 0.20 * Math.max(0, s.notoriety - 55),
    0, 100,
  );
}

export function quote(s, recentRoi = 1, eraMultiplier = 1) {
  return 0.05 * Math.exp(K.quoteExp * bankability(s, recentRoi)) * eraMultiplier;
}

export function discoveryMultiplier(credits) {
  if (credits >= K.discoveryCredits) return 1;
  const t = 1 - credits / K.discoveryCredits;
  return 1 + (K.discoveryPeak - 1) * t * t;
}

export function heatKeep(billingThisYear) {
  switch (billingThisYear) {
    case 'lead': return K.heatKeepLead;
    case 'supporting': return K.heatKeepSupporting;
    case 'bit': return K.heatKeepBit;
    default: return K.heatKeepIdle;
  }
}

// ---------------------------------------------------------------------------
// Persona and Legibility (§4.2)
// ---------------------------------------------------------------------------

export function legibility(persona) {
  const conc = (vec) => {
    const vals = Object.values(vec);
    const max = Math.max(...vals);
    if (max <= 0) return 0;
    const mn = vals.reduce((a, b) => a + b, 0) / vals.length;
    return 100 * ((max - mn) / max);
  };
  return clamp((conc(persona.genre) + conc(persona.archetype)) / 2, 0, 100);
}

export function updatePersona(persona, genre, archetype, billing, audienceScore) {
  const bw = BILLING_WEIGHT[billing];
  const rf = clamp(0.4 + audienceScore / 100, 0.4, 1.6);
  for (const k of Object.keys(persona.genre)) {
    persona.genre[k] = clamp(
      persona.genre[k] + (k === genre ? 6 * bw * rf : -0.8 * bw), 0, 100,
    );
  }
  for (const k of Object.keys(persona.archetype)) {
    persona.archetype[k] = clamp(
      persona.archetype[k] + (k === archetype ? 6 * bw * rf : -0.8 * bw), 0, 100,
    );
  }
}

// ---------------------------------------------------------------------------
// Casting (§4.4)
// ---------------------------------------------------------------------------

export function ageMismatchPenalty(charAge, actorAge) {
  const d = Math.abs(charAge - actorAge);
  if (d <= 4) return 0;
  const raw = 2.2 * Math.pow(d - 4, 1.35);
  const asym = charAge < actorAge ? 1.6 : 1.0; // playing younger costs more
  return Math.min(70, raw * asym);
}

export function fitScore(actor, role) {
  let fit = 100;
  fit -= ageMismatchPenalty(role.charAge, actor.age);
  fit -= 0.45 * (100 - actor.persona.genre[role.genre]) * role.typeStrictness;
  fit -= 0.45 * (100 - actor.persona.archetype[role.archetype]) * role.typeStrictness;
  for (const [gate, req] of Object.entries(role.gates || {})) {
    const have = actor.gates[gate] ?? 50;
    if (have < req) fit -= 0.6 * (req - have);
  }
  return clamp(fit, 0, 100);
}

export function utility(actor, role, relationshipBonus = 0) {
  const g = GATEKEEPERS[role.gatekeeper];
  const standingScore = clamp(
    g.heat * actor.standing.heat + g.prestige * actor.standing.prestige
      + g.affection * actor.standing.affection + g.notoriety * actor.standing.notoriety,
    0, 100,
  );
  const fit = fitScore(actor, role);
  const craftTerm = 0.6 * actor.attrs.craft + 0.4 * actor.attrs.instinct;

  // FIX-1d Recognition only opens the lower two tiers, and it fades as you
  // acquire standing of your own. It is a way IN, not a way up: being the
  // person who was good in that one scene gets an unknown read for the
  // supporting part, and means nothing at all once you are somebody.
  const standingNow = starPower(actor.standing);
  const stillUseful = clamp(1 - standingNow / K.recognitionFadesBy, 0, 1);
  const recog = role.billing === 'lead'
    ? 0
    : K.recognitionUtility * actor.recognition * stillUseful;

  // You are too expensive for this film. Capped, because an actor who wants a
  // part takes less for it, and the doc's uncapped version priced working
  // actors out of the entire board the moment their quote moved.
  const overpriced = clamp(
    5 * (actor.quote / Math.max(0.05, role.budgetForRole) - 1), 0, 12,
  );

  return 0.40 * standingScore + 0.35 * fit + 0.15 * craftTerm
    + recog + relationshipBonus - overpriced;
}

export function offerProbability(u, difficulty) {
  return sig(0.11 * (u - difficulty));
}

// FIX-6 the doc's "offer" path (Utility − difficulty > 25) is unreachable
// without relationships, which makes it the same path as path 3. The threshold
// is expressed against the role's own difficulty instead, so a star who is
// obvious casting for a small film gets offered it outright.
export function castingPath(u, role, relationshipBonus) {
  if (relationshipBonus >= 18) return 'direct';
  if (u - role.difficulty > 14) return 'offer';
  return 'audition';
}

// ---------------------------------------------------------------------------
// The film: palette, coherence, landmarks (§5.3–§5.4)
// ---------------------------------------------------------------------------

// §5.3 says palette effects run about +-7-10 on AudienceScore against a base
// sd of 7.6 — "a major factor, never the only one". K.paletteScale is what
// holds them there; at 1.0 the palette swamps every other reception term and
// critics and crowds stop agreeing at all.
export function paletteEffect(palette, genre) {
  const w = PALETTE_WEIGHTS[genre];
  let aud = 0, crit = 0;
  for (const d of DIALS) {
    aud += (w.aud[d] * palette[d]) / 100;
    crit += (w.crit[d] * palette[d]) / 100;
  }
  return { aud: aud * K.paletteScale, crit: crit * K.paletteScale };
}

export function coherence(palette) {
  let best = Infinity, bestName = null;
  for (const [name, shape] of Object.entries(SHAPES)) {
    let sum = 0;
    for (const d of DIALS) sum += (palette[d] - shape[d]) ** 2;
    const dist = Math.sqrt(sum / DIALS.length);
    if (dist < best) { best = dist; bestName = name; }
  }
  return { value: clamp(100 - 2.2 * best, 0, 100), nearest: bestName };
}

export function landmarkChance(coh, skill) {
  if (coh >= K.landmarkCoherenceGate || skill <= 70) return 0;
  return clamp(0.02 + 0.00022 * (K.landmarkCoherenceGate - coh) * (skill - 70), 0, 0.20);
}

// ---------------------------------------------------------------------------
// The performance (§4.7 + §5.5–§5.7)
//
// FIX-2 Part 5 and Part 4 defined Notices and Ensemble as different quantities
// and never reconciled them. There is now exactly one of each, produced here
// and consumed as terms inside reception() below.
// ---------------------------------------------------------------------------

export function contrastBudget(craft, directorCommand) {
  return (craft + directorCommand) / K.contrastBudgetDivisor;
}

export function performance(rng, ctx) {
  const { actor, role, film, prep, chemistry, condition, directorSkill } = ctx;
  const a = actor.attrs;
  const fit = ctx.fit ?? fitScore(actor, role);

  const base = 0.28 * a.craft + 0.18 * a.instinct + 0.16 * a.presence
    + 0.16 * fit + 0.12 * prep + 0.10 * chemistry;
  const directionMult = 0.86 + 0.0028 * directorSkill;
  const conditionMult = 0.80 + 0.0020 * condition;
  const sigma = Math.max(4, 16 - 0.09 * a.craft);

  let p = base * directionMult * conditionMult + rng.gauss(0, sigma);
  let transcendent = false;
  if (rng.chance(a.instinct / 320)) {
    p += rng.float(9, 26);
    transcendent = true;
  }
  // §5.4 an incoherent film widens every outcome in it.
  const coh = film.coherence ?? 50;
  const varianceMult = 1 + 0.014 * (100 - coh);
  p = 63.6 + (p - 63.6) * Math.sqrt(varianceMult);

  return { value: clamp(p, 0, 100), transcendent, base };
}

// Resolve the four chosen positions into the two currencies.
export function resolvePositions(positions, ctx) {
  const { genre, craft, directorCommand, partnerPositions } = ctx;
  const gw = GENRE_DIAL_WEIGHT[genre] || GENRE_DIAL_WEIGHT.drama;
  let forYou = 0, forFilm = 0, cost = 0, spikeCost = 0;

  for (const d of PERF_DIALS) {
    const pos = positions[d] || 'with';
    const [you, film] = READ[d][pos];
    forYou += you * (gw[d] ?? 1);
    forFilm += film;
    cost += POSITION_COST[pos];
    if (pos === 'beyond' || pos === 'against') spikeCost += POSITION_COST[pos];
  }

  const budget = contrastBudget(craft, directorCommand);
  const overspend = Math.max(0, cost - budget);
  const spikiness = clamp(spikeCost / 12, 0, 1);

  // §5.7 generosity and upstaging, resolved against the scene partner.
  let generosity = 0, upstaging = 0;
  if (partnerPositions) {
    for (const d of PERF_DIALS) {
      const mine = positions[d] || 'with';
      const theirs = partnerPositions[d] || 'with';
      const theirsBig = theirs === 'against' || theirs === 'beyond';
      if (mine === 'beneath' && theirsBig) generosity += 1;
      if (mine === 'beyond' && theirsBig) upstaging += 1;
    }
  }

  return {
    forYou: forYou - 5 * overspend - 1.5 * generosity + 2.0 * upstaging,
    forFilm: forFilm - 3 * overspend + 1.5 * generosity - 1.5 * upstaging,
    spikiness, overspend, budget, cost, generosity, upstaging,
  };
}

// The shape of a performance across three beats (§5.6), producing the single
// Notices value and the single Ensemble contribution used everywhere else.
export function shapePerformance(perfValue, resolved, presence) {
  const lift = 9 * resolved.spikiness;
  const intro = perfValue - 0.65 * lift;
  const turn = perfValue + 1.30 * lift;
  const reso = perfValue - 0.65 * lift;
  const beats = { intro, turn, reso };
  const peak = Math.max(intro, turn, reso);

  const noticesRaw = 0.55 * peak + 0.45 * perfValue + resolved.forYou;
  // §4.1 Presence sets a floor. Re-scaled from the doc's 0.10×Presence, which
  // the review showed could never bind against a mean of 58.
  const floor = 0.42 * presence;

  return {
    beats,
    peak,
    notices: clamp(Math.max(noticesRaw, floor), 0, 100),
    ensembleValue: clamp(perfValue - 4.0 * resolved.spikiness + resolved.forFilm, 0, 100),
    floorBound: noticesRaw < floor,
  };
}

// ---------------------------------------------------------------------------
// Reception (§4.10) — one box office model, one Ensemble, one Notices.
// ---------------------------------------------------------------------------

export function reception(rng, ctx) {
  const {
    film, genre, budget, scriptQuality, directorSkill, directorPrestige,
    castStarPower, genreDemand, ensembleScore, yourNotices, billing,
    stalenessPenalty = 0, palette,
  } = ctx;

  const pal = palette ? paletteEffect(palette, genre) : { aud: 0, crit: 0 };
  const productionValue = clamp(35 + 22 * Math.log10(Math.max(1, budget)), 0, 100);
  const postLuck = rng.gauss(52, 14);

  const projectQuality = clamp(
    0.31 * scriptQuality + 0.22 * directorSkill + 0.29 * ensembleScore
      + 0.08 * productionValue + 0.10 * postLuck,
    0, 100,
  );

  const filmCritic = clamp(
    projectQuality + GENRE_ECON[genre].critBias + 0.10 * (directorPrestige - 50)
      - stalenessPenalty + pal.crit + rng.gauss(0, 4.6),
    0, 100,
  );

  const bw = BILLING_WEIGHT[billing];
  const notices = clamp(
    0.52 * yourNotices + 0.25 * filmCritic + 0.13 * (50 + 30 * bw) + rng.gauss(0, 7),
    0, 100,
  );

  const audience = clamp(
    0.62 * projectQuality + 0.17 * genreDemand + 0.11 * castStarPower
      + 0.06 * (100 - projectQuality) + pal.aud + rng.gauss(0, 4.5),
    0, 100,
  );

  // FIX-4 the doc carried two incompatible box-office models (§4.10 and §8.2).
  // This is the §8.2 shape with §4.10's rights share, and it is the only one.
  const marketing = 0.45 * budget;
  const opening = budget * (K.openingBase + 0.005 * castStarPower + 0.005 * genreDemand)
    * Math.pow(budget / 30, -0.10);
  const z = audience + rng.gauss(0, 12);
  const legs = clamp(1.7 + 0.048 * (audience - 50) + 0.032 * Math.pow(Math.max(0, z - 70), 1.5), 1.15, 8.0);
  const gross = opening * legs;
  const roi = (0.62 * gross) / (budget + marketing);

  return {
    projectQuality, filmCritic, notices, audience, postLuck,
    gross, roi, opening, legs, palette: pal,
    wrecked: postLuck < 30, blessed: postLuck > 74,
    film,
  };
}

// ---------------------------------------------------------------------------
// Standing update (§4.10 payoff, with FIX-1)
// ---------------------------------------------------------------------------

// FIX-1e Heat is market demand, and demand is a function of how many people
// saw you. A hit on a $4M film and a hit on a $140M film are the same ROI and
// nothing like the same career event — which is where the game's upper tail
// comes from, and why it is rare.
export function reach(budget) {
  return clamp(K.reachBase + K.reachCoef * Math.log10(Math.max(1, budget)), 0.3, 1.7);
}

export function applyReception(s, rec, billing, credits, budget = 20) {
  const bw = BILLING_WEIGHT[billing];
  const disc = discoveryMultiplier(credits);
  const rch = reach(budget);

  const dHeat = bw * disc * rch * (
    K.heatBase
    + K.heatRoiCoef * clamp(rec.roi - K.heatRoiCentre, -0.6, 2.2)
    + K.heatAudCoef * (rec.audience - K.heatAudCentre)
  );
  const dPrestige = bw * disc * (
    K.prestigeCriticCoef * (rec.filmCritic - K.prestigeCriticCentre)
    + K.prestigeNoticesCoef * (rec.notices - K.prestigeNoticesCentre)
  );
  const dAffection = bw * disc * rch * (K.affectionCoef * (rec.audience - K.affectionCentre));

  s.heat = clamp(s.heat + dHeat, 0, 100);
  s.prestige = clamp(s.prestige + dPrestige, 0, 100);
  s.affection = clamp(s.affection + dAffection, 0, 100);
  return { dHeat, dPrestige, dAffection, discovery: disc, reach: rch };
}

export function decayStanding(s, billingThisYear) {
  s.heat *= heatKeep(billingThisYear);
  s.affection *= K.affectionKeep;
  s.prestige *= K.prestigeKeep;
  s.notoriety *= K.notorietyKeep;
}

export function updateRecognition(actor, notices, billing) {
  // Deliberately not billing-weighted: five good minutes is five good minutes.
  const gain = K.recognitionGain * Math.max(0, notices - K.recognitionCentre)
    * (billing === 'lead' ? 0.6 : 1.0);
  actor.recognition = clamp(actor.recognition + gain, 0, 100);
}

// ---------------------------------------------------------------------------
// Awards (§4.11)
// ---------------------------------------------------------------------------

export const NARRATIVES = {
  due: { bonus: 14, label: "She's due" },
  transformation: { bonus: 12, label: 'The transformation' },
  comeback: { bonus: 11, label: 'The comeback' },
  finalBow: { bonus: 10, label: 'The final bow' },
  newcomer: { bonus: 8, label: 'The newcomer' },
  posthumous: { bonus: 20, label: 'They were overdue and now they are gone' },
  tooCommercial: { bonus: -10, label: 'Too commercial' },
  overexposed: { bonus: -7, label: 'Overexposed' },
};

export function narrativeBonus(flags) {
  let total = 0;
  const applied = [];
  for (const [k, on] of Object.entries(flags)) {
    if (on && NARRATIVES[k]) {
      total += NARRATIVES[k].bonus;
      applied.push(NARRATIVES[k].label);
    }
  }
  // FIX-7 the review found narrative outweighing merit ~2:1 against N(0,9).
  // Halved and capped, so a campaign fiction tilts a close race rather than
  // deciding an open one.
  return { total: clamp(total * 0.5, -12, 12), applied };
}

export function buzzScore(rng, ctx) {
  const { notices, filmCritic, campaignSpend, prestige, flags, categoryAdvantage } = ctx;
  const nb = narrativeBonus(flags || {});
  const value = 0.34 * notices + 0.20 * filmCritic
    + 0.14 * clamp(28 * Math.log10(1 + campaignSpend), 0, 100)
    + 0.12 * prestige + nb.total + 0.10 * (categoryAdvantage || 0)
    + rng.gauss(0, 9);
  return { value, narratives: nb.applied };
}

export function nominationChance(buzz) {
  return clamp(sig(0.13 * (buzz - K.buzzCentre)), 0, 0.62);
}

// ---------------------------------------------------------------------------
// Money (§11.6) — the going-broke ratchet
// ---------------------------------------------------------------------------

// Your fee is your quote or the going rate for the size of the film, whichever
// is larger — which is why a journeyman supporting actor makes a living and a
// star makes a fortune off the same curve.
export function fee(rng, actor, role, agentTier, recentRoi, era = 1) {
  const q = quote(actor.standing, recentRoi, era);
  const bw = BILLING_WEIGHT[role.billing];
  const negotiate = 1 + rng.float(-1, 1) * agentTier.negotiate;
  const scaleRate = (K.scaleFeeBase + K.scaleFeeCoef * role.budget) * bw;
  const capped = Math.min(Math.max(q * bw, scaleRate) * negotiate, role.budgetForRole);

  return Math.max(0.005, capped) * (1 - agentTier.commission);
}

// §11.6 the going-broke ratchet. Money in is money in; what ruins people is
// that the way they live rises to meet their best year and then comes down far
// more slowly than the work does. The floor is charged once a year, in
// endYear() — never per payment, or a good year bills you several times over.
export function applyLifestyle(moneyState, income) {
  moneyState.net += income;
  moneyState.lifetime += income;
  moneyState.floor = Math.max(moneyState.floor, K.lifestyleShare * income);
  return moneyState;
}
