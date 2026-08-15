// CALLBACK — the front end. All rules live in ../engine; this file only asks
// questions and draws answers.

import { Game, BACKGROUNDS, PREP_OPTIONS, MOMENTS } from '../engine/career.js';
import { DIAL_LABELS, DIALS, PERF_DIALS, POSITIONS, POSITION_COST } from '../engine/data.js';
import * as M from '../engine/model.js';

const stage = document.getElementById('stage');
const hud = document.getElementById('hud');
const ledger = document.getElementById('ledger');

let game = null;
let choice = {};        // in-progress prep/positions/moment selections

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------
const el = (tag, attrs = {}, ...kids) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') n.className = v;
    else if (k === 'html') n.innerHTML = v;
    else if (k.startsWith('on')) n.addEventListener(k.slice(2), v);
    else if (v !== null && v !== false) n.setAttribute(k, v);
  }
  for (const kid of kids.flat()) {
    if (kid == null) continue;
    n.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return n;
};
const clear = () => { stage.replaceChildren(); };
const money = (m) => (Math.abs(m) >= 1 ? `$${m.toFixed(1)}M` : `$${Math.round(m * 1000)}K`);
const quarterName = (q) => ['', 'Q1 — winter', 'Q2 — spring', 'Q3 — summer', 'Q4 — autumn'][q];

function drawHud() {
  if (!game) return;
  hud.hidden = false;
  ledger.hidden = false;
  const a = game.actor;
  document.getElementById('hud-name').textContent = a.name;
  document.getElementById('hud-when').textContent =
    `${a.age} · ${game.year} ${quarterName(game.quarter)} · ${game.blocksBooked}/4 blocks booked`;
  for (const k of ['heat', 'prestige', 'affection', 'notoriety']) {
    document.getElementById(`m-${k}`).style.width = `${a.standing[k]}%`;
    document.getElementById(`v-${k}`).textContent = a.standing[k].toFixed(0);
  }
  document.getElementById('hud-quote').textContent = `quote ${money(a.quote)}`;
  document.getElementById('hud-money').textContent =
    `${money(game.money.net)} banked · ${money(game.money.lifetime)} lifetime`;

  const log = document.getElementById('log');
  log.replaceChildren(...game.log.slice(-14).reverse().map(
    (e) => el('li', { class: e.kind }, `${e.year} · ${e.text}`),
  ));
}

// ---------------------------------------------------------------------------
// 1. character creation — the opening the design document never had
// ---------------------------------------------------------------------------
function screenCreate() {
  clear();
  hud.hidden = true;
  ledger.hidden = true;
  stage.append(
    el('h1', {}, 'Callback'),
    el('p', { class: 'lede' },
      'You are an actor. The work is the game: what you take, how you play it, '
      + 'and what the industry decides that means. Nobody will ever tell you how good you were.'),
    el('h3', { class: 'section' }, 'Where you are starting from'),
  );

  let picked = 'conservatory';
  const cards = el('div', { class: 'grid2' });
  const draw = () => {
    cards.replaceChildren(...Object.entries(BACKGROUNDS).map(([key, bg]) => el(
      'div',
      {
        class: `card pick${picked === key ? ' selected' : ''}`,
        style: picked === key ? 'border-color: var(--accent)' : '',
        onclick: () => { picked = key; draw(); },
      },
      el('h4', {}, bg.label),
      el('div', { class: 'meta' }, `age ${bg.age} · ${bg.unionCredits}/3 union credits · ${
        bg.agent === 'none' ? 'no agent' : bg.agent} · ${money(bg.money)}`),
      el('p', { class: 'why' }, bg.blurb),
      el('div', { class: 'tags' },
        Object.entries(bg.attrs).map(([k, v]) => el('span', { class: 'tag' }, `${k} ${v}`))),
    )));
  };
  draw();
  stage.append(cards);

  const nameInput = el('input', {
    placeholder: 'leave blank for a name from the pool',
    style: 'width:320px;padding:9px;background:var(--panel-2);border:1px solid var(--line);color:var(--ink);border-radius:5px;font:inherit',
  });
  const seedInput = el('input', {
    placeholder: 'seed (optional)',
    style: 'width:150px;padding:9px;margin-left:8px;background:var(--panel-2);border:1px solid var(--line);color:var(--ink);border-radius:5px;font:inherit',
  });
  stage.append(
    el('h3', { class: 'section' }, 'Who you are'),
    el('div', {}, nameInput, seedInput),
    el('div', { style: 'margin-top:20px' }, el('button', {
      class: 'primary',
      onclick: () => {
        const seed = seedInput.value ? Number(seedInput.value) : Math.floor(Math.random() * 1e9);
        game = new Game({ seed, background: picked, name: nameInput.value.trim() || undefined });
        game.say(`${BACKGROUNDS[picked].label}. ${game.year}. Nobody knows your name yet.`);
        screenQuarter();
      },
    }, 'Start working')),
  );
}

