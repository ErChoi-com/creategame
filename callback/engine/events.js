// Two pools of authored content, both governed by the same rule: every option
// has to be defensible, or it is not a choice and does not belong here (§0.1).
//
//   MOMENT_POOL — what happens on a set. The most-repeated interaction in the
//   game, so it cannot be three table cells; the pool is drawn from by what
//   the production actually is, and a veteran sees fewer of them.
//
//   LIFE_EVENTS — at most one a year, and only ever fired by something true
//   about your state: you are broke, you are exhausted, someone hates you,
//   the press has noticed. Nothing here is upkeep and nothing here is random
//   noise you have to click past.

import { clamp } from './rng.js';
import * as M from './model.js';

// ---------------------------------------------------------------------------
// ON SET
// ---------------------------------------------------------------------------
export const MOMENT_POOL = [
  {
    id: 'not_working',
    core: true,
    prompt: 'The scene is not working. Sixth take, and everyone knows.',
    options: [
      { id: 'suggest', label: 'Suggest a change', effect: { chemistry: -4, prep: 8, affinity: -3 } },
      { id: 'absorb', label: 'Take the note and give them exactly what they asked for', effect: { chemistry: 4, prep: -2, affinity: 4 } },
      { id: 'ask', label: 'Ask the director what they actually want', effect: { prep: 4, condition: -2, affinity: 2 } },
    ],
  },
  {
    id: 'adjustment',
    core: true,
    prompt: 'The adjustment is wrong. You are sure of it, and you might be wrong about that.',
    options: [
      { id: 'take', label: 'Take it', effect: { affinity: 6, perf: -3 } },
      { id: 'argue', label: 'Argue for yours', effect: { affinity: -7, perf: 5, chemistry: -3 } },
      { id: 'both', label: 'Give them both and let the edit decide', effect: { condition: -5, perf: 2, affinity: 1 } },
    ],
  },
  {
    id: 'discovery',
    core: true,
    prompt: 'Something happened in the rehearsal that is not in the script.',
    options: [
      { id: 'keep', label: 'Keep it. Play it in the take.', effect: { perf: 6, ensemble: -2, condition: -2 } },
      { id: 'offer', label: 'Offer it to your scene partner instead', effect: { perf: -1, ensemble: 4, affinity: 8, favour: 1 } },
      { id: 'lose', label: 'Let it go. It was a rehearsal thing.', effect: {} },
    ],
  },
  {
    id: 'costar_late',
    when: (c) => c.costar.ego > 66,
    prompt: 'Your co-star has been two hours late three days running, and the crew is looking at you.',
    options: [
      { id: 'cover', label: 'Say nothing and cover for them', effect: { chemistry: 6, condition: -4, costarAffinity: 12 } },
      { id: 'raise', label: 'Raise it with the first AD', effect: { chemistry: -8, condition: 4, costarGrudge: 20 } },
      { id: 'match', label: 'Start turning up late yourself', effect: { affinity: -10, condition: 6, chemistry: 3 } },
    ],
  },
  {
    id: 'night_shoot',
    when: (c) => c.chaos > 58,
    prompt: 'Week four of night shoots. You have not seen daylight and the schedule has slipped again.',
    options: [
      { id: 'push', label: 'Push through it', effect: { condition: -10, perf: 3, affinity: 4 } },
      { id: 'pace', label: 'Pace yourself and protect the big scenes', effect: { perf: -2, condition: 4 } },
      { id: 'flag', label: 'Tell production the schedule is not survivable', effect: { affinity: -6, condition: 8, chemistry: -2 } },
    ],
  },
  {
    id: 'rewrite_pages',
    when: (c) => c.director.temperament === 'chaotic',
    prompt: 'New pages at 6am. Your best scene is gone and something else is in its place.',
    options: [
      { id: 'learn', label: 'Learn them in the van', effect: { prep: -10, perf: 2, affinity: 8 } },
      { id: 'refuse', label: 'Say you will shoot what you prepared', effect: { affinity: -14, perf: 4 } },
      { id: 'negotiate', label: 'Ask for the old scene back in exchange for the rest', effect: { affinity: -3, prep: 4, perf: 1 } },
    ],
  },
  {
    id: 'crew_love',
    when: (c) => c.chaos < 45,
    prompt: 'The crew has started saving you a chair. Somebody made you a mug with your character on it.',
    options: [
      { id: 'lean', label: 'Spend your breaks with them', effect: { condition: 5, chemistry: 4, crew: 1 } },
      { id: 'work', label: 'Stay in it between setups', effect: { perf: 4, chemistry: -3, condition: -3 } },
    ],
  },
  {
    id: 'director_doubt',
    when: (c) => c.director.temperament === 'remote',
    prompt: 'The director has not spoken to you in nine days. You cannot tell if that is good.',
    options: [
      { id: 'ask', label: 'Ask them directly', effect: { affinity: -4, prep: 6 } },
      { id: 'trust', label: 'Assume it means they are happy', effect: { perf: -2, condition: 2 } },
      { id: 'dp', label: 'Ask the cinematographer instead', effect: { prep: 4, affinity: 2, crew: 1 } },
    ],
  },
  {
    id: 'stunt',
    when: (c) => c.role.genre === 'action' || c.role.genre === 'thriller',
    prompt: 'They would like you to do the fall yourself. Insurance would prefer you did not.',
    options: [
      { id: 'do_it', label: 'Do it yourself', effect: { perf: 5, affinity: 6, injuryRisk: 0.22 } },
      { id: 'double', label: 'Use the double', effect: { perf: -1, affinity: -3 } },
      { id: 'half', label: 'Do the approach, let the double take the impact', effect: { perf: 2, injuryRisk: 0.07 } },
    ],
  },
  {
    id: 'press_visit',
    when: (c) => c.role.budget > 60,
    prompt: 'A journalist is on set for the day, and your co-star has already said something unwise.',
    options: [
      { id: 'smooth', label: 'Smooth it over on the record', effect: { costarAffinity: 14, notoriety: -2, affinity: 2 } },
      { id: 'distance', label: 'Make clear it was not your view', effect: { costarGrudge: 18, notoriety: -4 } },
      { id: 'join', label: 'Agree with them, loudly', effect: { costarAffinity: 20, notoriety: 9 } },
    ],
  },
];

