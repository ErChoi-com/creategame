// Part 6 — leverage: the half of a career where you act on the industry.
//
// Everything in this file is PULL. The game never prompts any of it, never
// reminds you it exists, and never punishes you for not opening the menu
// (§0.3 rule 2b). That is the licence for the breadth: a player who ignores
// this file plays a clean uncluttered career, and sim/agency.mjs verifies that
// such a career still meets every target in §14.9.
//
// The gates are resources — favours, standing, money, blocks, information —
// never permissions (§6.7). There is no ladder and no prerequisite anywhere in
// this catalogue.

import { clamp } from './rng.js';
import * as M from './model.js';
import { GENRES } from './data.js';

// A tiny helper so every action reads the same way.
const A = (def) => ({
  salience: () => 0.3,
  available: () => true,
  cost: () => '',
  ...def,
});

// ---------------------------------------------------------------------------
// GET WORK THAT WASN'T OFFERED YOU
// ---------------------------------------------------------------------------
const GET_WORK = [
  A({
    id: 'campaign_for_role',
    category: 'Get work',
    label: 'Publicly campaign for a part',
    blurb: 'Say in an interview that you want it. Everyone will know if you do not get it.',
    cost: () => 'Notoriety +6 if you miss',
    needs: 'boardRole',
    available: (g, c) => !!c.role && c.role.path === 'audition',
    salience: (g, c) => (c.role && c.role.billing !== 'bit' ? 0.7 : 0.2),
    run: (g, c) => {
      const r = c.role;
      r.chance = clamp(r.chance * 2.1, 0, 0.9);
      r.campaigned = true;
      g.flagCampaign(r);
      return { text: `You said it out loud: you want ${r.title}. The trades picked it up.` };
    },
  }),
  A({
    id: 'screen_test_free',
    category: 'Get work',
    label: 'Screen-test for free',
    blurb: 'No fee, no agent, no standing. Just the work, in a room, on tape.',
    cost: () => 'Half a block, and the room sees you want it',
    needs: 'boardRole',
    available: (g, c) => !!c.role && c.role.path === 'audition',
    salience: (g, c) => (M.standing(g.actor.standing) < 40 ? 0.8 : 0.25),
    run: (g, c) => {
      const r = c.role;
      // Bypasses the Standing term in §4.4 entirely — this is the great
      // equaliser for an unknown who can actually act.
      const craftOnly = 0.35 * r.fit + 0.30 * (0.6 * g.actor.attrs.craft + 0.4 * g.actor.attrs.instinct) + 22;
      r.chance = clamp(M.offerProbability(Math.max(r.utility, craftOnly), r.difficulty), 0, 0.92);
      r.screenTested = true;
      return { text: `You put ${r.title} on tape yourself. It is only the work now.` };
    },
  }),
  A({
    id: 'take_scale',
    category: 'Get work',
    label: 'Take scale to work with someone',
    blurb: 'Waive the fee. They will remember, and you will be better afterwards.',
    cost: () => 'The entire fee',
    needs: 'boardRole',
    available: (g, c) => !!c.role,
    salience: (g, c) => (c.role && g.world.directorSkill(c.role.director) > 70 ? 0.85 : 0.3),
    run: (g, c) => {
      const r = c.role;
      r.takeScale = true;
      r.chance = clamp(r.chance * 1.6, 0, 0.95);
      return { text: `You told them you would do ${r.title} for scale. The offer got easier immediately.` };
    },
  }),
  A({
    id: 'call_in_favour',
    category: 'Get work',
    label: 'Call in a favour for a part',
    blurb: 'Someone owes you. A part appears, with no audition.',
    cost: () => '2 favours',
    available: (g) => g.rolodex.creditors(2).length > 0,
    salience: (g) => (g.rolodex.creditors(2).length && g.board.length < 3 ? 0.9 : 0.5),
    run: (g, c, rng) => {
      const e = c.person || g.rolodex.creditors(2)
        .sort((x, y) => y.favours - x.favours)[0];
      if (!e || !g.rolodex.spend(e.person, 'directOffer', g.year)) {
        return { text: 'Nobody owes you enough for that.' };
      }
      const role = g.world.generateRole(g.actor, { billing: rng.chance(0.45) ? 'lead' : 'supporting' });
      role.director = e.person.kind === 'director' ? e.person : role.director;
      role.path = 'direct';
      role.chance = 1;
      role.fit = M.fitScore(g.actor, role);
      role.utility = M.utility(g.actor, role, 40);
      role.viaFavour = e.person.name;
      g.board.unshift(role);
      return { text: `${e.person.name} made a call. ${role.title} is yours if you want it.` };
    },
  }),
  A({
    id: 'option_material',
    category: 'Get work',
    label: 'Option material yourself',
    blurb: 'Buy the rights to something nobody is making. Develop a part that does not exist yet.',
    cost: (g) => `$${optionPrice(g).toFixed(2)}M`,
    available: (g) => g.money.net > optionPrice(g),
    salience: (g) => (g.development.length === 0 && g.money.net > 4 ? 0.6 : 0.35),
    run: (g, c, rng) => {
      const price = optionPrice(g);
      g.money.net -= price;
      const script = g.world.generateScript(rng, g.actor);
      g.development.push(script);
      return { text: `You optioned ${script.title} for $${price.toFixed(2)}M. It is yours to get made, or not.` };
    },
  }),
  A({
    id: 'attach_and_shop',
    category: 'Get work',
    label: 'Attach yourself and shop it',
    blurb: 'Take one of your projects out. You are the package now; financing follows you.',
    cost: () => 'A block, and your own money',
    available: (g) => g.development.some((s) => !s.shopped),
    salience: (g) => (g.development.length ? 0.75 : 0),
    run: (g, c, rng) => {
      const script = c.script || g.development.find((s) => !s.shopped);
      script.shopped = true;
      const heatFactor = M.standing(g.actor.standing) / 100;
      const favourFactor = clamp(g.rolodex.totalFavours() / 25, 0, 0.5);
      script.financingChance = clamp(0.12 + 0.55 * heatFactor + favourFactor
        + (script.quality - 58) / 220, 0.05, 0.93);
      g.blocksBooked = Math.min(4, g.blocksBooked + 1);
      return {
        text: `You walked ${script.title} into four offices with yourself attached. `
          + `${(100 * script.financingChance).toFixed(0)}% of the town thinks that is enough.`,
      };
    },
  }),
  A({
    id: 'agency_package',
    category: 'Get work',
    label: 'Ask the agency to package you',
    blurb: 'They rep the writer and the director too. You go in as a bundle, before casting exists.',
    cost: () => '15% of everything, forever',
    available: (g) => g.actor.agent === 'powerhouse' && g.year - (g.lastPackage || -9) >= 4,
    salience: () => 0.55,
    run: (g, c, rng) => {
      g.lastPackage = g.year;
      const role = g.world.generateRole(g.actor, { billing: 'lead' });
      role.path = 'direct';
      role.chance = 1;
      role.packaged = true;
      role.fit = M.fitScore(g.actor, role);
      role.utility = M.utility(g.actor, role, 30);
      g.board.unshift(role);
      return { text: `The agency put you, a writer and a director in one envelope. ${role.title}.` };
    },
  }),
];

