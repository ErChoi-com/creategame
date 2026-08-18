'use strict';

/*
 * Career Sim — The Independent Auteur
 *
 * Jonah Ricci: former teen star turned actor/director whose defining trait is a
 * high SELF-FINANCE TENDENCY — he'd rather bankroll his own passion projects than
 * cede creative control to a studio. That tendency isn't just flavor: it biases
 * which action is "recommended" each year and boosts the payoff/risk math whenever
 * he actually chooses to self-finance a directorial project (the "Auteur Bonus").
 */

const RETIREMENT_AGE = 65;
const START_AGE = 34;

function clamp(v, lo = 0, hi = 100) {
  return Math.max(lo, Math.min(hi, v));
}

function rand(min, max) {
  return Math.random() * (max - min) + min;
}

function weightedPick(items) {
  const total = items.reduce((s, i) => s + i.weight, 0);
  let r = Math.random() * total;
  for (const it of items) {
    r -= it.weight;
    if (r <= 0) return it;
  }
  return items[items.length - 1];
}

function fmtMoney(n) {
  const sign = n < 0 ? '-' : '';
  n = Math.abs(n);
  if (n >= 1_000_000) return `${sign}$${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${sign}$${(n / 1_000).toFixed(0)}K`;
  return `${sign}$${n.toFixed(0)}`;
}

function freshCharacter() {
  return {
    name: 'Jonah Ricci',
    archetype: 'The Independent Auteur',
    age: START_AGE,
    year: 1,
    retired: false,
    bankrupt: false,
    stats: {
      acting: 78,
      directing: 70,
      charisma: 74,
      business: 62,
      networking: 65,
      stamina: 78,
    },
    reputation: 58,
    legacy: 0,
    wealth: 2_400_000,
    selfFinanceTendency: 80,
    filmography: [],
    log: [],
  };
}

let state = freshCharacter();

// ---------- rendering ----------

function render() {
  renderHeadline();
  renderStats();
  renderFilmography();
  renderLog();
  if (state.retired || state.bankrupt) {
    renderEnding();
  } else {
    document.getElementById('game-over-panel').style.display = 'none';
    document.getElementById('actions-panel').style.display = '';
    renderActions();
  }
}

function renderHeadline() {
  const el = document.getElementById('headline');
  el.innerHTML = '';
  const items = [
    ['Age', state.age],
    ['Year', state.year],
    ['Wealth', fmtMoney(state.wealth)],
    ['Reputation', Math.round(state.reputation)],
    ['Legacy', Math.round(state.legacy)],
  ];
  for (const [label, value] of items) {
    const div = document.createElement('div');
    div.innerHTML = `<div class="label">${label}</div><div class="value">${value}</div>`;
    el.appendChild(div);
  }
}

function renderStats() {
  const el = document.getElementById('stats');
  el.innerHTML = '';
  const labels = {
    acting: 'Acting',
    directing: 'Directing',
    charisma: 'Charisma',
    business: 'Business',
    networking: 'Network',
    stamina: 'Stamina',
  };
  for (const key of Object.keys(labels)) {
    const val = Math.round(state.stats[key]);
    const row = document.createElement('div');
    row.className = 'stat-row';
    row.innerHTML = `
      <span class="stat-label">${labels[key]}</span>
      <span class="bar-track"><span class="bar-fill" style="width:${clamp(val)}%"></span></span>
      <span class="stat-val">${val}</span>
    `;
    el.appendChild(row);
  }
  document.getElementById('trait-note').textContent =
    `Self-finance tendency: ${state.selfFinanceTendency}/100 — Jonah trusts his own money ` +
    `over a studio's notes. Self-financed projects carry an Auteur Bonus to reputation and ` +
    `legacy, at the cost of real financial risk.`;
}

function renderFilmography() {
  const el = document.getElementById('filmography');
  if (state.filmography.length === 0) {
    el.innerHTML = '<div class="film" style="color:var(--dim)">No credits yet.</div>';
    return;
  }
  el.innerHTML = '';
  for (const f of [...state.filmography].reverse()) {
    const div = document.createElement('div');
    div.className = 'film';
    div.innerHTML = `<b>${f.title}</b> (Y${f.year}) — ${f.role}, ${f.outcome}`;
    el.appendChild(div);
  }
}

