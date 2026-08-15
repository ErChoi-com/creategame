// CALLBACK — the front end. All rules live in ../engine; this file only asks
// questions and draws answers.
//
// Two kinds of screen, and the difference is the whole design:
//   PUSH — the game stops and asks you something. Budgeted, ~5 a year.
//   PULL — you open the moves menu because you want to. Unbudgeted, ~30 verbs.

import { Game, BACKGROUNDS, PREP_OPTIONS, MOMENTS } from '../engine/career.js';
import { DIAL_LABELS, DIALS, PERF_DIALS, POSITIONS, POSITION_COST } from '../engine/data.js';
import { AMBITIONS, ambitionAdvice } from '../engine/ambition.js';
import * as M from '../engine/model.js';

const stage = document.getElementById('stage');
const hud = document.getElementById('hud');
const ledger = document.getElementById('ledger');

let game = null;
let choice = {};
let showAllMoves = false;

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
    `${a.age} · ${game.year} ${quarterName(game.quarter)} · ${game.blocksBooked}/4 blocks`
    + (game.hiatus ? ' · away' : '');
  for (const k of ['heat', 'prestige', 'affection', 'notoriety']) {
    document.getElementById(`m-${k}`).style.width = `${a.standing[k]}%`;
    document.getElementById(`v-${k}`).textContent = a.standing[k].toFixed(0);
  }
  document.getElementById('hud-quote').textContent = `quote ${money(a.quote)}`;
  document.getElementById('hud-money').textContent =
    `${money(game.money.net)} banked · ${money(game.money.lifetime)} lifetime`;

  const log = document.getElementById('log');
  log.replaceChildren(...game.log.slice(-16).reverse().map(
    (e) => el('li', { class: e.kind }, `${e.year} · ${e.text}`),
  ));
  drawState();
}

// The quiet panel: everything you are carrying, none of it demanding anything.
function drawState() {
  const box = document.getElementById('state');
  if (!box) return;
  const g = game;
  const amb = g.ambitionReport();
  const bits = [
    ['Ambition', `${amb.label} — ${amb.value} (${amb.grade.toLowerCase()})`],
    ['Standing', g.standing.toFixed(0)],
    ['Legibility', `${g.legibility.toFixed(0)} — ${g.legibility < 36 ? 'unreadable'
      : g.legibility > 70 ? 'typecast' : 'known for a few things'}`],
    ['Favours owed you', g.favours.toFixed(0)],
    g.scarcity > 0 ? ['Scarcity', g.scarcity.toFixed(0)] : null,
    g.franchise && !g.franchise.writtenOut
      ? ['Franchise', `${g.franchise.title} — identification ${g.franchise.identification.toFixed(0)}`] : null,
    g.approvals.size ? ['Approvals', [...g.approvals].join(', ')] : null,
    g.positions.size ? ['Positions', [...g.positions].join(', ')] : null,
    g.development.length ? ['In development', g.development.map((s) => s.title).join(', ')] : null,
    g.mentees.length ? ['Taught', g.mentees.map((m) => `${m.person.name} (${m.power.toFixed(0)})`).join(', ')] : null,
    g.information.length ? ['You know things about', g.information.map((i) => i.about.name).join(', ')] : null,
  ].filter(Boolean);
  box.replaceChildren(...bits.map(([k, v]) => el('div', { class: 'statline' },
    el('span', {}, k), el('b', {}, v))));
}

// ---------------------------------------------------------------------------
// The moves menu — pull. Reachable from anywhere, never prompted.
// ---------------------------------------------------------------------------
function movesPanel(ctx, redraw) {
  const all = game.moves(ctx);
  const shown = showAllMoves ? all : all.slice(0, 5);
  const wrap = el('div', { class: 'moves' },
    el('h3', { class: 'section' },
      `What you could do — ${all.length} available`,
      el('button', {
        class: 'tiny',
        onclick: () => { showAllMoves = !showAllMoves; redraw(); },
      }, showAllMoves ? 'show fewer' : 'show all'),
    ),
  );
  if (!all.length) {
    wrap.append(el('p', { class: 'why' }, 'Nothing you can make happen from here today.'));
    return wrap;
  }
  for (const { action } of shown) {
    wrap.append(el('div', {
      class: 'card pick move',
      onclick: () => {
        const res = game.do(action.id, ctx);
        drawHud();
        showAllMoves = false;
        redraw(res.text);
      },
    },
      el('h4', {}, action.label),
      el('div', { class: 'meta' }, `${action.category} · costs: ${action.cost(game)}`),
      el('p', { class: 'why' }, action.blurb),
    ));
  }
  return wrap;
}

