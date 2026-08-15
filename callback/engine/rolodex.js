// The Rolodex — §4.12 and §6.2.
//
// Forty-odd people exist and run their own careers. Eight are *tracked*, chosen
// dynamically: whoever you have worked with most, plus anyone currently holding
// a grudge or owing you something. The rest are real and quiet.
//
// Favours are tokens attached to named people, not a pool. You earn them by
// doing things that cost you and help them, you spend them on concrete
// outcomes, and they are gone when spent. They decay at one per five years of
// no contact — which is not upkeep, because there is no button that stops it
// and no reminder that nags you to press one. People drift. That is the fact
// being modelled.

import { clamp } from './rng.js';

export const FAVOUR_EARNED = {
  scale: 2,            // took scale to be in their small film
  dayPlayer: 1,        // did a day on their project as a favour
  defended: 3,         // publicly defended them during a scandal
  recommended: 2,      // recommended them for a job they got
  picket: 2,           // held the line beside them
  hiredThem: 3,        // hired them when nobody else would
  generosity: 1,       // gave them the moment on set
};

export const FAVOUR_SPENT = {
  directOffer: 2,      // a part, no audition
  attach: 3,           // they attach to your project
  hireWhoIName: 2,
  introduction: 1,
  publicBacking: 3,
};

export class Rolodex {
  constructor(world) {
    this.world = world;
    this.edges = new Map();   // personId -> edge
  }

  edge(person) {
    let e = this.edges.get(person.id);
    if (!e) {
      e = {
        id: person.id,
        person,
        affinity: 0,
        grudge: 0,
        favours: 0,          // what they owe you
        owed: 0,             // what you owe them
        sharedProjects: 0,
        lastContact: null,
        history: [],
        dead: false,
      };
      this.edges.set(person.id, e);
    }
    e.person = person;
    return e;
  }

  note(person, text, year) {
    const e = this.edge(person);
    e.history.push({ year, text });
    if (e.history.length > 12) e.history.shift();
    e.lastContact = year;
    return e;
  }

  contact(person, year) {
    const e = this.edge(person);
    e.lastContact = year;
    e.sharedProjects += 1;
    return e;
  }

  gain(person, reason, year) {
    const e = this.edge(person);
    const n = FAVOUR_EARNED[reason] ?? 1;
    e.favours += n;
    e.affinity = clamp(e.affinity + 3 * n, -100, 100);
    e.lastContact = year;
    this.note(person, reasonText(reason, n), year);
    return n;
  }

  spend(person, reason, year) {
    const e = this.edge(person);
    const n = FAVOUR_SPENT[reason] ?? 1;
    if (e.favours < n) return false;
    e.favours -= n;
    e.lastContact = year;
    this.note(person, `You called it in. (−${n})`, year);
    return true;
  }

  // Eight tracked, chosen by weight rather than by the player maintaining a list.
  tracked(limit = 8) {
    const scored = [...this.edges.values()]
      .filter((e) => !e.dead)
      .map((e) => ({
        e,
        w: e.sharedProjects * 3 + e.favours * 4 + Math.abs(e.grudge) * 3
          + Math.abs(e.affinity) / 12 + (e.owed ? 5 : 0),
      }))
      .sort((a, b) => b.w - a.w);
    return scored.slice(0, limit).map((s) => s.e);
  }

  // Anyone who owes you enough to be worth calling.
  creditors(min = 2) {
    return [...this.edges.values()].filter((e) => !e.dead && e.favours >= min);
  }

  totalFavours() {
    return [...this.edges.values()].reduce((a, e) => a + (e.dead ? 0 : e.favours), 0);
  }

  // Called once a year. Favours fade with silence, and people die.
  tickYear(year, rng) {
    const gone = [];
    for (const e of this.edges.values()) {
      if (e.dead) continue;
      if (e.lastContact !== null && year - e.lastContact >= 5 && e.favours > 0) {
        e.favours -= 1;
        e.lastContact = year - 1; // reset the five-year clock
      }
      e.grudge = Math.max(0, e.grudge - 0.5);
      const age = e.person.age ?? 45;
      if (age > 62 && rng.chance(0.004 * (age - 62))) {
        e.dead = true;
        gone.push(e);
      }
    }
    return gone;
  }
}

function reasonText(reason, n) {
  const texts = {
    scale: 'You worked for nothing so they could make it.',
    dayPlayer: 'You gave them a day.',
    defended: 'You said so out loud, when nobody else would.',
    recommended: 'You put their name in a room they were not in.',
    picket: 'You stood on the line with them.',
    hiredThem: 'You hired them when nobody else would.',
    generosity: 'You gave them the scene.',
  };
  return `${texts[reason] || 'They owe you.'} (+${n})`;
}