function renderLog() {
  const el = document.getElementById('log');
  el.innerHTML = '';
  for (const entry of state.log) {
    const div = document.createElement('div');
    div.className = `entry ${entry.tone || ''}`;
    div.innerHTML = `<span class="year-tag">Y${entry.year}</span>${entry.text}`;
    el.appendChild(div);
  }
}

function logEvent(text, tone = '') {
  state.log.push({ year: state.year, text, tone });
}

// ---------- actions ----------

function selfFinanceBudget() {
  // Budget is driven by skill (business/directing), not a percentage of current wealth —
  // otherwise a win just inflates the next budget and compounds into absurd numbers.
  // Wealth only ever acts as a ceiling: he can't stake more than he actually has.
  const skillBudget = 300_000 + state.stats.business * 7_000 + state.stats.directing * 5_000;
  const wealthCeiling = Math.max(100_000, state.wealth * 0.4);
  return Math.round(Math.min(skillBudget, wealthCeiling));
}

const ACTIONS = [
  {
    id: 'blockbuster',
    title: 'Act — Studio Blockbuster',
    desc: 'Big paycheck, wide exposure, little creative control.',
    available: () => true,
    cost: { stamina: 20 },
    run: () => {
      const pay = Math.round(2_000_000 + state.stats.charisma * 40_000 + rand(-300000, 800000));
      const repChange = rand(0, 3);
      state.wealth += pay;
      state.reputation = clamp(state.reputation + repChange);
      state.stats.acting = clamp(state.stats.acting + rand(0.5, 1.5));
      state.filmography.push({ title: randomTitle('blockbuster'), year: state.year, role: 'Lead actor (studio)', outcome: 'solid box office' });
      logEvent(`Starred in a studio blockbuster, earning ${fmtMoney(pay)}.`, 'good');
    },
  },
  {
    id: 'indie',
    title: 'Act — Prestige Indie',
    desc: 'Modest pay, real award buzz, sharpens the craft.',
    available: () => true,
    cost: { stamina: 15 },
    run: () => {
      const pay = Math.round(150_000 + state.stats.acting * 4_000 + rand(-50000, 150000));
      state.wealth += pay;
      const awardChance = clamp(state.stats.acting + state.reputation) / 200;
      let repChange = rand(2, 5);
      let outcome = 'quiet festival run';
      if (Math.random() < awardChance) {
        repChange += rand(6, 12);
        state.legacy += rand(4, 8);
        outcome = 'award nomination';
        logEvent('Prestige indie performance picked up an award nomination.', 'good');
      } else {
        logEvent(`Acted in a small prestige drama for ${fmtMoney(pay)}.`);
      }
      state.reputation = clamp(state.reputation + repChange);
      state.stats.acting = clamp(state.stats.acting + rand(1, 2.5));
      state.stats.networking = clamp(state.stats.networking + rand(0.5, 1.5));
      state.filmography.push({ title: randomTitle('indie'), year: state.year, role: 'Lead actor (indie)', outcome });
    },
  },
  {
    id: 'self_direct',
    title: 'Direct — Self-Financed Passion Project',
    desc: 'Bankroll it himself. Full control, real risk, the Auteur Bonus applies.',
    available: () => state.wealth > 200_000,
    cost: { stamina: 28 },
    recommended: true,
    run: () => {
      const budget = selfFinanceBudget();
      state.wealth -= budget;
      const skill = (state.stats.directing * 1.3 + state.stats.charisma * 0.5 + state.reputation * 0.6) / 2.4;
      const auteurBonus = state.selfFinanceTendency / 100; // 0..1
      const successChance = clamp((skill + auteurBonus * 25) / 100, 0.15, 0.92);
      if (Math.random() < successChance) {
        const multiplier = rand(1.4, 3.2) + auteurBonus * 0.8;
        const ret = Math.round(budget * multiplier);
        state.wealth += ret;
        const repGain = rand(6, 14) + auteurBonus * 8;
        const legacyGain = rand(8, 18) + auteurBonus * 10;
        state.reputation = clamp(state.reputation + repGain);
        state.legacy += legacyGain;
        state.stats.directing = clamp(state.stats.directing + rand(2, 4));
        state.filmography.push({ title: randomTitle('auteur'), year: state.year, role: 'Writer/Director (self-financed)', outcome: 'critical triumph' });
        logEvent(`Self-financed film (budget ${fmtMoney(budget)}) was a critical triumph — grossed/sold for ${fmtMoney(ret)}.`, 'good');
      } else {
        const lossFrac = rand(0.6, 1.0);
        const salvage = Math.round(budget * (1 - lossFrac));
        state.wealth += salvage;
        const repChange = rand(-4, 2);
        state.reputation = clamp(state.reputation + repChange);
        state.legacy += rand(1, 4); // artistic integrity still counts for something
        state.stats.directing = clamp(state.stats.directing + rand(1, 2));
        state.filmography.push({ title: randomTitle('auteur'), year: state.year, role: 'Writer/Director (self-financed)', outcome: 'box-office disappointment' });
        logEvent(`Self-financed film (budget ${fmtMoney(budget)}) flopped commercially, though he kept full creative control. Lost ${fmtMoney(budget - salvage)}.`, 'bad');
      }
    },
  },
  {
    id: 'studio_direct',
    title: 'Direct — Studio-Financed Film',
    desc: 'No wealth risk, upfront fee, but the studio has notes.',
    available: () => state.stats.directing >= 40,
    cost: { stamina: 26 },
    run: () => {
      const fee = Math.round(400_000 + state.stats.directing * 8_000 + rand(-50000, 200000));
      state.wealth += fee;
      const interference = Math.random() < 0.35;
      let repChange = rand(1, 4);
      let outcome = 'released to mixed reviews';
      if (interference) {
        repChange -= rand(1, 5);
        outcome = 'reshot into something he barely recognized';
        logEvent(`Studio interfered heavily with his film; it was ${outcome}.`, 'bad');
      } else {
        logEvent(`Directed a studio film for a ${fmtMoney(fee)} fee, ${outcome}.`);
      }
      state.reputation = clamp(state.reputation + repChange);
      state.stats.directing = clamp(state.stats.directing + rand(1, 2));
      state.filmography.push({ title: randomTitle('studio'), year: state.year, role: 'Director (studio)', outcome });
    },
  },
  {
    id: 'business',
    title: 'Take Development Meetings',
    desc: 'Build the business & network so future self-financed budgets go further.',
    available: () => true,
    cost: { stamina: 12 },
    run: () => {
      state.stats.business = clamp(state.stats.business + rand(3, 6));
      state.stats.networking = clamp(state.stats.networking + rand(3, 6));
      const windfall = Math.random() < 0.3;
      if (windfall) {
        const amt = Math.round(rand(80_000, 300_000));
        state.wealth += amt;
        logEvent(`A development deal paid off unexpectedly: +${fmtMoney(amt)}.`, 'good');
      } else {
        logEvent('Spent the year in meetings, sharpening the business side of the operation.');
      }
    },
  },
  {
    id: 'rest',
    title: 'Rest & Train',
    desc: 'Recover stamina and drill a craft with a coach.',
    available: () => true,
    cost: { stamina: -35 },
    run: () => {
      const trainable = ['acting', 'directing', 'charisma'];
      const pick = trainable[Math.floor(Math.random() * trainable.length)];
      state.stats[pick] = clamp(state.stats[pick] + rand(2, 4));
      logEvent(`Took the year slower, resting up and training ${pick}.`);
    },
  },
];