// ---------------------------------------------------------------------------
// 1. character creation
// ---------------------------------------------------------------------------
function screenCreate() {
  clear();
  hud.hidden = true;
  ledger.hidden = true;
  let picked = 'conservatory';
  let ambition = 'work';

  const render = () => {
    clear();
    stage.append(
      el('h1', {}, 'Callback'),
      el('p', { class: 'lede' },
        'You are an actor. The work is the game: what you take, how you play it, and what the '
        + 'industry decides that means. Nobody will ever tell you how good you were.'),
      el('h3', { class: 'section' }, 'Where you are starting from'),
      el('div', { class: 'grid2' }, Object.entries(BACKGROUNDS).map(([key, bg]) => el('div', {
        class: 'card pick',
        style: picked === key ? 'border-color: var(--accent)' : '',
        onclick: () => { picked = key; render(); },
      },
        el('h4', {}, bg.label),
        el('div', { class: 'meta' }, `age ${bg.age} · ${bg.unionCredits}/3 union credits · ${
          bg.agent === 'none' ? 'no agent' : bg.agent} · ${money(bg.money)}`),
        el('p', { class: 'why' }, bg.blurb),
        el('div', { class: 'tags' }, Object.entries(bg.attrs).map(
          ([k, v]) => el('span', { class: 'tag' }, `${k} ${v}`))),
      ))),
      el('h3', { class: 'section' }, 'What you want it to have been for'),
      el('p', { class: 'why' },
        'This gates nothing. It decides what the obituary measures you against, and you can '
        + 'change it once.'),
      el('div', { class: 'grid2' }, Object.entries(AMBITIONS).map(([key, a]) => el('div', {
        class: 'card pick',
        style: ambition === key ? 'border-color: var(--accent)' : '',
        onclick: () => { ambition = key; render(); },
      },
        el('h4', {}, a.label),
        el('p', { class: 'why' }, a.blurb),
        el('div', { class: 'meta' }, `measured by ${a.measure}`),
      ))),
    );

    const nameInput = el('input', { placeholder: 'a name, or leave it blank', class: 'text' });
    const seedInput = el('input', { placeholder: 'seed', class: 'text short' });
    stage.append(
      el('h3', { class: 'section' }, 'Who you are'),
      el('div', {}, nameInput, seedInput),
      el('div', { style: 'margin-top:20px' }, el('button', {
        class: 'primary',
        onclick: () => {
          const seed = seedInput.value ? Number(seedInput.value) : Math.floor(Math.random() * 1e9);
          game = new Game({
            seed, background: picked, ambition,
            name: nameInput.value.trim() || undefined,
          });
          game.say(`${BACKGROUNDS[picked].label}. ${game.year}. Nobody knows your name yet.`);
          screenQuarter();
        },
      }, 'Start working')),
    );
  };
  render();
}

