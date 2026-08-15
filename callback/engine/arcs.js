// Arcs — the storylet patterns the one-shot events in events.js cannot express.
//
// The literature on quality-based narrative (Failbetter's storylets, and the
// pattern catalogue that grew out of them) names the shapes this file needs:
//
//   THE CHAIN   a sequence that progresses toward an ending
//   THE CLOCK   a hidden quality that rises on its own while conditions hold,
//               surfacing a different scene each time it crosses a threshold
//   THE GRAVITY WELL  what happens when a vein is exhausted, so a finished arc
//               leaves a mark rather than simply going quiet
//
// §11.2 asks for addiction "as an arc, not a flag", and that is exactly a
// clock driving a chain: the level rises because of how you are living, the
// scenes change as it rises, and the ending is different depending on where
// you got off.
//
// Same rules as everything else in this game: at most one of these reaches the
// player in a year, every option is defensible, and nothing here is upkeep —
// an arc's clock is driven by what you did, never by whether you clicked.

import { clamp } from './rng.js';
import * as M from './model.js';

export const ARCS = [
  // -------------------------------------------------------------------------
  {
    id: 'drinking',
    label: 'The drinking',
    // Starts when the life is doing the thing that starts it.
    start: (g) => g.stats.coldYears >= 2 || (g.blocksBooked >= 4 && g.actor.condition < 60),
    // The clock: how the year went decides how fast it moves.
    drift: (g) => {
      let d = 0;
      if (g.actor.condition < 55) d += 1.4;
      if (g.stats.coldYears >= 2) d += 1.2;
      if (g.actor.standing.notoriety > 30) d += 0.8;
      if (g.blocksBooked === 0) d += 1.0;
      if (g.actor.attrs.resilience > 60) d -= 1.0;
      if (g.actor.flags.sober) d -= 2.5;
      return d - 0.6;
    },
    stages: [
      {
        at: 4,
        prompt: 'It is a drink after work, and then it is a drink instead of the rest of the evening. '
          + 'Nobody has said anything.',
        options: [
          {
            label: 'It is fine. Everyone in this business drinks.',
            text: 'It is fine. Everyone in this business drinks.',
            run: (g) => { g.arcState('drinking').level += 2; },
          },
          {
            label: 'Cut it back to weekends',
            text: 'Weekends only, mostly, for a while.',
            run: (g) => { g.arcState('drinking').level -= 3; },
          },
          {
            label: 'Stop entirely, and be boring about it',
            text: 'You stop. You become the person at dinner who is not drinking.',
            run: (g) => {
              g.actor.flags.sober = g.year;
              g.arcState('drinking').level -= 6;
              g.actor.attrs.resilience = clamp(g.actor.attrs.resilience + 3, 5, 99);
            },
          },
        ],
      },
      {
        at: 10,
        prompt: 'You were late twice and one of the takes is unusable. The first AD has started '
          + 'scheduling your coverage for the morning.',
        options: [
          {
            label: 'Apologise and get through the shoot',
            text: 'You apologise. You get through it. The schedule stays changed.',
            run: (g) => { g.actor.condition = clamp(g.actor.condition - 6, 5, 100); },
          },
          {
            label: 'Take the month off and dry out',
            text: 'A month somewhere quiet, at your own expense, and nobody is told which quiet place.',
            run: (g) => {
              g.arcState('drinking').level -= 8;
              g.money.net -= 0.4;
              g.blocksBooked = Math.min(4, g.blocksBooked + 1);
              g.actor.condition = clamp(g.actor.condition + 14, 5, 100);
            },
          },
          {
            label: 'Blame the schedule, loudly',
            text: 'You say it was the schedule. Two people who were there disagree, on the record.',
            run: (g) => {
              g.actor.standing.notoriety = clamp(g.actor.standing.notoriety + 9, 0, 100);
              g.arcState('drinking').level += 2;
            },
          },
        ],
      },
      {
        at: 17,
        prompt: 'The insurance company has questions about you, which means the studio has questions '
          + 'about you, which means the part is gone.',
        options: [
          {
            label: 'Go to the place they send people',
            text: 'Twenty-eight days. It is not cinematic and it works more often than not.',
            run: (g, rng) => {
              g.blocksBooked = 4;
              g.money.net -= 0.6;
              if (rng.chance(0.62)) {
                g.actor.flags.sober = g.year;
                g.arcState('drinking').level = 2;
                g.actor.attrs.resilience = clamp(g.actor.attrs.resilience + 6, 5, 99);
              } else {
                g.arcState('drinking').level -= 4;
              }
            },
          },
          {
            label: 'Handle it privately',
            text: 'You handle it yourself. You are handling it.',
            run: (g) => {
              g.arcState('drinking').level += 3;
              g.actor.standing.notoriety = clamp(g.actor.standing.notoriety + 4, 0, 100);
            },
          },
        ],
      },
      {
        at: 26,
        terminal: true,
        prompt: 'You are uninsurable. Nobody will say the word, and every offer that mattered has '
          + 'quietly stopped arriving.',
        options: [
          {
            label: 'Work anyway, wherever will have you',
            text: 'Non-union, low-budget, nobody asking questions. It is still the work.',
            run: (g) => {
              g.actor.flags.uninsurable = g.year;
              g.actor.health = clamp(g.actor.health - 12, 0, 100);
            },
          },
          {
            label: 'Stop, properly, and take however long it takes',
            text: 'You stop. It takes two years and the two years are not in the papers.',
            run: (g) => {
              g.actor.flags.sober = g.year;
              g.hiatus = true;
              g.hiatusUntil = g.year + 2;
              g.arcState('drinking').level = 0;
              g.actor.health = clamp(g.actor.health + 10, 0, 100);
              g.actor.attrs.resilience = clamp(g.actor.attrs.resilience + 8, 5, 99);
            },
          },
        ],
      },
    ],
    // The gravity well: a finished arc leaves something behind rather than
    // simply ceasing to fire.
    afterword: (g) => (g.actor.flags.sober
      ? 'You have not had a drink in years. It comes up in every profile.'
      : 'The drinking is a fact about you now, and everyone books around it.'),
  },

  // -------------------------------------------------------------------------
  {
    id: 'rival',
    label: 'The rival',
    start: (g) => g.credits.length > 5
      && g.rolodex.tracked().some((e) => e.person.kind === 'costar' && e.grudge > 15),
    drift: (g) => {
      const r = g.rolodex.tracked().find((e) => e.person.kind === 'costar' && e.grudge > 10);
      if (!r) return -1.5;
      return 1.2 + (r.grudge > 40 ? 1.2 : 0) + (r.person.heat > g.actor.standing.heat ? 1 : 0);
    },
    who: (g) => g.rolodex.tracked().find((e) => e.person.kind === 'costar' && e.grudge > 10),
    stages: [
      {
        at: 4,
        prompt: (g, who) => `${who.person.name} is up for the same part you are, and told the trades `
          + 'they had been offered it first.',
        options: [
          {
            label: 'Say nothing and read better',
            text: 'You say nothing. You read better. It is not always enough.',
            run: (g) => { g.actor.attrs.craft = clamp(g.actor.attrs.craft + 1, 5, 99); },
          },
          {
            label: 'Correct the record',
            text: 'You correct the record. Now there are two versions and one story.',
            run: (g, rng, who) => {
              g.actor.standing.notoriety = clamp(g.actor.standing.notoriety + 6, 0, 100);
              if (who) who.grudge = clamp(who.grudge + 20, 0, 100);
            },
          },
          {
            label: 'Call them',
            text: 'You call them. It is a short, strange, useful conversation.',
            run: (g, rng, who) => {
              if (who) { who.grudge = clamp(who.grudge - 25, 0, 100); who.affinity = clamp(who.affinity + 10, -100, 100); }
            },
          },
        ],
      },
      {
        at: 11,
        prompt: (g, who) => `${who.person.name} won the thing you were nominated for, and thanked `
          + 'you in the speech in a way that was not kind.',
        options: [
          {
            label: 'Applaud, on camera, for the full eleven seconds',
            text: 'You applaud for the full eleven seconds. It is the most acting you do that year.',
            run: (g) => { g.actor.standing.affection = clamp(g.actor.standing.affection + 5, 0, 100); },
          },
          {
            label: 'Leave before the party',
            text: 'You leave before the party. Two photographers get it.',
            run: (g) => { g.actor.standing.notoriety = clamp(g.actor.standing.notoriety + 7, 0, 100); },
          },
          {
            label: 'Say the true thing to a journalist',
            text: 'You say the true thing to a journalist and it runs for a fortnight.',
            run: (g, rng, who) => {
              g.actor.standing.notoriety = clamp(g.actor.standing.notoriety + 12, 0, 100);
              g.actor.standing.heat = clamp(g.actor.standing.heat + 6, 0, 100);
              if (who) who.grudge = clamp(who.grudge + 30, 0, 100);
            },
          },
        ],
      },
      {
        at: 20,
        terminal: true,
        prompt: (g, who) => `${who.person.name} is directing now, and the part is one you would be `
          + 'right for. They have to decide whether the last twenty years matter.',
        options: [
          {
            label: 'Put yourself on tape for them',
            text: 'You put yourself on tape for the person who has spent twenty years not casting you.',
            run: (g, rng, who) => {
              if (!who) return;
              if (rng.chance(clamp(0.5 - who.grudge / 200, 0.1, 0.8))) {
                who.grudge = 0;
                who.affinity = clamp(who.affinity + 40, -100, 100);
                const role = g.world.generateRole(g.actor, { billing: 'supporting' });
                role.path = 'direct';
                role.viaFavour = who.person.name;
                role.difficulty = 0;
                role.scriptQuality = clamp(role.scriptQuality + 10, 5, 98);
                g.board.unshift(role);
              } else {
                g.say('They watched it. They did not call.', 'bad');
              }
            },
          },
          {
            label: 'Let it lie',
            text: 'You let it lie. Some things get to stay unresolved.',
            run: () => {},
          },
        ],
      },
    ],
    afterword: () => 'That one is settled, one way or the other.',
  },

  // -------------------------------------------------------------------------
  {
    id: 'the_body',
    label: 'The body',
    start: (g) => g.actor.age > 52 || g.actor.health < 60,
    drift: (g) => 0.8 + (g.actor.age > 62 ? 1.0 : 0) + (g.actor.health < 55 ? 1.2 : 0)
      + (g.blocksBooked >= 4 ? 0.8 : -0.4),
    stages: [
      {
        at: 5,
        prompt: 'The stunt coordinator has started walking you through things you used to just do.',
        options: [
          {
            label: 'Train for it, seriously, at your age',
            text: 'Six mornings a week with somebody half your age shouting encouragement.',
            run: (g) => {
              g.actor.gates.physicality = clamp(g.actor.gates.physicality + 7, 5, 98);
              g.actor.condition = clamp(g.actor.condition - 5, 5, 100);
            },
          },
          {
            label: 'Let the parts change instead',
            text: 'You stop reading for the ones that need running, and the other pile is larger anyway.',
            run: (g) => {
              for (const k of ['leading_hero', 'romantic_lead', 'ingenue']) {
                g.actor.persona.archetype[k] *= 0.7;
              }
              for (const k of ['character_actor', 'authority']) {
                g.actor.persona.archetype[k] = clamp(g.actor.persona.archetype[k] + 14, 0, 100);
              }
            },
          },
        ],
      },
      {
        at: 13,
        prompt: 'A director you like says the word "distinguished" about your face, and means it kindly.',
        options: [
          {
            label: 'Have the work done',
            text: 'It is very good work and almost nobody can tell.',
            run: (g, rng) => {
              g.money.net -= clamp(0.1 + g.money.net * 0.04, 0.1, 2);
              g.actor.gates.look = clamp(g.actor.gates.look + 12, 5, 98);
              if (rng.chance(0.12)) {
                g.actor.attrs.presence = clamp(g.actor.attrs.presence - 6, 5, 99);
                g.say('Something is off about the face now. Nobody says what.', 'bad');
              }
            },
          },
          {
            label: 'Let the face do what it is doing',
            text: 'You let it happen. It photographs like a person things have happened to.',
            run: (g) => {
              g.actor.standing.prestige = clamp(g.actor.standing.prestige + 4, 0, 100);
              g.actor.persona.archetype.character_actor = clamp(
                g.actor.persona.archetype.character_actor + 12, 0, 100,
              );
            },
          },
        ],
      },
      {
        at: 22,
        terminal: true,
        prompt: 'Your body has made a decision about the next ten years and is informing you of it.',
        options: [
          {
            label: 'Work only from a chair, and only for people worth it',
            text: 'Fewer days, better rooms. The parts that are left are mostly good ones.',
            run: (g) => {
              g.standingOrders.floor = 'supporting';
              g.actor.health = clamp(g.actor.health + 6, 0, 100);
              g.actor.standing.prestige = clamp(g.actor.standing.prestige + 6, 0, 100);
            },
          },
          {
            label: 'Keep going exactly as you are',
            text: 'You keep going exactly as you are, which is the whole answer to the question.',
            run: (g) => {
              g.actor.health = clamp(g.actor.health - 10, 0, 100);
              g.actor.standing.affection = clamp(g.actor.standing.affection + 6, 0, 100);
            },
          },
        ],
      },
    ],
    afterword: () => 'You know what you can do now, which is not nothing.',
  },
];