// ---------------------------------------------------------------------------
// 2. the quarter — the offer board
// ---------------------------------------------------------------------------
function screenQuarter(fresh = true) {
  if (game.over) return screenObituary();
  drawHud();
  clear();
  const board = fresh ? game.openBoard() : game.board;

  stage.append(
    el('h2', {}, `${game.year} · ${quarterName(game.quarter)}`),
    el('p', { class: 'lede' }, boardMood(board)),
  );

  if (!board.length) {
    stage.append(el('div', { class: 'card' },
      el('p', {}, 'Nothing this quarter. Your agent says it is quiet everywhere, which is what agents say.')));
  }

  for (const r of board) {
    const cast = game.blocksBooked + r.blocks > 4;
    const locked = r.union && game.actor.unionCredits < 3;
    const card = el('div', {
      class: `card${cast || locked ? '' : ' pick'}`,
      onclick: cast || locked ? null : () => attempt(r),
    },
      el('h4', {}, r.title),
      el('div', { class: 'meta' },
        `${r.billing} · ${r.genre} · ${r.label} · $${r.budget.toFixed(0)}M · ${r.blocks} block${r.blocks > 1 ? 's' : ''} · dir. ${r.director.name}`),
      el('p', { class: 'why' }, roleBlurb(r)),
      el('div', { class: 'tags' },
        el('span', { class: `tag ${r.path === 'direct' ? 'good' : r.path === 'offer' ? 'good' : ''}` },
          r.path === 'direct' ? `offered by ${r.director.name}` : r.path === 'offer' ? 'offer, no audition' : 'audition'),
        el('span', { class: 'tag' }, `fit ${r.fit.toFixed(0)}`),
        el('span', { class: 'tag' }, `they want someone about ${r.charAge}`),
        r.nonUnionNote ? el('span', { class: 'tag warn' }, 'non-union, pays nothing') : null,
        locked ? el('span', { class: 'tag warn' }, `union — you have ${game.actor.unionCredits}/3`) : null,
        cast ? el('span', { class: 'tag warn' }, 'no dates') : null,
        r.path === 'audition' ? el('span', { class: 'tag' }, `${(100 * r.chance * (r.billing === 'lead' ? M.K.fieldLead : r.billing === 'supporting' ? M.K.fieldSupporting : M.K.fieldBit)).toFixed(0)}% shot`) : null,
      ),
    );
    stage.append(card);
  }

  stage.append(el('div', { style: 'margin-top:18px' },
    el('button', { onclick: () => advanceQuarter() }, 'Let the quarter go by')));
}

function boardMood(board) {
  const s = M.standing(game.actor.standing);
  if (!board.length) return 'The phone does not ring.';
  if (s > 70) return 'Everything on this list wants you specifically. That is the trap and the prize.';
  if (s > 35) return 'Your agent has read all of these. Two of them she thinks are beneath you.';
  if (game.actor.unionCredits < 3) return 'Non-union work, mostly. Three credits and the real board opens.';
  return 'What is available is what is available.';
}