// ---------------------------------------------------------------------------
// CHANGE A PROJECT YOU'RE ON
// ---------------------------------------------------------------------------
const CHANGE_PROJECT = [
  A({
    id: 'request_rewrite',
    category: 'On the project',
    label: 'Request a rewrite of your part',
    blurb: 'You know this character better than the writer does. Probably.',
    cost: () => 'Goodwill, and you might be wrong',
    needs: 'currentRole',
    available: (g, c) => !!c.current && !c.current.rewritten,
    salience: (g, c) => (c.current && c.current.fit < 55 ? 0.85 : 0.4),
    run: (g, c, rng) => {
      const r = c.current;
      r.rewritten = true;
      const right = rng.chance(clamp(0.35 + g.actor.attrs.instinct / 180, 0.2, 0.85));
      if (right) {
        r.fitBonus = (r.fitBonus || 0) + 14;
        return { text: 'They took your pages. The part fits you now.' };
      }
      r.scriptQuality = clamp(r.scriptQuality - 7, 5, 98);
      r.director.affinity = clamp(r.director.affinity - 5, -100, 100);
      return { text: 'They took your pages. The part is worse and everyone is being polite about it.' };
    },
  }),
  A({
    id: 'recommend_costar',
    category: 'On the project',
    label: 'Recommend a co-star',
    blurb: 'Someone you trust in the room opposite you changes what the scenes can be.',
    cost: () => '1 favour spent, 2 earned',
    needs: 'currentRole',
    available: (g, c) => !!c.current && g.rolodex.creditors(1).length > 0 && !c.current.recommended,
    salience: (g, c) => (c.current && c.current.costar.ego > 65 ? 0.8 : 0.45),
    run: (g, c) => {
      const r = c.current;
      const e = c.person || g.rolodex.creditors(1)[0];
      if (!e || !g.rolodex.spend(e.person, 'introduction', g.year)) {
        return { text: 'You have nobody to call about it.' };
      }
      r.recommended = true;
      r.chemistryBonus = (r.chemistryBonus || 0) + 16;
      const other = g.world.costars.find((x) => x.id !== r.costar.id) || r.costar;
      g.rolodex.gain(other, 'recommended', g.year);
      return { text: `You got ${other.name} into the film. They know who did that.` };
    },
  }),
  A({
    id: 'block_costar',
    category: 'On the project',
    label: 'Block the co-star',
    blurb: 'You have approval. Use it and make a permanent enemy.',
    cost: () => 'Co-star approval, and one person who will never forget',
    needs: 'currentRole',
    available: (g, c) => !!c.current && g.approvals.has('costar') && !c.current.blocked,
    salience: (g, c) => (c.current && c.current.costar.ego > 78 ? 0.7 : 0.2),
    run: (g, c) => {
      const r = c.current;
      r.blocked = true;
      const victim = r.costar;
      const edge = g.rolodex.edge(victim);
      edge.grudge = clamp(edge.grudge + 45, 0, 100);
      edge.affinity = clamp(edge.affinity - 50, -100, 100);
      r.costar = g.world.costars.find((x) => x.ego < 50 && x.id !== victim.id) || r.costar;
      r.chemistryBonus = (r.chemistryBonus || 0) + 8;
      return { text: `${victim.name} is off the picture and knows exactly why.` };
    },
  }),
  A({
    id: 'push_director',
    category: 'On the project',
    label: 'Push for a different director',
    blurb: 'The single biggest swing available to an actor, and the one that gets you a reputation.',
    cost: () => 'Director approval, or enough standing to be feared',
    needs: 'currentRole',
    available: (g, c) => !!c.current && (g.approvals.has('director') || M.standing(g.actor.standing) > 72)
      && !c.current.directorSwapped,
    salience: (g, c) => (c.current && g.world.directorSkill(c.current.director) < 45 ? 0.9 : 0.25),
    run: (g, c, rng) => {
      const r = c.current;
      r.directorSwapped = true;
      const old = r.director;
      const better = g.world.directors
        .filter((d) => !d.retired && d.id !== old.id)
        .sort((a, b) => g.world.directorSkill(b) - g.world.directorSkill(a))[rng.int(0, 2)];
      const oldEdge = g.rolodex.edge(old);
      oldEdge.grudge = clamp(oldEdge.grudge + 60, 0, 100);
      r.director = better;
      g.actor.standing.notoriety = clamp(g.actor.standing.notoriety + 5, 0, 100);
      return { text: `${old.name} is off it. ${better.name} is on it. The town heard about this within a day.` };
    },
  }),
  A({
    id: 'improvise',
    category: 'On the project',
    label: 'Improvise against the script',
    blurb: 'Go off the page and see what happens. High variance; this is what Instinct is for.',
    cost: () => "The director's patience",
    needs: 'currentRole',
    available: (g, c) => !!c.current && !c.current.improvised,
    salience: (g) => (g.actor.attrs.instinct > 65 ? 0.7 : 0.3),
    run: (g, c) => {
      c.current.improvised = true;
      return { text: 'You are going to go off the page and find out on the day.' };
    },
  }),
  A({
    id: 'refuse_scene',
    category: 'On the project',
    label: 'Refuse a scene',
    blurb: 'You can always say no. It always costs.',
    cost: () => 'Notoriety +5, and the director remembers',
    needs: 'currentRole',
    available: (g, c) => !!c.current && !c.current.refused,
    salience: () => 0.2,
    run: (g, c) => {
      const r = c.current;
      r.refused = true;
      g.actor.standing.notoriety = clamp(g.actor.standing.notoriety + 5, 0, 100);
      r.director.affinity = clamp(r.director.affinity - 12, -100, 100);
      r.scriptQuality = clamp(r.scriptQuality - 3, 5, 98);
      return { text: 'You will not be doing that scene. They shot around you, coldly.' };
    },
  }),
];