// ---------------------------------------------------------------------------
// 2. the quarter — the board, and the moves menu beside it
// ---------------------------------------------------------------------------
function screenQuarter(fresh = true, flash = null) {
  if (game.over) return screenObituary();
  if (fresh) game.openBoard();
  drawHud();
  clear();
  const board = game.board;

  stage.append(
    el('h2', {}, `${game.year} · ${quarterName(game.quarter)}`),
    flash ? el('p', { class: 'flash' }, flash) : null,
    el('p', { class: 'lede' }, boardMood(board)),
  );

  if (game.hiatus) {
    stage.append(el('div', { class: 'card' }, el('p', {},
      'You are not working. Nobody is being told why. '
      + `Scarcity ${game.scarcity.toFixed(0)} of 40.`)));
  } else if (!board.length) {
    stage.append(el('div', { class: 'card' }, el('p', {},
      'Nothing this quarter. Your agent says it is quiet everywhere, which is what agents say.')));
  }

  for (const r of board) {
    const noDates = game.blocksBooked + r.blocks > 4;
    const locked = r.union && game.actor.unionCredits < 3;
    const advice = ambitionAdvice(game, r);
    stage.append(el('div', { class: 'card' },
      el('h4', {}, r.title),
      el('div', { class: 'meta' },
        `${r.billing} · ${r.genre} · ${r.label} · $${r.budget.toFixed(0)}M · `
        + `${r.blocks} block${r.blocks > 1 ? 's' : ''} · dir. ${r.director.name}`),
      el('p', { class: 'why' }, roleBlurb(r)),
      advice ? el('p', { class: 'advice' }, advice) : null,
      el('div', { class: 'tags' },
        el('span', { class: `tag ${r.path === 'audition' ? '' : 'good'}` },
          r.viaFavour ? `${r.viaFavour} made a call`
            : r.franchiseInstallment ? 'they need you back'
            : r.yours ? 'you made this exist'
            : r.comeback ? 'they waited for you'
            : r.path === 'direct' ? `offered by ${r.director.name}`
            : r.path === 'offer' ? 'offer, no audition' : 'audition'),
        el('span', { class: 'tag' }, `fit ${r.fit.toFixed(0)}`),
        el('span', { class: 'tag' }, `they want someone about ${r.charAge}`),
        r.takeScale ? el('span', { class: 'tag good' }, 'you offered to do it for scale') : null,
        r.publicCampaign ? el('span', { class: 'tag warn' }, 'you said publicly you want it') : null,
        r.nonUnionNote ? el('span', { class: 'tag warn' }, 'non-union') : null,
        locked ? el('span', { class: 'tag warn' }, `union — you have ${game.actor.unionCredits}/3`) : null,
        noDates ? el('span', { class: 'tag warn' }, 'no dates') : null,
        r.path === 'audition'
          ? el('span', { class: 'tag' }, `${(100 * r.chance * fieldFor(r)).toFixed(0)}% shot`) : null,
      ),
      el('div', { class: 'row' },
        el('button', {
          class: 'primary',
          disabled: noDates || locked,
          onclick: () => attempt(r),
        }, r.path === 'audition' ? 'Read for it' : 'Take it'),
        el('button', { onclick: () => { game.decline(r.id); screenQuarter(false, 'Passed.'); } }, 'Pass'),
        el('button', {
          onclick: () => screenMoves({ role: r }, `About ${r.title}`),
        }, 'Do something about it'),
      ),
    ));
  }

  stage.append(
    movesPanel({}, (text) => screenQuarter(false, text)),
    el('div', { class: 'row spaced' },
      el('button', {
        // When there is nothing to take, moving on is the obvious action and
        // should look like it.
        class: board.some((r) => game.blocksBooked + r.blocks <= 4
          && !(r.union && game.actor.unionCredits < 3)) ? '' : 'primary',
        onclick: () => advanceQuarter(),
      }, 'Let the quarter go by'),
      el('button', { onclick: () => screenRolodex() }, 'The Rolodex'),
      el('button', { onclick: () => screenOrders() }, 'Standing orders'),
    ),
  );
}

const fieldFor = (r) => (r.billing === 'lead' ? M.K.fieldLead
  : r.billing === 'supporting' ? M.K.fieldSupporting : M.K.fieldBit);

function boardMood(board) {
  const s = M.standing(game.actor.standing);
  if (game.hiatus) return 'You are away.';
  if (!board.length) return 'The phone does not ring.';
  if (game.legibility > 72) return 'Every one of these is the part you already played. That is what being legible buys.';
  if (s > 70) return 'Everything on this list wants you specifically. That is the trap and the prize.';
  if (s > 35) return 'Your agent has read all of these. Two of them she thinks are beneath you.';
  if (game.actor.unionCredits < 3) return 'Non-union work, mostly. Three credits and the real board opens.';
  return 'What is available is what is available.';
}

function roleBlurb(r) {
  const tone = { generous: 'known for being good with actors', exacting: 'known for take forty',
    chaotic: 'known for rewriting on the day', remote: 'known for not speaking to the cast' }[r.director.temperament];
  return `${r.archetype.replace(/_/g, ' ')} in a ${r.genre} picture. ${r.director.name} is ${tone}. `
    + `Script reads ${r.scriptQuality > 72 ? 'genuinely good' : r.scriptQuality > 55 ? 'competent' : 'thin'}.`;
}