function roleBlurb(r) {
  const d = r.director;
  const tone = { generous: 'known for being good with actors', exacting: 'known for take forty',
    chaotic: 'known for rewriting on the day', remote: 'known for not speaking to the cast' }[d.temperament];
  return `${r.archetype.replace(/_/g, ' ')} in a ${r.genre} picture. ${d.name} is ${tone}. `
    + `Script reads ${r.scriptQuality > 72 ? 'genuinely good' : r.scriptQuality > 55 ? 'competent' : 'thin'}.`;
}

function attempt(role) {
  const res = game.pursue(role.id);
  drawHud();
  if (!res.cast) {
    clear();
    stage.append(
      el('h2', {}, role.title),
      el('p', { class: 'lede' }, res.note || 'They went another way. You will not be told why.'),
      el('button', { class: 'primary', onclick: () => screenQuarter(false) }, 'Back to the board'),
    );
    return;
  }
  choice = { role, prep: 'table', positions: { energy: 'with', volume: 'with', warmth: 'with', speed: 'with' }, moments: {}, momentIndex: 0 };
  screenPrep();
}

// ---------------------------------------------------------------------------
// 3. prep
// ---------------------------------------------------------------------------
function screenPrep() {
  clear();
  const r = choice.role;
  stage.append(
    el('h2', {}, `You are doing ${r.title}`),
    el('p', { class: 'lede' },
      `${r.billing === 'lead' ? 'Above the title.' : r.billing === 'supporting' ? 'Fourth on the call sheet.' : 'Two scenes.'} `
      + `${r.blocks} block${r.blocks > 1 ? 's' : ''} of the year, ${money(r.budgetForRole)} in the role's budget.`),
    el('h3', { class: 'section' }, 'How you prepare'),
  );
  for (const [key, p] of Object.entries(PREP_OPTIONS)) {
    stage.append(el('div', {
      class: 'card pick',
      style: choice.prep === key ? 'border-color: var(--accent)' : '',
      onclick: () => { choice.prep = key; screenPrep(); },
    },
      el('h4', {}, p.label),
      el('div', { class: 'meta' }, `${p.weeks} weeks${p.health ? ` · health ${p.health}` : ''}${p.resilience ? ` · resilience ${p.resilience}` : ''}${p.flag ? ' · award narrative flag' : ''}`),
    ));
  }
  stage.append(el('button', { class: 'primary', onclick: () => screenPositions() }, 'To the set'));
}