// ---------------------------------------------------------------------------
// CHANGE YOUR OWN STANDING
// ---------------------------------------------------------------------------
const CHANGE_STANDING = [
  A({
    id: 'disappear',
    category: 'Your standing',
    label: 'Disappear',
    blurb: 'Stop. Turn everything down. Let them forget you and then miss you.',
    cost: () => 'Heat, and every fee you would have earned',
    available: (g) => !g.hiatus,
    salience: (g) => (g.legibility > 74 && g.actor.standing.heat > 45 ? 0.8 : 0.3),
    run: (g) => {
      g.hiatus = true;
      return { text: 'You are not working. You are not saying why. It starts now.' };
    },
  }),
  A({
    id: 'end_disappear',
    category: 'Your standing',
    label: 'Come back',
    blurb: 'Return, with whatever scarcity you have accumulated.',
    cost: () => 'Nothing. That was the point.',
    available: (g) => !!g.hiatus,
    salience: (g) => (g.scarcity > 22 ? 0.95 : 0.5),
    run: (g, c, rng) => {
      g.hiatus = false;
      // Somebody serious has been waiting for you to be available. The auteur
      // board is the one that opens for an absence; the tentpole board is not.
      if (g.scarcity > 24) {
        const auteur = g.world.directors
          .filter((d) => !d.retired)
          .sort((x, y) => y.prestige - x.prestige)[rng.int(0, 2)];
        const role = g.world.generateRole(g.actor, { billing: 'lead' });
        role.director = auteur;
        role.gatekeeper = 'auteur';
        role.type = 'indie';
        role.blocks = 1;
        role.scriptQuality = clamp(role.scriptQuality + 18, 5, 98);
        role.path = 'direct';
        role.chance = 1;
        role.difficulty = 0;
        role.comeback = true;
        role.fit = M.fitScore(g.actor, role);
        role.utility = 100;
        g.board.unshift(role);
        return {
          text: `You are back. ${auteur.name}, who has never worked with you, sent ${role.title} `
            + `the same week. Scarcity ${g.scarcity.toFixed(0)}.`,
        };
      }
      return { text: `You are back, and the board knows it. Scarcity ${g.scarcity.toFixed(0)}.` };
    },
  }),
  A({
    id: 'theatre_season',
    category: 'Your standing',
    label: 'Do a season of theatre',
    blurb: 'Eight shows a week for no money in front of nine hundred people a night.',
    cost: () => '2 blocks, no money',
    available: (g) => g.blocksBooked <= 2,
    salience: (g) => (g.actor.standing.prestige < 45 ? 0.7 : 0.4),
    run: (g) => {
      g.blocksBooked = Math.min(4, g.blocksBooked + 2);
      g.actor.attrs.craft = clamp(g.actor.attrs.craft + 3.5, 5, 99);
      g.actor.standing.prestige = clamp(g.actor.standing.prestige + 9, 0, 100);
      g.actor.standing.heat = clamp(g.actor.standing.heat - 4, 0, 100);
      g.markWorked('theatre');
      return { text: 'Twelve weeks of it. You are better than you were, and poorer.' };
    },
  }),
  A({
    id: 'fund_indie',
    category: 'Your standing',
    label: 'Fund an indie out of your own pocket',
    blurb: 'The paycheque film paid for this one. The most common real strategy there is.',
    cost: (g) => `$${Math.max(1, g.money.net * 0.25).toFixed(1)}M`,
    available: (g) => g.money.net > 3,
    salience: (g) => (g.money.net > 20 && g.actor.standing.prestige < 60 ? 0.65 : 0.3),
    run: (g, c, rng) => {
      const spend = Math.max(1, g.money.net * 0.25);
      g.money.net -= spend;
      const script = g.world.generateScript(rng, g.actor, { quality: 66 });
      script.selfFunded = spend;
      script.financingChance = 1;
      script.shopped = true;
      g.development.push(script);
      return { text: `You are paying for ${script.title} yourself. Nobody can take it away from you now.` };
    },
  }),
  A({
    id: 'turn_down_publicly',
    category: 'Your standing',
    label: 'Turn something famous down, publicly',
    blurb: 'Say no to the franchise and say why. It burns the studio and it plays beautifully.',
    cost: () => 'That studio, for years',
    available: (g, c) => !!c.role && c.role.type === 'tentpole',
    salience: (g, c) => (c.role && c.role.type === 'tentpole' && g.actor.standing.prestige > 40 ? 0.6 : 0.15),
    run: (g, c) => {
      const r = c.role;
      g.board = g.board.filter((x) => x.id !== r.id);
      g.actor.standing.affection = clamp(g.actor.standing.affection + 5, 0, 100);
      g.actor.standing.prestige = clamp(g.actor.standing.prestige + 6, 0, 100);
      g.burnedStudios = (g.burnedStudios || 0) + 1;
      return { text: `You told a magazine why you were not doing ${r.title}. It reads very well.` };
    },
  }),
  A({
    id: 'start_feud',
    category: 'Your standing',
    label: 'Start a feud',
    blurb: 'Pick someone your size. Visibility for two, and sometimes both careers benefit.',
    cost: () => 'Notoriety, both ways',
    available: (g) => g.rolodex.tracked().some((e) => e.person.kind === 'costar'),
    salience: (g) => (g.actor.standing.heat < 20 ? 0.6 : 0.2),
    run: (g, c, rng) => {
      const e = c.person || g.rolodex.tracked().find((x) => x.person.kind === 'costar');
      if (!e) return { text: 'Nobody worth fighting.' };
      e.grudge = clamp(e.grudge + 55, 0, 100);
      g.actor.standing.notoriety = clamp(g.actor.standing.notoriety + 14, 0, 100);
      g.actor.standing.heat = clamp(g.actor.standing.heat + 8, 0, 100);
      e.person.heat = clamp(e.person.heat + 8, 0, 100);
      return { text: `You and ${e.person.name} are in the papers for something that is not a film.` };
    },
  }),
  A({
    id: 'court_critic',
    category: 'Your standing',
    label: 'Court a critic',
    blurb: 'Lunches, access, years. Eventually one person\'s noise term leans your way.',
    cost: () => 'Years, and a certain amount of self-respect',
    available: (g) => g.courtedCritics < 2,
    salience: (g) => (g.actor.standing.prestige > 30 ? 0.45 : 0.2),
    run: (g) => {
      g.courtedCritics += 1;
      g.criticSkew += 2.6;
      return { text: 'You have a critic now. Nobody says it out loud, least of all the critic.' };
    },
  }),
  A({
    id: 'memoir',
    category: 'Your standing',
    label: 'Write a memoir',
    blurb: 'Money, affection, and one person you can burn on the record.',
    cost: () => 'A block',
    available: (g) => g.actor.age > 44 && !g.wroteMemoir,
    salience: (g) => (g.actor.age > 58 ? 0.7 : 0.3),
    run: (g, c) => {
      g.wroteMemoir = true;
      g.blocksBooked = Math.min(4, g.blocksBooked + 1);
      const take = clamp(0.4 + M.standing(g.actor.standing) / 28, 0.4, 6);
      g.money.net += take;
      g.money.lifetime += take;
      g.actor.standing.affection = clamp(g.actor.standing.affection + 7, 0, 100);
      const victim = c.person || g.rolodex.tracked().find((e) => e.grudge > 20);
      if (victim) {
        victim.grudge = clamp(victim.grudge + 30, 0, 100);
        g.actor.standing.notoriety = clamp(g.actor.standing.notoriety + 6, 0, 100);
        return { text: `The book did $${take.toFixed(1)}M and chapter nine is about ${victim.person.name}.` };
      }
      return { text: `The book did $${take.toFixed(1)}M and it is kinder than it needed to be.` };
    },
  }),
  A({
    id: 'reinvent',
    category: 'Your standing',
    label: 'Change your name and reinvent',
    blurb: 'Everything you built, traded for the ability to be read as something else.',
    cost: () => 'Heat, recognition, and your Persona',
    available: (g) => g.legibility > 62,
    salience: (g) => (g.legibility > 80 && g.actor.standing.heat < 25 ? 0.75 : 0.1),
    run: (g) => {
      const old = g.actor.name;
      g.actor.name = g.world.name();
      for (const k of Object.keys(g.actor.persona.genre)) g.actor.persona.genre[k] *= 0.35;
      for (const k of Object.keys(g.actor.persona.archetype)) g.actor.persona.archetype[k] *= 0.35;
      g.actor.standing.heat *= 0.55;
      g.actor.recognition *= 0.5;
      g.actor.standing.notoriety *= 0.4;
      return { text: `${old} does not work any more. ${g.actor.name} is available immediately.` };
    },
  }),
];