export const ARCS_BY_ID = Object.fromEntries(ARCS.map((a) => [a.id, a]));

// Advance every running arc's clock and start any whose conditions now hold.
// Returns the arc scene to show, if one crossed a threshold this year.
export function tickArcs(game) {
  let surfaced = null;
  for (const arc of ARCS) {
    const state = game.arcState(arc.id);
    if (state.done) continue;
    if (!state.started) {
      let starts = false;
      try { starts = arc.start(game); } catch { starts = false; }
      if (!starts) continue;
      state.started = game.year;
    }

    let drift = 0;
    try { drift = arc.drift(game); } catch { drift = 0; }
    state.level = clamp(state.level + drift, 0, 40);

    // The next stage this level has reached and not yet played.
    const next = arc.stages.find((s, i) => i >= state.stage && state.level >= s.at);
    if (!next || surfaced) continue;
    // Only surface if the scene can still be written — an arc about a person
    // who has left the story quietly closes instead.
    if (arc.who && !arc.who(game)) {
      state.stage = arc.stages.indexOf(next) + 1;
      if (state.stage >= arc.stages.length) state.done = true;
      continue;
    }
    surfaced = { arc, stage: next, index: arc.stages.indexOf(next) };
  }
  return surfaced;
}

export function arcPrompt(arc, stage, game) {
  const who = arc.who ? arc.who(game) : null;
  if (typeof stage.prompt !== 'function') return stage.prompt;
  // The person an arc is about can be gone by the time its next scene fires —
  // the grudge faded, or they died. The arc has to survive that.
  if (arc.who && !who) return null;
  return stage.prompt(game, who);
}