// A moves screen scoped to one thing (a listing, or the project you are on).
function screenMoves(ctx, title) {
  clear();
  drawHud();
  stage.append(
    el('h2', {}, title),
    el('p', { class: 'lede' }, 'Nothing here is required. Nothing here will ever be asked of you.'),
    movesPanel(ctx, (text) => screenMoves(ctx, title)),
    el('button', { class: 'primary', onclick: () => (ctx.current ? screenPrep() : screenQuarter(false)) },
      'Back'),
  );
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
  choice = { role, prep: game.standingOrders.prep, positions: null, moments: {} };
  screenPrep();
}

// ---------------------------------------------------------------------------
// 3. prep — asked only when the answer could differ
// ---------------------------------------------------------------------------
function screenPrep() {
  const r = choice.role;
  if (!game.shouldAskPrep(r)) return screenFilm(`You prepared the way you always do: ${PREP_OPTIONS[game.standingOrders.prep].label.toLowerCase()}.`);
  clear();
  drawHud();
  game.countPush('prep');
  stage.append(
    el('h2', {}, `You are doing ${r.title}`),
    el('p', { class: 'lede' },
      `${r.billing === 'lead' ? 'Above the title.' : r.billing === 'supporting' ? 'Fourth on the call sheet.' : 'Two scenes.'} `
      + `${r.blocks} block${r.blocks > 1 ? 's' : ''}, ${money(r.budgetForRole)} in the role's budget.`),
    el('h3', { class: 'section' }, 'This one is worth thinking about'),
  );
  for (const [key, p] of Object.entries(PREP_OPTIONS)) {
    stage.append(el('div', {
      class: 'card pick',
      style: choice.prep === key ? 'border-color: var(--accent)' : '',
      onclick: () => { choice.prep = key; screenPrep(); },
    },
      el('h4', {}, p.label),
      el('div', { class: 'meta' },
        `${p.weeks} weeks${p.health ? ` · health ${p.health}` : ''}`
        + `${p.resilience ? ` · resilience ${p.resilience}` : ''}${p.flag ? ' · award narrative' : ''}`),
    ));
  }
  stage.append(el('div', { class: 'row' },
    el('button', { class: 'primary', onclick: () => screenFilm() }, 'To the set'),
    el('button', { onclick: () => screenMoves({ current: r }, `Before you shoot ${r.title}`) },
      'Do something about the project'),
  ));
}

// ---------------------------------------------------------------------------
// 4. the film, and your positions against it
// ---------------------------------------------------------------------------
function screenFilm(note) {
  const r = choice.role;
  if (!choice.palette) {
    choice.palette = game.world.randomPalette(game.rng, r.genre, r.budget, r.director.taste);
    r.palette = choice.palette;
  }
  const coh = M.coherence(choice.palette);
  if (!game.shouldAskStance(r, { coherence: coh.value })) {
    choice.positions = game.autoPositions(r);
    return resolveShoot(note);
  }
  if (!choice.positions) choice.positions = game.autoPositions(r);
  game.countPush('stance');

  clear();
  drawHud();
  const budget = M.contrastBudget(game.actor.attrs.craft, r.director.command);
  const spent = PERF_DIALS.reduce((a, d) => a + POSITION_COST[choice.positions[d]], 0);

  stage.append(
    note ? el('p', { class: 'flash' }, note) : null,
    el('h2', {}, 'The film they are making'),
    el('p', { class: 'lede' },
      `${r.director.name} is shooting something ${coh.value > 65 ? 'very much like'
        : coh.value > 40 ? 'loosely in the shape of' : 'that does not resemble'} `
      + `a ${coh.nearest.replace(/_/g, ' ')}. Coherence ${coh.value.toFixed(0)}`
      + `${coh.value < 40 ? ' — wide open. It is a mess or it is a landmark.' : '.'}`),
    el('div', { class: 'palette' }, DIALS.flatMap((d) => [
      el('div', { class: 'l' }, DIAL_LABELS[d][0]),
      el('div', { class: 'track' }, el('i', { style: `left:${((choice.palette[d] + 50) / 100) * 100}%` })),
      el('div', { class: 'r' }, DIAL_LABELS[d][1]),
    ])),
    el('h3', { class: 'section' }, 'What you play against it'),
    el('p', {},
      'With: you move as the film moves. Beneath: the calm inside it. Beyond: the most of it '
      + 'on screen. Against: counterpoint. Every position costs, and you have only so much.'),
  );

  const table = el('table', { class: 'dials' });
  for (const d of PERF_DIALS) {
    table.append(el('tr', {},
      el('td', {}, d),
      el('td', {}, POSITIONS.map((p) => el('button', {
        class: choice.positions[d] === p ? 'selected' : '',
        onclick: () => { choice.positions[d] = p; renderStanceOnly(); },
      }, `${p} (${POSITION_COST[p]})`))),
    ));
  }
  stage.append(table,
    el('div', { class: `budgetline${spent > budget ? ' over' : ''}` },
      `contrast budget ${budget.toFixed(1)} · spending ${spent}`
      + (spent > budget ? ' — over. Critics will call it mannered.' : '')),
    el('div', { class: 'row' },
      el('button', { class: 'primary', onclick: () => resolveShoot() }, 'Shoot it'),
      el('button', { onclick: () => screenMoves({ current: r }, `Before you shoot ${r.title}`) },
        'Do something about the project'),
    ));

  function renderStanceOnly() { screenFilm(); }
}