// ---------------------------------------------------------------------------
// CHANGE OTHER PEOPLE
// ---------------------------------------------------------------------------
const CHANGE_PEOPLE = [
  A({
    id: 'mentor',
    category: 'Other people',
    label: 'Mentor a newcomer',
    blurb: 'A block a year for someone with nothing. In twenty years they may be the most powerful person you know.',
    cost: () => 'A block a year, for as long as you keep it up',
    available: (g) => g.mentees.length < 4,
    salience: (g) => (g.actor.age > 38 ? 0.6 : 0.25),
    run: (g, c, rng) => {
      const person = g.world.makeNewcomer(rng);
      g.mentees.push({ person, since: g.year, power: 0 });
      g.rolodex.gain(person, 'hiredThem', g.year);
      g.blocksBooked = Math.min(4, g.blocksBooked + 1);
      return { text: `You are teaching ${person.name} what took you fifteen years. They are twenty-two.` };
    },
  }),
  A({
    id: 'defend_scandal',
    category: 'Other people',
    label: 'Publicly defend someone in a scandal',
    blurb: 'Say it out loud when nobody else will. It costs you and it buys a loyalty that outlives careers.',
    cost: () => 'Notoriety +10',
    available: (g) => g.world.scandals.length > 0,
    salience: (g) => (g.world.scandals.length ? 0.75 : 0),
    run: (g, c) => {
      const s = c.scandal || g.world.scandals[0];
      g.actor.standing.notoriety = clamp(g.actor.standing.notoriety + 10, 0, 100);
      g.rolodex.gain(s.person, 'defended', g.year);
      s.defendedBy = g.actor.name;
      return { text: `You stood up for ${s.person.name}. Half the town thinks less of you and ${s.person.name} will never forget it.` };
    },
  }),
  A({
    id: 'broker_reconciliation',
    category: 'Other people',
    label: 'Broker a reconciliation',
    blurb: 'Get two people who hate each other into one room. The best trade in the game, if you can spot it.',
    cost: () => '2 favours',
    available: (g) => g.rolodex.creditors(1).length >= 2,
    salience: (g) => (g.rolodex.creditors(1).length >= 2 ? 0.55 : 0),
    run: (g, c) => {
      const [a, b] = g.rolodex.creditors(1).slice(0, 2);
      if (!a || !b) return { text: 'Not enough goodwill to spend.' };
      a.favours = Math.max(0, a.favours - 1);
      b.favours = Math.max(0, b.favours - 1);
      a.favours += 3; b.favours += 3;
      a.affinity = clamp(a.affinity + 12, -100, 100);
      b.affinity = clamp(b.affinity + 12, -100, 100);
      return { text: `${a.person.name} and ${b.person.name} are speaking again, because of you, and they both know it.` };
    },
  }),
  A({
    id: 'recommend_someone',
    category: 'Other people',
    label: 'Recommend someone for a job',
    blurb: 'Spend your credibility on somebody else. It comes back, or it does not.',
    cost: () => 'Your credibility if they are bad',
    available: (g) => g.rolodex.tracked().length > 0,
    salience: () => 0.4,
    run: (g, c, rng) => {
      const e = c.person || g.rolodex.tracked()[rng.int(0, Math.min(3, g.rolodex.tracked().length - 1))];
      const good = rng.chance(clamp(0.45 + e.affinity / 200, 0.2, 0.9));
      if (good) {
        g.rolodex.gain(e.person, 'recommended', g.year);
        return { text: `${e.person.name} got the job and was good in it. That is two you are owed.` };
      }
      g.actor.standing.prestige = clamp(g.actor.standing.prestige - 2, 0, 100);
      return { text: `${e.person.name} got the job and was not good in it. People noticed who suggested them.` };
    },
  }),
  A({
    id: 'leak',
    category: 'Other people',
    label: 'Leak something',
    blurb: 'Effective, deniable, and information spends only once.',
    cost: () => 'One piece of information',
    available: (g) => g.information.length > 0,
    salience: (g) => (g.information.length ? 0.5 : 0),
    run: (g, c) => {
      const info = g.information.shift();
      const edge = g.rolodex.edge(info.about);
      edge.grudge = clamp(edge.grudge + 25, 0, 100);
      info.about.prestige = clamp((info.about.prestige ?? 50) - 14, 0, 100);
      return { text: `It ran on a Tuesday with no byline. ${info.about.name} has had a bad week.` };
    },
  }),
];