// ---------------------------------------------------------------------------
// 4. the palette and your positions against it — the core creative decision
// ---------------------------------------------------------------------------
function screenPositions() {
  clear();
  const r = choice.role;
  if (!choice.palette) {
    choice.palette = game.world.randomPalette(game.rng, r.genre, r.budget, r.director.taste);
    r.palette = choice.palette;
  }
  const coh = M.coherence(choice.palette);
  const budget = M.contrastBudget(game.actor.attrs.craft, r.director.command);
  const spent = PERF_DIALS.reduce((a, d) => a + POSITION_COST[choice.positions[d]], 0);

  stage.append(
    el('h2', {}, 'The film they are making'),
    el('p', { class: 'lede' },
      `${r.director.name} is shooting something ${coh.value > 65 ? 'very much like' : coh.value > 40 ? 'loosely in the shape of' : 'that does not resemble'} `
      + `a ${coh.nearest.replace(/_/g, ' ')}. Coherence ${coh.value.toFixed(0)}`
      + `${coh.value < 40 ? ' — wide open. It is a mess or it is a landmark.' : '.'}`),
    el('div', { class: 'palette' }, DIALS.flatMap((d) => [
      el('div', { class: 'l' }, DIAL_LABELS[d][0]),
      el('div', { class: 'track' }, el('i', { style: `left:${((choice.palette[d] + 50) / 100) * 100}%` })),
      el('div', { class: 'r' }, DIAL_LABELS[d][1]),
    ])),
    el('h3', { class: 'section' }, 'What you play against it'),
    el('p', {},
      'With: you move as the film moves. Beneath: the calm inside it. '
      + 'Beyond: the most of it on screen. Against: counterpoint. '
      + 'Holding a position costs you; holding several costs more than most actors have.'),
  );

  const table = el('table', { class: 'dials' });
  for (const d of PERF_DIALS) {
    table.append(el('tr', {},
      el('td', {}, d),
      el('td', {}, POSITIONS.map((p) => el('button', {
        class: choice.positions[d] === p ? 'selected' : '',
        onclick: () => { choice.positions[d] = p; screenPositions(); },
      }, `${p} (${POSITION_COST[p]})`))),
    ));
  }
  stage.append(table);
  stage.append(el('div', { class: `budgetline${spent > budget ? ' over' : ''}` },
    `contrast budget ${budget.toFixed(1)} · spending ${spent}`
    + (spent > budget ? ' — over. Critics will call it mannered.' : '')));

  stage.append(el('div', { style: 'margin-top:18px' },
    el('button', { class: 'primary', onclick: () => screenMoment(0) }, 'Shoot it')));
}

// ---------------------------------------------------------------------------
// 5. the three moments
// ---------------------------------------------------------------------------
function screenMoment(i) {
  if (i >= MOMENTS.length) return resolveShoot();
  clear();
  const m = MOMENTS[i];
  stage.append(
    el('h2', {}, choice.role.title),
    el('p', { class: 'lede' }, m.prompt),
  );
  for (const opt of m.options) {
    stage.append(el('div', {
      class: 'card pick',
      onclick: () => { choice.moments[m.id] = opt.id; screenMoment(i + 1); },
    }, el('h4', {}, opt.label)));
  }
}

function resolveShoot() {
  const project = game.shoot(choice.role, {
    prep: choice.prep, positions: choice.positions, moments: choice.moments,
  });
  drawHud();
  clear();
  stage.append(
    el('h2', {}, `${choice.role.title} wrapped`),
    el('p', { class: 'lede' }, game.log[game.log.length - 1].text),
    el('div', { class: 'attrib' },
      el('div', {}, `You were paid ${money(project.fee)}.`),
      el('div', {}, project.resolved.overspend > 0
        ? 'You were carrying more than you could hold. You could feel it in the last week.'
        : 'It held together.'),
      el('div', {}, project.landmark
        ? 'Nobody has made anything that looks like this before.'
        : `It comes out in ${project.releaseIn} quarter${project.releaseIn > 1 ? 's' : ''}.`),
    ),
    el('button', { class: 'primary', onclick: () => advanceQuarter() }, 'Next'),
  );
}

// ---------------------------------------------------------------------------
// 6. quarter turnover, releases, the year
// ---------------------------------------------------------------------------
function advanceQuarter() {
  const cards = game.tickPending();
  game.world.tickQuarter();
  const yearRolled = game.world.quarter === 1;
  if (cards.length) return screenRelease(cards, 0, yearRolled);
  if (yearRolled) return screenYearEnd();
  screenQuarter();
}