function randomTitle(kind) {
  const banks = {
    blockbuster: ['Skyline Protocol', 'Iron Meridian', 'Last Contract', 'Zero Hour City'],
    indie: ['Quiet Static', 'Paper Anniversary', 'The Long Exhale', 'Low Tide'],
    auteur: ['A Room With No Exit', 'Sundown Ledger', 'The Cost of Light', 'Everything I Owed You'],
    studio: ['Redline Division', 'Glass Horizon', 'The Ninth Floor', 'Crown & Static'],
  };
  const list = banks[kind];
  return list[Math.floor(Math.random() * list.length)];
}

function renderActions() {
  const el = document.getElementById('actions');
  el.innerHTML = '';
  for (const action of ACTIONS) {
    const avail = action.available() && state.stats.stamina >= (action.cost.stamina > 0 ? action.cost.stamina : 0);
    const btn = document.createElement('button');
    btn.className = 'action' + (action.recommended && state.selfFinanceTendency >= 65 ? ' recommended' : '');
    btn.disabled = !avail;
    btn.innerHTML = `<span class="title">${action.title}</span><span class="desc">${action.desc}</span>`;
    btn.addEventListener('click', () => takeAction(action));
    el.appendChild(btn);
  }
}

function takeAction(action) {
  if (state.retired || state.bankrupt) return;
  action.run();
  state.stats.stamina = clamp(state.stats.stamina - action.cost.stamina);
  advanceYear();
}