// ---------------------------------------------------------------------------
// CHANGE THE MARKET, AND THE RULES
// ---------------------------------------------------------------------------
const CHANGE_MARKET = [
  A({
    id: 'awards_campaign',
    category: 'The market',
    label: 'Fund your own awards campaign',
    blurb: 'Luncheons instead of work for a quarter. It is not corruption, it is a category.',
    cost: (g) => `$${campaignCost(g).toFixed(1)}M and a block`,
    available: (g) => g.awards.thisSeason.length > 0 && g.money.net > campaignCost(g) && !g.campaignedThisYear,
    salience: (g) => (g.awards.thisSeason.some((e) => e.rec.notices > 68) ? 0.9 : 0.3),
    run: (g) => {
      const cost = campaignCost(g);
      g.money.net -= cost;
      g.campaignSpend += cost;
      g.campaignedThisYear = true;
      g.blocksBooked = Math.min(4, g.blocksBooked + 1);
      return { text: `$${cost.toFixed(1)}M of your own money, and a quarter of lunches.` };
    },
  }),
  A({
    id: 'category_fraud',
    category: 'The market',
    label: 'Campaign a lead in supporting',
    blurb: 'A weaker field. The trades may call it out, and calling it out is also a story.',
    cost: () => 'Notoriety +6 if the press bites',
    available: (g) => g.awards.thisSeason.some((e) => e.role.billing === 'lead') && !g.categoryFraud,
    salience: () => 0.5,
    run: (g) => {
      g.categoryFraud = true;
      return { text: 'Your lead performance is, it turns out, a supporting performance.' };
    },
  }),
  A({
    id: 'festival_premiere',
    category: 'The market',
    label: 'Push for a festival premiere',
    blurb: 'Trade the opening weekend for a room of critics in October.',
    cost: () => "The film's commercial best case",
    available: (g) => g.pending.some((p) => !p.festival),
    salience: (g) => (g.pending.some((p) => p.role.type === 'indie') ? 0.7 : 0.25),
    run: (g, c) => {
      const p = c.project || g.pending.find((x) => !x.festival);
      if (!p) return { text: 'Nothing in the can to premiere.' };
      p.festival = true;
      return { text: `${p.role.title} goes to a festival first. Everything now depends on one screening.` };
    },
  }),
  A({
    id: 'holdout',
    category: 'The market',
    label: 'Hold out on the franchise',
    blurb: 'They cannot recast you and you both know it. Ask for what you are worth.',
    cost: () => 'They may call the bluff and write you out',
    available: (g) => !!g.franchise && g.franchise.identification > 45 && !g.franchise.heldOut,
    salience: (g) => (g.franchise && g.franchise.identification > 60 ? 0.95 : 0.4),
    run: (g, c, rng) => {
      const f = g.franchise;
      f.heldOut = true;
      const win = rng.chance(clamp(f.identification / 105, 0.15, 0.9));
      if (win) {
        f.grossPoints = (f.grossPoints || 0) + 0.06;
        g.approvals.add('costar');
        g.approvals.add('script');
        return { text: `They paid. Gross points, script approval, and a producer who now hates you.` };
      }
      f.writtenOut = true;
      g.actor.standing.notoriety = clamp(g.actor.standing.notoriety + 8, 0, 100);
      return { text: `They called it. Your character dies off-screen between installments.` };
    },
  }),
  A({
    id: 'buy_back_ip',
    category: 'The market',
    label: 'Buy back your own IP',
    blurb: 'Own the thing you are famous for.',
    cost: (g) => `$${ipPrice(g).toFixed(0)}M`,
    available: (g) => !!g.franchise && g.money.net > ipPrice(g) && !g.franchise.owned,
    salience: (g) => (g.franchise && g.money.net > 2 * ipPrice(g) ? 0.6 : 0.15),
    run: (g) => {
      const price = ipPrice(g);
      g.money.net -= price;
      g.franchise.owned = true;
      return { text: `You own ${g.franchise.title} now. All of it.` };
    },
  }),
];