// ---------------------------------------------------------------------------
// 5. the moments that still fire
// ---------------------------------------------------------------------------
function resolveShoot(note) {
  const prompted = game.momentsFor(choice.role);
  return runMoments(prompted, 0, note);
}

function runMoments(list, i, note) {
  if (i >= list.length) return finishShoot(note);
  clear();
  drawHud();
  game.countPush('moment');
  const m = list[i];
  stage.append(
    note && i === 0 ? el('p', { class: 'flash' }, note) : null,
    el('h2', {}, choice.role.title),
    el('p', { class: 'lede' }, m.prompt),
  );
  for (const opt of m.options) {
    stage.append(el('div', {
      class: 'card pick',
      onclick: () => { choice.moments[m.id] = opt.id; runMoments(list, i + 1); },
    }, el('h4', {}, opt.label)));
  }
}

function finishShoot(note) {
  const project = game.shoot(choice.role, {
    prep: choice.prep, positions: choice.positions, moments: choice.moments,
  });
  drawHud();
  clear();
  const unasked = project.momentLog.filter((m) => !m.asked);
  stage.append(
    note ? el('p', { class: 'flash' }, note) : null,
    el('h2', {}, `${choice.role.title} wrapped`),
    el('p', { class: 'lede' }, game.log.filter((l) => l.kind === 'work').slice(-1)[0]?.text || ''),
    el('div', { class: 'attrib' },
      el('div', {}, `You were paid ${money(project.fee)}.`),
      unasked.length
        ? el('div', {}, `Three months of days you have had a hundred times: ${
          unasked.map((m) => m.chose.toLowerCase()).join('; ')}.`)
        : null,
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
// 6. turnover
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
    ),
    el('button', { class: 'primary', onclick: () => screenRelease(cards, i + 1, yearRolled) }, 'Next'),
  );
}

function screenYearEnd() {
  const before = { ...game.actor.standing };
  const needsYou = game.seasonNeedsYou();
  if (needsYou) return screenSeason(before);
  finishYear(before);
}

// The season only stops you when there is something to decide.
function screenSeason(before) {
  clear();
  drawHud();
  game.countPush('season');
  const contenders = game.awards.thisSeason.map((e) => e.project.role.title).join(', ');
  stage.append(
    el('h2', {}, 'Awards season'),
    el('p', { class: 'lede' }, `They are talking about ${contenders}. Talk is the whole mechanism.`),
    movesPanel({}, () => screenSeason(before)),
    el('button', { class: 'primary', onclick: () => finishYear(before) }, 'Let the season happen'),
  );
}

function finishYear(before) {
  game.endYear();
  drawHud();
  if (game.over) return screenObituary();
  clear();
  const a = game.actor;
  stage.append(
    el('h2', {}, `${game.year - 1} is over`),
    el('div', { class: 'attrib' },
      el('div', {}, `You are ${a.age}. Heat fell to ${a.standing.heat.toFixed(0)} from ${before.heat.toFixed(0)} — it always does.`),
      el('div', {}, `Legibility ${game.legibility.toFixed(0)} — ${
        game.legibility < 36 ? 'casting directors still do not know what you are.'
          : game.legibility > 70 ? 'everyone knows exactly what you are, which is a floor and a ceiling.'
          : 'known for two or three things. The healthy place.'}`),
      el('div', {}, `Standing ${game.standing.toFixed(0)} · recognition ${a.recognition.toFixed(0)} · ${a.unionCredits} union credits · ${game.favours} favours owed you`),
      el('div', {}, `${money(game.money.net)} banked. Your life costs ${money(game.money.floor)} a year now.`),
      a.health < 60 ? el('div', {}, 'Your body is keeping a list.') : null,
    ),
    el('button', { class: 'primary', onclick: () => screenQuarter() }, `On to ${game.year}`),
  );
}

