// Ambitions — §0.4.
//
// An Ambition gates nothing. No content is locked behind it, no action is
// refused because of it. It decides what the obituary measures you against and
// gives the middle of a run a shape, and the interesting part is that they
// conflict in exactly the ways the systems already model: the Fortune wants
// tentpoles, the Prize wants a campaign block every year and a prestige lane,
// the Run wants you out of the ingenue lane by 35 and never chasing Heat.
//
// You may change it once. The game notes when you did, because people do.

import { clamp, mean } from './rng.js';

export const AMBITIONS = {
  work: {
    label: 'The Work',
    blurb: 'To be good. Whether anyone notices is not the measure.',
    measure: 'lifetime average of your notices',
    score: (g) => mean(g.noticesHistory.length ? g.noticesHistory : [0]),
    grade: (v) => (v > 72 ? 'Achieved' : v > 62 ? 'Nearly' : v > 50 ? 'Sometimes' : 'No'),
    format: (v) => v.toFixed(1),
  },
  prize: {
    label: 'The Prize',
    blurb: 'The statue. Say it out loud; everyone else wants it too.',
    measure: 'awards won',
    score: (g) => g.awards.wins * 10 + g.awards.nominations * 2,
    grade: (v) => (v >= 20 ? 'Achieved' : v >= 10 ? 'Nearly' : v > 0 ? 'Sometimes' : 'No'),
    format: (v) => `${v.toFixed(0)} pts`,
  },
  fortune: {
    label: 'The Fortune',
    blurb: 'Peak net worth, and what is left at the end.',
    measure: 'money kept',
    score: (g) => Math.max(0, g.money.net) + 0.25 * g.money.lifetime,
    grade: (v) => (v > 90 ? 'Achieved' : v > 30 ? 'Nearly' : v > 6 ? 'Sometimes' : 'No'),
    format: (v) => `$${v.toFixed(0)}M`,
  },
  run: {
    label: 'The Run',
    blurb: 'To still be working at the top of the call sheet at seventy.',
    measure: 'years worked at lead level',
    score: (g) => g.stats.leadCredits + (g.stats.leadsAfter42 * 1.5),
    grade: (v) => (v >= 30 ? 'Achieved' : v >= 16 ? 'Nearly' : v >= 5 ? 'Sometimes' : 'No'),
    format: (v) => v.toFixed(0),
  },
  franchise: {
    label: 'The Franchise',
    blurb: 'To be the face of something bigger than any film in it.',
    measure: 'peak indispensability to a property',
    score: (g) => g.stats.peakIdentification || 0,
    grade: (v) => (v >= 70 ? 'Achieved' : v >= 45 ? 'Nearly' : v > 12 ? 'Sometimes' : 'No'),
    format: (v) => v.toFixed(0),
  },
  voice: {
    label: 'The Voice',
    blurb: 'To be legible as one specific thing, and to be respected for it.',
    measure: 'sustained legibility above 70 with critics on side',
    score: (g) => g.stats.voiceYears * 2 + Math.max(0, g.actor.standing.prestige - 50),
    grade: (v) => (v >= 50 ? 'Achieved' : v >= 25 ? 'Nearly' : v > 6 ? 'Sometimes' : 'No'),
    format: (v) => v.toFixed(0),
  },
};

export function ambitionReport(game) {
  const a = AMBITIONS[game.ambition] || AMBITIONS.work;
  const v = a.score(game);
  if (!game.credits.length) {
    return {
      label: a.label, measure: a.measure, value: '—',
      grade: 'Too early to say', changed: game.ambitionChangedAt,
    };
  }
  return {
    label: a.label,
    measure: a.measure,
    value: a.format(v),
    grade: a.grade(v),
    changed: game.ambitionChangedAt,
  };
}

// A soft nudge the interface can show: what this Ambition would have you do
// with the board in front of you. Advice, never a gate.
export function ambitionAdvice(game, role) {
  switch (game.ambition) {
    case 'prize':
      return role.scriptQuality > 70 && role.billing !== 'bit'
        ? 'This is the kind of part that gets campaigned.' : null;
    case 'fortune':
      return role.budget > 90 ? 'This is where the money is.' : null;
    case 'run':
      return role.archetype === 'character_actor' || role.archetype === 'authority'
        ? 'This is the lane that stays open after fifty.' : null;
    case 'franchise':
      return role.type === 'tentpole' && role.billing === 'lead'
        ? 'Properties come from parts like this.' : null;
    case 'voice':
      return game.legibility < 70 && role.genre === dominantGenre(game)
        ? 'Another one of these sharpens what you are.' : null;
    case 'work':
    default:
      return role.director && game.world.directorSkill(role.director) > 72
        ? 'You would be better in this than in anything else on the board.' : null;
  }
}

function dominantGenre(game) {
  const g = game.actor.persona.genre;
  return Object.keys(g).reduce((best, k) => (g[k] > g[best] ? k : best), Object.keys(g)[0]);
}

export function clampAmbition(key) {
  return AMBITIONS[key] ? key : 'work';
}

export { clamp };