const CHANGE_RULES = [
  A({
    id: 'guild_officer',
    category: 'The rules',
    label: 'Stand for guild office',
    blurb: 'Set residual policy. Call a strike, or settle one. You are on the other side of it now.',
    cost: () => 'Standing among peers, and a fraction of every year',
    available: (g) => !g.positions.has('guild') && g.credits.length > 8,
    salience: (g) => (g.actor.standing.affection > 40 ? 0.5 : 0.25),
    run: (g, c, rng) => {
      const won = rng.chance(clamp(0.25 + g.actor.standing.affection / 160 + g.rolodex.totalFavours() / 60, 0.1, 0.9));
      if (!won) return { text: 'You stood. You lost. The person who won thanked you graciously.' };
      g.positions.add('guild');
      return { text: 'You are on the board of the guild. People email you about pension arithmetic now.' };
    },
  }),
  A({
    id: 'festival_juror',
    category: 'The rules',
    label: 'Sit on a festival jury',
    blurb: 'You decide who wins. Every filmmaker in competition now has a relationship with you.',
    cost: () => 'Prestige 55 and an invitation',
    available: (g) => g.actor.standing.prestige > 55 && !g.positions.has('juror'),
    salience: (g) => (g.actor.standing.prestige > 65 ? 0.6 : 0.3),
    run: (g, c, rng) => {
      g.positions.add('juror');
      const friends = g.world.directors.filter((d) => !d.retired).slice(0, 4);
      for (const d of friends) g.rolodex.edge(d).affinity = clamp(g.rolodex.edge(d).affinity + 14, -100, 100);
      g.information.push({ about: g.world.directors[rng.int(0, g.world.directors.length - 1)], kind: 'jury room' });
      return { text: 'Eight days of films and one very long argument. Four directors now owe you their year.' };
    },
  }),
  A({
    id: 'production_company',
    category: 'The rules',
    label: 'Start a production company',
    blurb: 'Develop anything, for anyone, including yourself.',
    cost: () => 'Prestige 45 and running costs',
    available: (g) => g.actor.standing.prestige > 45 && !g.positions.has('prodco'),
    salience: (g) => (g.development.length ? 0.75 : 0.5),
    run: (g) => {
      g.positions.add('prodco');
      return { text: 'Two rooms, an assistant, and a shingle with your name on it. You can develop now.' };
    },
  }),
  A({
    id: 'teach',
    category: 'The rules',
    label: 'Teach',
    blurb: 'Your students become the next generation. In fifteen years your Rolodex is the industry.',
    cost: () => 'A block a year, forever, for very little money',
    available: (g) => g.actor.age > 48 && !g.positions.has('teacher'),
    salience: (g) => (g.actor.age > 58 && g.board.length < 3 ? 0.7 : 0.3),
    run: (g) => {
      g.positions.add('teacher');
      return { text: 'Tuesdays and Thursdays, a room of twenty-year-olds, most of whom will not make it.' };
    },
  }),
  A({
    id: 'board_seat',
    category: 'The rules',
    label: 'Take a studio board seat',
    blurb: 'Vote on greenlights. Fire an executive. Be the reason a film exists.',
    cost: (g) => `$${boardPrice(g).toFixed(0)}M or a very large favour`,
    available: (g) => !g.positions.has('board') && (g.money.net > boardPrice(g) || g.rolodex.creditors(3).length > 0),
    salience: (g) => (g.money.net > 60 ? 0.55 : 0.2),
    run: (g) => {
      if (g.money.net > boardPrice(g)) g.money.net -= boardPrice(g);
      else {
        const e = g.rolodex.creditors(3)[0];
        g.rolodex.spend(e.person, 'attach', g.year);
      }
      g.positions.add('board');
      return { text: 'Four meetings a year and a vote on what gets made. It is duller and more powerful than it sounds.' };
    },
  }),
];