function advanceYear() {
  randomYearlyEvent();
  state.age += 1;
  state.year += 1;
  state.stats.stamina = clamp(state.stats.stamina + rand(4, 8)); // natural recovery

  if (state.wealth < -100_000) {
    state.bankrupt = true;
    logEvent('The books finally caught up with him — forced into bankruptcy.', 'bad');
  } else if (state.age >= RETIREMENT_AGE) {
    state.retired = true;
    logEvent('Called it a career and stepped back from the spotlight.', 'good');
  }
  render();
}

const YEARLY_EVENTS = [
  {
    weight: 5,
    apply: () => {
      const amt = Math.round(rand(20_000, 120_000));
      state.wealth -= amt;
      logEvent(`Overhead and taxes on top of a working actor's life: -${fmtMoney(amt)}.`, 'bad');
    },
  },
  {
    weight: 3,
    apply: () => {
      state.stats.stamina = clamp(state.stats.stamina - rand(10, 20));
      logEvent('A rough shoot schedule left him running on fumes.', 'bad');
    },
  },
  {
    weight: 2,
    apply: () => {
      state.reputation = clamp(state.reputation + rand(3, 8));
      logEvent('A retrospective piece in the trade press praised his self-financed streak.', 'good');
    },
  },
  {
    weight: 2,
    apply: () => {
      const dip = rand(4, 10);
      state.reputation = clamp(state.reputation - dip);
      logEvent('Tabloids ran an unflattering story; reputation took a hit.', 'bad');
    },
  },
  {
    weight: 1,
    apply: () => {
      state.stats.networking = clamp(state.stats.networking + rand(5, 10));
      state.reputation = clamp(state.reputation + rand(2, 5));
      logEvent('A veteran filmmaker took him under their wing at a festival.', 'good');
    },
  },
  {
    weight: 5,
    apply: () => {
      // quiet year, nothing notable
    },
  },
];

function randomYearlyEvent() {
  const chosen = weightedPick(YEARLY_EVENTS);
  chosen.apply();
}

// ---------- ending ----------

function renderEnding() {
  document.getElementById('actions-panel').style.display = 'none';
  const panel = document.getElementById('game-over-panel');
  panel.style.display = '';

  let title, body;
  if (state.bankrupt) {
    title = 'Financial Collapse';
    body = `Jonah's faith in his own money outran his own money. He leaves the business with a body of ` +
      `uncompromised, self-financed work — and no financial cushion left. Final reputation ${Math.round(state.reputation)}, ` +
      `legacy score ${Math.round(state.legacy)}.`;
  } else {
    const legacyScore = Math.round(state.legacy + state.reputation * 0.5);
    let rank = 'Working Journeyman';
    if (legacyScore > 220) rank = 'Auteur Legend';
    else if (legacyScore > 150) rank = 'Celebrated Independent Filmmaker';
    else if (legacyScore > 90) rank = 'Respected Cult Favorite';
    else if (legacyScore > 40) rank = 'Steady Hand for Hire';
    title = `Retired: ${rank}`;
    body = `After ${state.year - 1} years in the business, Jonah retires at ${state.age} with ${fmtMoney(state.wealth)} ` +
      `in the bank, a reputation of ${Math.round(state.reputation)}/100, and a legacy score of ${legacyScore}. ` +
      `${state.filmography.length} credits to his name, built largely on his own terms.`;
  }
  document.getElementById('ending-title').textContent = title;
  document.getElementById('ending-body').textContent = body;
}

document.getElementById('restart-btn').addEventListener('click', () => {
  state = freshCharacter();
  render();
});

render();