export function momentsAvailable(ctx) {
  return MOMENT_POOL.filter((m) => !m.when || m.when(ctx));
}

// ---------------------------------------------------------------------------
// A LIFE
// ---------------------------------------------------------------------------
export const LIFE_EVENTS = [
  {
    id: 'broke',
    when: (g) => g.money.net < 0,
    prompt: 'The money is gone. Your accountant has stopped using the word "temporary".',
    options: [
      {
        label: 'Take the first thing that pays',
        text: 'You take the commercial. Everyone sees it.',
        run: (g) => {
          const cash = clamp(0.3 + M.standing(g.actor.standing) / 30, 0.3, 4);
          g.money.net += cash;
          g.money.lifetime += cash;
          g.actor.standing.prestige = clamp(g.actor.standing.prestige - 5, 0, 100);
          g.actor.standing.affection = clamp(g.actor.standing.affection + 3, 0, 100);
        },
      },
      {
        label: 'Sell the house and live smaller',
        text: 'A smaller place, and the ratchet finally goes the other way.',
        run: (g) => { g.money.floor *= 0.55; g.money.net += 0.6; },
      },
      {
        label: 'Borrow against the next job',
        text: 'You borrow. It costs more than it looks like it costs.',
        run: (g) => { g.money.net += 1.2; g.money.floor *= 1.12; g.actor.flags.indebted = g.year; },
      },
    ],
  },
  {
    id: 'burnout',
    when: (g) => g.actor.condition < 45,
    prompt: 'You have worked every quarter for years and you cannot remember the last week you were not someone else.',
    options: [
      {
        label: 'Take the year off',
        text: 'You take the year. The board will be colder when you come back.',
        run: (g) => {
          g.actor.condition = clamp(g.actor.condition + 35, 0, 100);
          g.actor.health = clamp(g.actor.health + 8, 0, 100);
          // A year, not an open-ended vanishing: that is a different decision,
          // and it lives in the moves menu where you can end it yourself.
          g.hiatus = true;
          g.hiatusUntil = g.year + 1;
        },
      },
      {
        label: 'Keep going',
        text: 'You keep going. Everyone says how prolific you are.',
        run: (g) => {
          g.actor.condition = clamp(g.actor.condition - 6, 5, 100);
          g.actor.health = clamp(g.actor.health - 5, 0, 100);
          g.actor.attrs.resilience = clamp(g.actor.attrs.resilience - 3, 5, 99);
        },
      },
      {
        label: 'Get help',
        text: 'Twice a week, and it is duller and more useful than the films make it look.',
        run: (g) => {
          g.actor.attrs.resilience = clamp(g.actor.attrs.resilience + 6, 5, 99);
          g.actor.condition = clamp(g.actor.condition + 12, 0, 100);
          g.money.net -= 0.06;
        },
      },
    ],
  },
  {
    id: 'story_breaking',
    when: (g) => g.actor.standing.notoriety > 30,
    prompt: 'A paper has a story about you and has offered you the chance to comment.',
    options: [
      {
        label: 'Say nothing',
        text: 'You say nothing. It runs anyway, and then it goes away faster.',
        run: (g) => { g.actor.standing.notoriety = clamp(g.actor.standing.notoriety - 6, 0, 100); },
      },
      {
        label: 'Get ahead of it in your own words',
        text: 'You tell it yourself first. Some people find that admirable.',
        run: (g) => {
          g.actor.standing.notoriety = clamp(g.actor.standing.notoriety - 12, 0, 100);
          g.actor.standing.affection = clamp(g.actor.standing.affection + 6, 0, 100);
          g.actor.standing.prestige = clamp(g.actor.standing.prestige - 2, 0, 100);
        },
      },
      {
        label: 'Sue',
        text: 'Lawyers. It runs longer and everyone reads the coverage of the case.',
        run: (g) => {
          g.money.net -= clamp(0.2 + g.money.net * 0.05, 0.2, 2);
          g.actor.standing.notoriety = clamp(g.actor.standing.notoriety + 8, 0, 100);
          g.actor.standing.affection = clamp(g.actor.standing.affection + 2, 0, 100);
        },
      },
    ],
  },
  {
    id: 'grudge_room',
    when: (g) => g.rolodex.tracked().some((e) => e.grudge > 35),
    prompt: (g) => {
      const e = g.rolodex.tracked().find((x) => x.grudge > 35);
      return `${e.person.name}, who has not spoken to you in years, is at the same eight-person dinner.`;
    },
    options: [
      {
        label: 'Apologise, whether or not you were wrong',
        text: 'It is awkward for ninety seconds and then it is over.',
        run: (g) => {
          const e = g.rolodex.tracked().find((x) => x.grudge > 35);
          if (e) { e.grudge = clamp(e.grudge - 40, 0, 100); e.affinity = clamp(e.affinity + 15, -100, 100); }
        },
      },
      {
        label: 'Be perfectly polite and nothing else',
        text: 'Perfectly polite. Everyone at the table notices.',
        run: () => {},
      },
      {
        label: 'Say the true thing, at the table',
        text: 'You say it. Two people at that table will repeat it for a decade.',
        run: (g) => {
          const e = g.rolodex.tracked().find((x) => x.grudge > 35);
          if (e) e.grudge = clamp(e.grudge + 25, 0, 100);
          g.actor.standing.notoriety = clamp(g.actor.standing.notoriety + 7, 0, 100);
        },
      },
    ],
  },
  {
    id: 'offered_a_lane',
    when: (g) => g.legibility > 72 && g.credits.length > 8,
    prompt: 'Your agent, gently: everything coming in is the same part. There is a version of this that lasts twenty years.',
    options: [
      {
        label: 'Take the lane. It is a living.',
        text: 'You take the lane. It pays and it pays and it pays.',
        run: (g) => {
          g.standingOrders.floor = 'anything';
          g.actor.standing.heat = clamp(g.actor.standing.heat + 6, 0, 100);
          g.actor.flags.tookTheLane = g.year;
        },
      },
      {
        label: 'Refuse everything that looks like it, starting now',
        text: 'You start saying no to the thing you are good at.',
        run: (g) => {
          g.standingOrders.floor = 'supporting';
          for (const k of Object.keys(g.actor.persona.archetype)) g.actor.persona.archetype[k] *= 0.8;
          g.actor.standing.heat = clamp(g.actor.standing.heat - 5, 0, 100);
        },
      },
    ],
  },
  {
    id: 'someone_asks',
    when: (g) => g.credits.length > 14 && g.actor.age > 40,
    prompt: (g) => {
      const kid = g.world.costars.find((c) => c.age < 26) || g.world.costars[0];
      return `${kid.name}, who is twenty-three and frightened, has asked you what to do.`;
    },
    options: [
      {
        label: 'Tell them the truth about the odds',
        text: 'You tell them the truth. They will remember that you did.',
        run: (g) => {
          const kid = g.world.costars.find((c) => c.age < 26) || g.world.costars[0];
          g.rolodex.gain(kid, 'recommended', g.year);
        },
      },
      {
        label: 'Put them up for something',
        text: 'You make one call. It is not much and it is everything.',
        run: (g) => {
          const kid = g.world.costars.find((c) => c.age < 26) || g.world.costars[0];
          g.mentees.push({ person: kid, since: g.year, power: 0 });
          g.rolodex.gain(kid, 'hiredThem', g.year);
        },
      },
      {
        label: 'Say something encouraging and leave',
        text: 'You say something encouraging. You have a car waiting.',
        run: () => {},
      },
    ],
  },
  {
    id: 'the_body',
    when: (g) => g.actor.health < 62 && g.actor.age > 46,
    prompt: 'A scan that was meant to be routine has produced a follow-up appointment.',
    options: [
      {
        label: 'Deal with it properly and lose the quarter',
        text: 'You deal with it. It costs a job and it buys years.',
        run: (g) => {
          g.actor.health = clamp(g.actor.health + 16, 0, 100);
          g.blocksBooked = Math.min(4, g.blocksBooked + 1);
        },
      },
      {
        label: 'Work through it and tell nobody',
        text: 'You tell nobody. Insurance is a thing you have opinions about now.',
        run: (g) => {
          g.actor.health = clamp(g.actor.health - 8, 0, 100);
          g.actor.condition = clamp(g.actor.condition - 6, 5, 100);
        },
      },
    ],
  },
  {
    id: 'mentee_arrives',
    when: (g) => g.mentees.some((m) => m.power > 60 && !m.repaid),
    prompt: (g) => {
      const m = g.mentees.find((x) => x.power > 60 && !x.repaid);
      return `${m.person.name}, who you taught, is casting something and wants to know if you would read it.`;
    },
    options: [
      {
        label: 'Read it, and say yes',
        text: 'You say yes before you finish it.',
        run: (g) => {
          const m = g.mentees.find((x) => x.power > 60 && !x.repaid);
          if (!m) return;
          m.repaid = true;
          const role = g.world.generateRole(g.actor, { billing: 'lead' });
          role.title = role.title;
          role.path = 'direct';
          role.yours = true;
          role.difficulty = 0;
          role.scriptQuality = clamp(role.scriptQuality + 12, 5, 98);
          role.viaFavour = m.person.name;
          g.board.unshift(role);
        },
      },
      {
        label: 'Read it, and tell them the truth about it',
        text: 'You tell them what is wrong with it. They rewrite. It is better.',
        run: (g) => {
          const m = g.mentees.find((x) => x.power > 60 && !x.repaid);
          if (m) { m.repaid = true; g.rolodex.gain(m.person, 'recommended', g.year); }
          g.actor.standing.prestige = clamp(g.actor.standing.prestige + 3, 0, 100);
        },
      },
    ],
  },
];

// At most one a year, and only when something in your state actually fired it.
export function pickLifeEvent(game) {
  const eligible = LIFE_EVENTS.filter((e) => {
    if (game.firedEvents.has(e.id) && !e.repeatable) return false;
    try { return e.when(game); } catch { return false; }
  });
  if (!eligible.length) return null;
  return eligible[game.rng.int(0, eligible.length - 1)];
}

export function eventPrompt(event, game) {
  return typeof event.prompt === 'function' ? event.prompt(game) : event.prompt;
}