function screenRelease(cards, i, yearRolled) {
  if (i >= cards.length) return yearRolled ? screenYearEnd() : screenQuarter();
  drawHud();
  clear();
  const c = cards[i];
  const rec = c.rec;
  stage.append(
    el('h2', {}, `${c.project.role.title} is out`),
    el('p', { class: 'lede' }, c.headline),
    el('div', { class: 'tags' },
      el('span', { class: `tag ${rec.filmCritic > 66 ? 'good' : rec.filmCritic < 45 ? 'warn' : ''}` }, `critics ${rec.filmCritic.toFixed(0)}`),
      el('span', { class: `tag ${rec.notices > 66 ? 'good' : rec.notices < 45 ? 'warn' : ''}` }, `your notices ${rec.notices.toFixed(0)}`),
      el('span', { class: 'tag' }, `audience ${rec.audience.toFixed(0)}`),
      el('span', { class: `tag ${rec.roi > 1.4 ? 'hot' : rec.roi < 0.8 ? 'warn' : ''}` }, `roi ${rec.roi.toFixed(2)}`),
    ),
    el('div', { class: 'attrib' }, c.attribution.map((t) => el('div', {}, t))),
    el('div', { class: 'attrib' },
      el('div', {}, `Heat ${c.deltas.dHeat >= 0 ? '+' : ''}${c.deltas.dHeat.toFixed(1)} · `
        + `Prestige ${c.deltas.dPrestige >= 0 ? '+' : ''}${c.deltas.dPrestige.toFixed(1)} · `
        + `Affection ${c.deltas.dAffection >= 0 ? '+' : ''}${c.deltas.dAffection.toFixed(1)}`),
      c.deltas.discovery > 1.05 ? el('div', {}, 'A new face counts for more than it should. Use it.') : null,
      c.staleness > 0 ? el('div', {}, `Critics note you have done this ${game.actor.consecutiveSameLane + 1} times now (−${c.staleness}).`) : null,
    ),
    el('button', { class: 'primary', onclick: () => screenRelease(cards, i + 1, yearRolled) }, 'Next'),
  );
}

function screenYearEnd() {
  const before = { ...game.actor.standing };
  const noms = game.awards.thisSeason.length;
  game.endYear();
  drawHud();
  if (game.over) return screenObituary();
  clear();
  const a = game.actor;
  stage.append(
    el('h2', {}, `${game.year - 1} is over`),
    el('p', { class: 'lede' },
      noms ? 'Awards season came and went.' : 'No campaign this year. Nobody was going to nominate any of it.'),
    el('div', { class: 'attrib' },
      el('div', {}, `You are ${a.age}. Heat fell to ${a.standing.heat.toFixed(0)} from ${before.heat.toFixed(0)} — it always does.`),
      el('div', {}, `Legibility ${game.legibility.toFixed(0)} — ${
        game.legibility < 36 ? 'casting directors still do not know what you are.'
          : game.legibility > 70 ? 'everyone knows exactly what you are, which is a floor and a ceiling.'
          : 'known for two or three things. The healthy place.'}`),
      el('div', {}, `Standing ${game.standing.toFixed(0)} · recognition ${a.recognition.toFixed(0)} · ${a.unionCredits} union credits`),
      el('div', {}, `${money(game.money.net)} banked. Your life costs ${money(game.money.floor)} a year now.`),
      a.health < 60 ? el('div', {}, 'Your body is keeping a list.') : null,
    ),
    el('button', { class: 'primary', onclick: () => screenQuarter() }, `On to ${game.year}`),
  );
}

// ---------------------------------------------------------------------------
// 7. the obituary — where the private numbers finally become public
// ---------------------------------------------------------------------------
function screenObituary() {
  drawHud();
  clear();
  const lines = game.obituary();
  stage.append(
    el('h2', {}, game.actor.name),
    el('div', { class: 'obit' }, lines.map((l) => el('p', {}, l))),
    el('h3', { class: 'section' }, 'The credits'),
    el('div', { class: 'card' }, game.credits.length
      ? game.credits.map((c) => el('div', { class: 'meta' }, `${c.year}  ${c.title} — ${c.billing}, ${c.genre}`))
      : el('p', {}, 'None.')),
    el('div', { style: 'margin-top:20px' },
      el('button', { class: 'primary', onclick: () => { game = null; screenCreate(); } }, 'Again')),
  );
}

screenCreate();