// ---------------------------------------------------------------------------
// 7. the Rolodex and the standing orders
// ---------------------------------------------------------------------------
function screenRolodex() {
  clear();
  drawHud();
  const tracked = game.rolodex.tracked();
  stage.append(
    el('h2', {}, 'The Rolodex'),
    el('p', { class: 'lede' },
      'Eight people, chosen by how much they matter rather than by you maintaining a list. '
      + 'Everyone else is real and quiet.'),
  );
  if (!tracked.length) {
    stage.append(el('div', { class: 'card' }, el('p', {}, 'You do not know anybody yet.')));
  }
  for (const e of tracked) {
    stage.append(el('div', { class: 'card' },
      el('h4', {}, e.person.name),
      el('div', { class: 'meta' },
        `${e.person.kind} · ${e.sharedProjects} together · affinity ${e.affinity.toFixed(0)}`
        + `${e.grudge > 5 ? ` · grudge ${e.grudge.toFixed(0)}` : ''}`
        + `${e.favours ? ` · owes you ${e.favours}` : ''}`),
      e.history.length
        ? el('p', { class: 'why' }, e.history.slice(-2).map((h) => `${h.year}: ${h.text}`).join(' '))
        : null,
      el('div', { class: 'row' }, el('button', {
        onclick: () => screenMoves({ person: e }, e.person.name),
      }, 'Call them')),
    ));
  }
  stage.append(el('button', { class: 'primary', onclick: () => screenQuarter(false) }, 'Back'));
}

function screenOrders() {
  clear();
  drawHud();
  const o = game.standingOrders;
  const set = (k, v) => { o[k] = v; screenOrders(); };
  const group = (label, key, options, blurb) => el('div', { class: 'card' },
    el('h4', {}, label),
    el('p', { class: 'why' }, blurb),
    el('div', { class: 'row' }, options.map(([v, text]) => el('button', {
      class: o[key] === v ? 'selected' : '',
      onclick: () => set(key, v),
    }, text))),
  );
  stage.append(
    el('h2', {}, 'Standing orders'),
    el('p', { class: 'lede' },
      'How you work when the game does not need to ask. This is the dial between a career '
      + 'you micromanage and one you steer — the work still happens either way.'),
    group('Default preparation', 'prep',
      Object.entries(PREP_OPTIONS).map(([k, p]) => [k, p.label]),
      'What you reach for when the role does not raise a question.'),
    group('Default stance', 'stance', [
      ['shaped', 'Mostly restraint, one strong idea'],
      ['generous', 'Play for the film and your partners'],
      ['showy', 'Play for your own reviews'],
      ['still', 'Be the quiet centre of it'],
    ], 'How you position yourself against a film you are not asked about.'),
    group('What reaches you', 'floor', [
      ['anything', 'Anything at all'],
      ['supporting', 'Supporting and above'],
      ['lead', 'Leads only'],
    ], 'Your agent stops bringing you what you would never take.'),
    group('How often to ask', 'askWhenInteresting', [
      [true, 'Ask me when it is interesting'],
      [false, 'Never ask; run on these orders'],
    ], 'The second option plays the whole career on defaults. It is a real way to play.'),
    el('button', { class: 'primary', onclick: () => screenQuarter(false) }, 'Back'),
  );
}

// ---------------------------------------------------------------------------
// 8. the obituary
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
    game.turnedDown.length ? el('h3', { class: 'section' }, 'And what they passed on') : null,
    game.turnedDown.length
      ? el('div', { class: 'card' }, game.turnedDown.slice(-12).map(
        (c) => el('div', { class: 'meta' }, `${c.year}  ${c.title} — ${c.billing}, $${c.budget.toFixed(0)}M, ${c.director}`)))
      : null,
    el('div', { style: 'margin-top:20px' },
      el('button', { class: 'primary', onclick: () => { game = null; screenCreate(); } }, 'Again')),
  );
}

screenCreate();