export const ACTIONS = [
  ...GET_WORK, ...CHANGE_PROJECT, ...CHANGE_STANDING,
  ...CHANGE_PEOPLE, ...CHANGE_MARKET, ...CHANGE_RULES,
];

export const ACTIONS_BY_ID = Object.fromEntries(ACTIONS.map((a) => [a.id, a]));

// The interface asks for this and shows the top few. Nothing is hidden — the
// ranking exists so that a fifty-year-old with thirty available verbs sees the
// same size list as a twenty-four-year-old with six (§0.3 rule 3).
export function availableActions(game, ctx = {}) {
  return ACTIONS
    .filter((a) => {
      try { return a.available(game, ctx); } catch { return false; }
    })
    .map((a) => ({ action: a, salience: a.salience(game, ctx) }))
    .sort((x, y) => y.salience - x.salience);
}

export function perform(game, actionId, ctx = {}) {
  const a = ACTIONS_BY_ID[actionId];
  if (!a) return { text: 'No such move.' };
  if (!a.available(game, ctx)) return { text: 'Not available to you right now.' };
  const result = a.run(game, ctx, game.rng);
  game.say(result.text, 'lever');
  game.leverageUsed += 1;
  return result;
}

const optionPrice = (g) => clamp(0.05 + g.money.net * 0.06, 0.05, 3.5);
const campaignCost = (g) => clamp(0.4 + M.standing(g.actor.standing) / 22, 0.4, 3);
const ipPrice = (g) => clamp(18 + (g.franchise?.identification || 0) * 0.9, 18, 120);
const boardPrice = () => 45;

export { GENRES };
