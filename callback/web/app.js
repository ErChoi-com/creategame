// CALLBACK — the front end. All rules live in ../engine; this file only asks
// questions and draws answers.
//
// Two kinds of screen, and the difference is the whole design:
//   PUSH — the game stops and asks you something. Budgeted, ~5 a year.
//   PULL — you open the moves menu because you want to. Unbudgeted, ~30 verbs.

import { Game, BACKGROUNDS, PREP_OPTIONS, MOMENTS, SCENE_LABELS } from '../engine/career.js';
import {
  DIAL_LABELS, DIAL_AXIS_LABELS, DIALS, PERF_DIALS, PERF_DIAL_LABELS, PERF_DIAL_HINTS,
  POSITIONS, POSITION_COST, POSITION_LABELS, POSITION_HINTS, READ, GENRE_DIAL_WEIGHT,
  GENRE_NAMES, APPROVAL_LABELS, CAREER_POSITION_LABELS, SHAPE_LABELS,
} from '../engine/data.js';
import { AMBITIONS, ambitionAdvice } from '../engine/ambition.js';
import { ARCS_BY_ID } from '../engine/arcs.js';
import * as M from '../engine/model.js';

const stage = document.getElementById('stage');
const hud = document.getElementById('hud');
const ledger = document.getElementById('ledger');

let game = null;
let choice = {};
let showAllMoves = false;

const SAVE_KEY = 'callback.save.v1';

// Opened straight from a file, a browser gives the page an opaque origin and
// no storage. The game still runs; it just cannot remember. Say so once rather
// than swallowing every write and letting someone lose a forty-year career.
const storageWorks = (() => {
  try {
    localStorage.setItem('callback.probe', '1');
    localStorage.removeItem('callback.probe');
    return true;
  } catch { return false; }
})();

// Every mutating call goes through the journal, and the journal is the save.
function act(name, args = []) {
  const out = game.call(name, args);
  persist();
  return out;
}

// A handle for tooling: the screenshot pass and the save test drive the real
// game object rather than guessing at the DOM. Harmless in play.
function expose() {
  window.__callback = { get game() { return game; }, screens: { screenQuarter, screenYearSummary } };
}

function persist() {
  try { localStorage.setItem(SAVE_KEY, JSON.stringify(game.save())); } catch { /* full or blocked */ }
}

function storedSave() {
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function clearSave() {
  try { localStorage.removeItem(SAVE_KEY); } catch { /* nothing to do */ }
}

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
// DOM append() turns a null child into the string "null", so everything that
// reaches the page goes through here.
const put = (...kids) => stage.append(...kids.filter((k) => k != null));
const money = (m) => (Math.abs(m) >= 1 ? `$${m.toFixed(1)}M` : `$${Math.round(m * 1000)}K`);
// Box office is quoted the way the trades quote it: round numbers, and billions
// once a picture gets there.
const boxOffice = (m) => (m >= 1000 ? `$${(m / 1000).toFixed(2)}B`
  : m >= 10 ? `$${m.toFixed(0)}M` : `$${m.toFixed(1)}M`);
const count = (n, one, many) => `${n} ${n === 1 ? one : many || `${one}s`}`;
const genreName = (g) => GENRE_NAMES[g] || g;
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
  document.getElementById('hud-quote').textContent = `asking price ${money(a.quote)}`;
  document.getElementById('hud-money').textContent =
    `${money(game.money.net)} banked · ${money(game.money.lifetime)} lifetime`;

  const log = document.getElementById('log');
  log.replaceChildren(...game.log.slice(-16).reverse().map(
    (e) => el('li', { class: e.kind }, `${e.year} · ${e.text}`),
  ));
  drawState();
}

// Standing is a summary of the four HUD meters (net of scandal) — shown here
// as a plain-English rung on a ladder, not a fifth unexplained number sitting
// next to Heat/Prestige/Affection/Notoriety.
function standingLabel(v) {
  if (v < 20) return 'just getting started';
  if (v < 40) return 'a working actor';
  if (v < 60) return 'someone with a name';
  if (v < 80) return 'a name people bid for';
  return 'the industry front page';
}

function legibilityLabel(v) {
  if (v < 36) return 'hard to place, which cuts both ways';
  if (v > 70) return 'typecast';
  return 'known for a few things';
}

// Coherence is how much the six axes above agree with each other — a
// number, not a judgement, but it reads as one: a film that knows what it
// is versus one that is still deciding. Below 40 the "nearest shape" is not
// meaningfully close to anything, so the sentence stops naming one.
function filmDescription(director, coh, shapeName) {
  if (coh.value > 65) {
    return `${director.name} is shooting something very much like ${shapeName}. `
      + `Coherence ${coh.value.toFixed(0)} — it knows exactly what it is.`;
  }
  if (coh.value > 40) {
    return `${director.name} is shooting something loosely in the shape of ${shapeName}. `
      + `Coherence ${coh.value.toFixed(0)} — it mostly holds together.`;
  }
  return `${director.name} is shooting something that has not settled into a shape yet. `
    + `Coherence ${coh.value.toFixed(0)} — a mess or a landmark, and you will not know which until it is out.`;
}

// The quiet panel: everything you are carrying, none of it demanding anything.
function drawState() {
  const box = document.getElementById('state');
  if (!box) return;
  const g = game;
  const amb = g.ambitionReport();
  const bits = [
    ['Ambition', amb.value === '—'
      ? `${amb.label} — too early to say`
      : `${amb.label} — ${amb.value} (${amb.grade.toLowerCase()})`],
    ['Standing', `${g.standing.toFixed(0)} — ${standingLabel(g.standing)}`],
    ['Legibility', `${g.legibility.toFixed(0)} — ${legibilityLabel(g.legibility)}`],
    ['Favours owed you', g.favours.toFixed(0)],
    g.scarcity > 0
      ? ['Staying away', g.scarcity > 24 ? 'they are starting to miss you' : 'noticed, not yet missed']
      : null,
    g.franchise && !g.franchise.writtenOut
      ? ['The franchise', `${g.franchise.title} — ${g.franchise.identification > 55 ? 'you are the reason it works'
        : g.franchise.identification > 25 ? 'you are becoming the face of it' : 'one credit in, so far'}`] : null,
    g.approvals.size
      ? ['What you can veto', [...g.approvals].map((k) => APPROVAL_LABELS[k] || k).join('; ')] : null,
    g.positions.size
      ? ['Seats you hold', [...g.positions].map((k) => CAREER_POSITION_LABELS[k] || k).join(', ')] : null,
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
        const res = act('do', [action.id, Game.ctxRef(ctx)]);
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

// What a position on a dial reads as, in words rather than numbers. Craft
// knowledge — it tells you what the choice IS, never what the outcome will be.
function readsAs(dial, pos, genre) {
  const [forYou, forFilm] = READ[dial][pos];
  const weight = (GENRE_DIAL_WEIGHT[genre] || {})[dial] ?? 1;
  const mine = forYou * weight;
  const noun = {
    energy: ['still', 'kinetic'], volume: ['quiet', 'loud'],
    warmth: ['cold', 'warm'], speed: ['slow', 'quick'],
  }[dial];
  const phrases = {
    with: 'part of the texture',
    beneath: `the ${noun[0]} inside it`,
    beyond: `the most ${noun[1]} thing on screen`,
    against: 'counterpoint — the thing they quote',
  };
  const you = mine > 3.2 ? 'memorable' : mine > 1.8 ? 'noticed' : 'invisible';
  const film = forFilm > 0.8 ? 'helps the film' : forFilm < -0.4 ? 'costs the film' : 'neutral for the film';
  return `${phrases[pos]} — ${you}, ${film}`;
}

// A dailies line for the scene just shot — pure and client-side, so it costs
// nothing to compute a preview between two scenes that have not happened yet
// as far as the engine (and the save file) are concerned. Called once per
// scene and cached (see nextScene), never on every render, so the room does
// not change its mind about you every time you touch a dial.
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];
function dailiesLine(pos, role) {
  const resolved = M.resolvePositions(pos, {
    genre: role.genre, craft: game.actor.attrs.craft, directorCommand: role.director.command,
  });
  if (resolved.overspend > 0.4) return pick([
    `${role.director.name} watched the playback twice. That is a lot of scene.`,
    `Someone on the crew laughed at the monitor. Not unkindly. Not entirely kindly either.`,
    `${role.director.name} said "interesting" in the tone that means they are not sure yet.`,
  ]);
  if (resolved.forFilm > resolved.forYou + 1) return pick([
    'That one served the picture. Nobody will mention your name for it.',
    'Good day for the film. Quiet day for you.',
    `${role.director.name} moved on fast. That is what it looks like when something just works.`,
  ]);
  if (resolved.forYou > 3) return pick([
    'That take is going in the reel.',
    `${role.director.name} watched it back twice, then said "keep that."`,
    'Somebody on set clapped. That almost never happens.',
  ]);
  return pick([
    'A clean take. On to the next one.',
    'Nothing remarkable. The schedule holds.',
    'Professional, unremarkable, over by lunch.',
  ]);
}

function currencyBars(resolved) {
  const bar = (label, value, max, cls) => el('div', { class: 'currency' },
    el('span', {}, label),
    el('div', { class: 'track' },
      el('i', { class: cls, style: `width:${clampPct(value, max)}%` })),
  );
  return el('div', { class: 'currencies' },
    bar('for your reviews', resolved.forYou, 18, 'you'),
    bar('for the film', resolved.forFilm, 8, 'film'),
  );
}
const clampPct = (v, max) => Math.max(2, Math.min(100, (v / max) * 100));

// ---------------------------------------------------------------------------
// 1. character creation
// ---------------------------------------------------------------------------
function screenCreate() {
  clear();
  hud.hidden = true;
  ledger.hidden = true;
  let picked = 'conservatory';
  let ambition = 'work';
  const saved = storedSave();

  const render = () => {
    clear();
    put(
      el('h1', {}, 'Callback'),
      el('p', { class: 'lede' },
        'You are an actor. The work is the game: what you take, how you play it, and what the '
        + 'industry decides that means. Nobody will ever tell you how good you were.'),
      storageWorks ? null : el('div', { class: 'card' },
        el('h4', {}, 'This copy cannot save'),
        el('p', { class: 'why' },
          'You opened the file directly, so the browser has given the page no storage. '
          + 'The game plays fine — it just will not remember the career when you close the tab. '
          + 'Open the hosted link instead if you want to keep one.')),
      saved ? el('div', { class: 'card pick', onclick: () => resume(saved) },
        el('h4', {}, 'Carry on with the career you were having'),
        el('div', { class: 'meta' },
          `${saved.name || 'unnamed'} · ${saved.journal.length} decisions so far`),
        el('p', { class: 'why' }, 'Picks up exactly where you left it.')) : null,
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
        el('div', { class: 'meta' }, `measured by ${a.measure.replace(/,$/, '')}`),
      ))),
    );

    const nameInput = el('input', { placeholder: 'a name, or leave it blank', class: 'text' });
    const seedInput = el('input', { placeholder: 'seed', class: 'text short' });
    put(
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
          persist();
          expose();
          screenQuarter();
        },
      }, 'Start working')),
    );
  };
  render();
}

function resume(saved) {
  try {
    game = Game.load(saved);
    expose();
    game.say('You pick it up where you left it.', 'note');
    if (game.over) return screenObituary();
    screenQuarter(game.board.length === 0);
  } catch (err) {
    console.warn('save could not be replayed', err);
    clearSave();
    screenCreate();
  }
}

// ---------------------------------------------------------------------------
// 2. the quarter — the board, and the moves menu beside it
// ---------------------------------------------------------------------------
function screenQuarter(fresh = true, flash = null) {
  if (game.over) return screenObituary();
  if (fresh) act('openBoard');
  drawHud();
  clear();
  const board = game.board;

  const firstEver = !game.credits.length && !game.turnedDown.length && game.year === game.world.startYear;
  put(
    el('h2', {}, `${game.year} · ${quarterName(game.quarter)}`),
    flash ? el('p', { class: 'flash' }, flash) : null,
    firstEver ? el('div', { class: 'card intro' },
      el('p', {}, 'Your year is four blocks. Everything you take costs some of them, '
        + 'so the two things you want are always in the same months.'),
      el('p', {}, 'Read for something, pass on it, or open the moves menu below and '
        + 'make something happen that was not going to. Nothing down there is ever '
        + 'required — the game will not ask you for it and will not punish you for '
        + 'ignoring it.')) : null,
    el('p', { class: 'lede' }, boardMood(board)),
  );

  if (game.hiatus) {
    put(el('div', { class: 'card' }, el('p', {},
      'You are not working. Nobody is being told why. '
      + `Scarcity ${game.scarcity.toFixed(0)} of 40.`)));
  } else if (!board.length) {
    put(el('div', { class: 'card' }, el('p', {},
      'Nothing this quarter. Your agent says it is quiet everywhere, which is what agents say.')));
  }

  for (const r of board) {
    const noDates = game.blocksBooked + r.blocks > 4;
    const locked = r.union && game.actor.unionCredits < 3;
    const advice = ambitionAdvice(game, r);
    put(el('div', { class: 'card' },
      el('h4', {}, r.title),
      el('div', { class: 'meta' },
        `${r.billing} · ${genreName(r.genre)} · ${r.label} · $${r.budget.toFixed(0)}M · `
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
        r.unknownLead ? el('span', { class: 'tag hot' }, 'they want an unknown — five-picture deal') : null,
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
        el('button', { onclick: () => { act('decline', [r.id]); screenQuarter(false, 'Passed.'); } }, 'Pass'),
        el('button', {
          onclick: () => screenMoves({ role: r }, `About ${r.title}`),
        }, 'Do something about it'),
      ),
    ));
  }

  put(
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
  return `${r.archetype.replace(/_/g, ' ')} in a ${genreName(r.genre)} picture. ${r.director.name} is ${tone}. `
    + `Script reads ${r.scriptQuality > 72 ? 'genuinely good' : r.scriptQuality > 55 ? 'competent' : 'thin'}.`;
}

// A moves screen scoped to one thing (a listing, or the project you are on).
function screenMoves(ctx, title) {
  clear();
  drawHud();
  put(
    el('h2', {}, title),
    el('p', { class: 'lede' }, 'Nothing here is required. Nothing here will ever be asked of you.'),
    movesPanel(ctx, (text) => screenMoves(ctx, title)),
    el('button', { class: 'primary', onclick: () => (ctx.current ? screenPrep() : screenQuarter(false)) },
      'Back'),
  );
}

function attempt(role) {
  const res = act('pursue', [role.id]);
  drawHud();
  if (!res.cast) {
    clear();
    put(
      el('h2', {}, role.title),
      el('p', { class: 'lede' }, res.note || 'They went another way. You will not be told why.'),
      el('button', { class: 'primary', onclick: () => screenQuarter(false) }, 'Back to the board'),
    );
    return;
  }
  choice = {
    role, prep: game.standingOrders.prep, positions: null,
    scenePositions: null, sceneIndex: 0, moments: {},
    momentSet: null, momentIndex: 0, dailyNotes: [],
  };
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
  put(
    el('h2', {}, `You are doing ${r.title}`),
    el('p', { class: 'lede' },
      `${r.billing === 'lead' ? 'Above the title.' : r.billing === 'supporting' ? 'Fourth on the call sheet.' : 'Two scenes.'} `
      + `${r.blocks} block${r.blocks > 1 ? 's' : ''}, ${money(r.budgetForRole)} in the role's budget.`),
    el('h3', { class: 'section' }, 'This one is worth thinking about'),
  );
  for (const [key, p] of Object.entries(PREP_OPTIONS)) {
    put(el('div', {
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
  put(el('div', { class: 'row' },
    el('button', { class: 'primary', onclick: () => screenFilm() }, 'To the set'),
    el('button', { onclick: () => screenMoves({ current: r }, `Before you shoot ${r.title}`) },
      'Do something about the project'),
  ));
}

// ---------------------------------------------------------------------------
// 4. the film, and the three scenes you actually play against it
// ---------------------------------------------------------------------------
function screenFilm(note) {
  const r = choice.role;
  if (!choice.palette) choice.palette = act('filmFor', [r.id]).palette;
  const coh = M.coherence(choice.palette);
  // Decided once, here, and carried through to the final act('shoot', ...)
  // call below — so whatever the crew's day turns out to involve is fixed
  // the moment you start the shoot, not re-rolled behind your back the
  // moment you finish it.
  if (!choice.momentSet) choice.momentSet = game.momentsFor(r);
  if (!game.shouldAskStance(r, { coherence: coh.value })) {
    choice.positions = game.autoPositions(r);
    return resolveShoot(note);
  }
  game.countPush('stance');
  if (!choice.scenePositions) choice.scenePositions = [null, null, null];
  choice.sceneIndex = 0;
  screenScene(note);
}

function screenScene(note) {
  const r = choice.role;
  const i = choice.sceneIndex;
  const coh = M.coherence(choice.palette);
  if (!choice.scenePositions[i]) {
    // Carry the last scene's read forward as the starting point — a real
    // choice each time, not a blank form three times over.
    choice.scenePositions[i] = i === 0 ? game.autoPositions(r) : { ...choice.scenePositions[i - 1] };
  }
  const pos = choice.scenePositions[i];

  clear();
  drawHud();
  const budget = M.contrastBudget(game.actor.attrs.craft, r.director.command);
  const points = Math.max(1, Math.round(budget));
  const spent = PERF_DIALS.reduce((a, d) => a + POSITION_COST[pos[d]], 0);

  put(
    i === 0 && note ? el('p', { class: 'flash' }, note) : null,
    i > 0 && choice.dailyNotes[i - 1] ? el('p', { class: 'flash' }, choice.dailyNotes[i - 1]) : null,
    el('h2', {}, SCENE_LABELS[i]),
    el('div', { class: 'scene-progress' }, [0, 1, 2].map((n) => el('span', {
      class: n === i ? 'on' : n < i ? 'done' : '',
    }))),
  );
  if (i === 0) {
    const shapeName = SHAPE_LABELS[coh.nearest] || coh.nearest.replace(/_/g, ' ');
    put(
      el('p', { class: 'lede' }, filmDescription(r.director, coh, shapeName)),
      el('p', { class: 'why' },
        'This is the film itself, not something you choose — six things true about it before '
        + 'you ever walk on set, and what you play against on the next screen.'),
      el('div', { class: 'palette' }, DIALS.flatMap((d) => [
        el('div', { class: 'l' }, DIAL_LABELS[d][0]),
        el('div', { class: 'track', title: DIAL_AXIS_LABELS[d] },
          el('i', { style: `left:${((choice.palette[d] + 50) / 100) * 100}%` })),
        el('div', { class: 'r' }, DIAL_LABELS[d][1]),
      ])),
    );
  }
  put(
    el('h3', { class: 'section' }, 'How you play it'),
    el('p', {},
      'Four small decisions, and none of them are free. Match the scene, and it disappears into '
      + 'the film. Hold back, and it becomes the stillness people remember. Go big, and it is '
      + 'yours on the day but may not survive the cut. Play against it, and you are betting the '
      + 'room agrees with you before they do. Spend past what the day can carry and it stops '
      + 'reading as choices — it reads as trying too hard.'),
  );

  const table = el('table', { class: 'dials' });
  for (const d of PERF_DIALS) {
    table.append(el('tr', {},
      el('td', { title: PERF_DIAL_HINTS[d] }, PERF_DIAL_LABELS[d]),
      el('td', {},
        el('div', {}, POSITIONS.map((p) => el('button', {
          class: pos[d] === p ? 'selected' : '',
          title: `${POSITION_HINTS[p]} (${POSITION_COST[p]} point${POSITION_COST[p] === 1 ? '' : 's'})`,
          onclick: () => { pos[d] = p; screenScene(); },
        }, POSITION_LABELS[p]))),
        el('div', { class: 'reads' }, readsAs(d, pos[d], r.genre)),
      ),
    ));
  }
  const resolved = M.resolvePositions(pos, {
    genre: r.genre,
    craft: game.actor.attrs.craft,
    directorCommand: r.director.command,
  });
  put(table,
    currencyBars(resolved),
    el('div', { class: `budgetline${spent > budget ? ' over' : ''}` },
      spent > budget
        ? `You are carrying more than this scene can hold (${spent} of about ${points}) — it will read as mannered, not bold.`
        : `About ${points} point${points === 1 ? '' : 's'} of room this scene, ${spent} spent.`),
    el('div', { class: 'row' },
      el('button', { class: 'primary', onclick: () => nextScene() }, i < 2 ? 'Shoot the scene' : 'Wrap the shoot'),
      el('button', { onclick: () => screenMoves({ current: r }, `Before you shoot ${r.title}`) },
        'Do something about the project'),
    ));
}

// A scene wraps, the crew reacts (cached, not re-rolled — see dailiesLine),
// and whatever the shoot still owes you in the way of moments — a stunt, a
// late costar, a rewrite pushed under the trailer door — happens in the gap
// before the next one, the way it actually would on a real set, rather than
// all landing in a pile after the last take.
function nextScene() {
  const r = choice.role;
  choice.dailyNotes[choice.sceneIndex] = dailiesLine(choice.scenePositions[choice.sceneIndex], r);
  const advance = () => {
    if (choice.sceneIndex < 2) { choice.sceneIndex += 1; screenScene(); }
    else resolveShoot();
  };
  showNextMoment(advance);
}

// ---------------------------------------------------------------------------
// 5. the moments that still fire — interleaved with the scenes above when
// there is more than one to interleave with, otherwise shown back to back.
// ---------------------------------------------------------------------------
function resolveShoot(note) {
  if (!choice.momentSet) choice.momentSet = game.momentsFor(choice.role);
  showNextMoment(() => finishShoot(note), note);
}

// Shows exactly one moment from choice.momentSet, starting from
// choice.momentIndex, then calls onDone — or calls onDone immediately if
// none are left. The veteran path (auto positions, no scenes shown) walks
// the whole set this way in one pass; the interactive path calls it once
// per scene boundary, so the same pool of moments reads as things that
// happened *during* the shoot instead of a debrief after it.
function showNextMoment(onDone, note) {
  const list = choice.momentSet || [];
  const i = choice.momentIndex;
  if (i >= list.length) return onDone();
  clear();
  drawHud();
  game.countPush('moment');
  const m = list[i];
  put(
    note && i === 0 ? el('p', { class: 'flash' }, note) : null,
    el('h2', {}, choice.role.title),
    el('p', { class: 'lede' }, m.prompt),
  );
  for (const opt of m.options) {
    put(el('div', {
      class: 'card pick',
      onclick: () => { choice.moments[m.id] = opt.id; choice.momentIndex += 1; onDone(); },
    }, el('h4', {}, opt.label)));
  }
}

function finishShoot(note) {
  const project = act('shoot', [{
    prep: choice.prep,
    positions: choice.positions,
    scenePositions: choice.scenePositions || undefined,
    momentSet: choice.momentSet || undefined,
    moments: choice.moments,
  }]);
  drawHud();
  clear();
  const unasked = project.momentLog.filter((m) => !m.asked);
  put(
    note ? el('p', { class: 'flash' }, note) : null,
    el('h2', {}, `${choice.role.title} wrapped`),
    el('p', { class: 'lede' }, game.log.filter((l) => l.kind === 'work').slice(-1)[0]?.text || ''),
    choice.dailyNotes.length ? el('div', { class: 'attrib' },
      ...choice.dailyNotes.map((n, i) => el('div', {}, `${SCENE_LABELS[i]}: ${n}`))) : null,
    el('div', { class: 'attrib' },
      el('div', {}, project.readConfidence),
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
  const cards = act('tickPending');
  act('tickQuarter');
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
  put(
    el('h2', {}, `${c.project.role.title} is out`),
    el('p', { class: 'lede' }, c.headline),
    el('div', { class: 'tags' },
      el('span', { class: `tag ${rec.filmCritic > 66 ? 'good' : rec.filmCritic < 45 ? 'warn' : ''}` }, `critics ${rec.filmCritic.toFixed(0)}`),
      el('span', { class: `tag ${rec.notices > 66 ? 'good' : rec.notices < 45 ? 'warn' : ''}` }, `your notices ${rec.notices.toFixed(0)}`),
      el('span', { class: 'tag' }, `audience ${rec.audience.toFixed(0)}`),
      el('span', { class: `tag ${rec.roi > 1.4 ? 'hot' : rec.roi < 0.8 ? 'warn' : ''}` }, `roi ${rec.roi.toFixed(2)}`),
      el('span', { class: `tag ${rec.roi > 1.4 ? 'hot' : rec.roi < 0.8 ? 'warn' : ''}` },
        `box office ${boxOffice(rec.gross * (c.project.role.era ?? 1))}`),
    ),
    el('div', { class: 'attrib' }, el('div', {}, boxOfficeLine(c))),
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

// The trades number, and the figure it had to clear. Break-even is the budget
// plus prints and advertising, against the share of the gross that comes back —
// which is why a picture can take twice what it cost and still be spoken of as
// a disappointment. Both terms come from the model, not from here.
function boxOfficeLine(c) {
  const { rec } = c;
  const era = c.project.role.era || 1;
  const breakEven = M.breakEven(c.project.role.budget);
  const aside = rec.legs > 3.2 ? ' — word of mouth did that, not the opening'
    : rec.legs < 1.6 ? ' — everyone who was ever going to see it went the first weekend'
      : '';
  return `Opened to ${boxOffice(rec.opening * era)}, played ${rec.legs.toFixed(1)}× that, `
    + `finished at ${boxOffice(rec.gross * era)}${aside}. `
    + `It needed about ${boxOffice(breakEven)} to break even.`;
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
  put(
    el('h2', {}, 'Awards season'),
    el('p', { class: 'lede' }, `They are talking about ${contenders}. Talk is the whole mechanism.`),
    movesPanel({}, () => screenSeason(before)),
    el('button', { class: 'primary', onclick: () => finishYear(before) }, 'Let the season happen'),
  );
}

function finishYear(before) {
  act('endYear');
  drawHud();
  if (game.over) return screenObituary();
  const event = game.rollEvent();
  if (event) return screenLifeEvent(event, before);
  screenYearSummary(before);
}

// One a year at most, and only because something in your life caused it —
// either a one-shot, or the next scene of an arc that has been building.
function screenLifeEvent(event, before) {
  clear();
  drawHud();
  const arc = event.kind === 'arc' ? ARCS_BY_ID[event.id] : null;
  put(
    el('h2', {}, `${game.year}`),
    arc ? el('div', { class: 'meta' }, arc.label) : null,
    el('p', { class: 'lede' }, event.prompt),
  );
  event.options.forEach((label, i) => {
    put(el('div', {
      class: 'card pick',
      onclick: () => {
        const res = act('event', [i]);
        drawHud();
        screenYearSummary(before, res && res.text);
      },
    }, el('h4', {}, label)));
  });
}

// What the season did, said as a scene rather than a log line.
function seasonCard() {
  const season = game.lastSeason;
  if (!season || !season.contenders) return null;
  const { results, contenders, spent } = season;
  const won = results.filter((r) => r.won);
  const nominated = results.filter((r) => !r.won);
  const lines = [];
  if (!results.length) {
    lines.push(contenders === 1
      ? 'One eligible performance and no nominations. The season happened to other people.'
      : `${contenders} eligible performances and nothing came of any of them.`);
  }
  for (const r of won) {
    lines.push(`You won, for ${r.title}${r.category === 'supporting' ? ', in supporting' : ''}.`
      + (r.narratives.length ? ` The story they told about it: ${r.narratives.join('; ').toLowerCase()}.` : ''));
  }
  for (const r of nominated) {
    lines.push(`Nominated for ${r.title}${r.category === 'supporting' ? ', in supporting' : ''}.`
      + (r.rival ? ` ${r.rival} won it.` : ''));
  }
  if (spent > 0) lines.push(`You spent $${spent.toFixed(1)}M of your own money on the campaign.`);
  return el('div', {}, [
    el('h3', { class: 'section' }, 'The season'),
    el('div', { class: 'card trades' }, lines.map((t) => el('p', {}, t))),
  ]);
}

function screenYearSummary(before, flash) {
  clear();
  const a = game.actor;
  put(
    flash ? el('p', { class: 'flash' }, flash) : null,
    el('h2', {}, `${game.year - 1} is over`),
    el('div', { class: 'attrib' },
      el('div', {}, `You are ${a.age}. Heat fell to ${a.standing.heat.toFixed(0)} from ${before.heat.toFixed(0)} — it always does.`),
      el('div', {}, `Legibility ${game.legibility.toFixed(0)} — ${
        game.legibility < 36 ? 'casting directors still do not know what you are.'
          : game.legibility > 70 ? 'everyone knows exactly what you are, which is a floor and a ceiling.'
          : 'known for two or three things. The healthy place.'}`),
      el('div', {}, `Standing ${game.standing.toFixed(0)} · recognition ${a.recognition.toFixed(0)} · `
        + `${count(a.unionCredits, 'union credit')} · ${count(game.favours, 'favour')} owed you`),
      el('div', {}, `${money(game.money.net)} banked. Your life costs ${money(game.money.floor)} a year now.`),
      a.health < 60 ? el('div', {}, 'Your body is keeping a list.') : null,
    ),
    seasonCard(),
    el('h3', { class: 'section' }, 'The trades'),
    el('div', { class: 'card trades' }, game.tradePaper().map((t) => el('p', {}, t))),
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
  put(
    el('h2', {}, 'The Rolodex'),
    el('p', { class: 'lede' },
      'Eight people, chosen by how much they matter rather than by you maintaining a list. '
      + 'Everyone else is real and quiet.'),
  );
  if (!tracked.length) {
    put(el('div', { class: 'card' }, el('p', {}, 'You do not know anybody yet.')));
  }
  for (const e of tracked) {
    put(el('div', { class: 'card' },
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
  put(el('button', { class: 'primary', onclick: () => screenQuarter(false) }, 'Back'));
}

function screenOrders() {
  clear();
  drawHud();
  const o = game.standingOrders;
  const set = (k, v) => { act('orders', [{ [k]: v }]); screenOrders(); };
  const group = (label, key, options, blurb) => el('div', { class: 'card' },
    el('h4', {}, label),
    el('p', { class: 'why' }, blurb),
    el('div', { class: 'row' }, options.map(([v, text]) => el('button', {
      class: o[key] === v ? 'selected' : '',
      onclick: () => set(key, v),
    }, text))),
  );
  put(
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
  put(
    el('h2', {}, game.actor.name),
    el('div', { class: 'obit' }, lines.map((l) => el('p', {}, l))),
    el('h3', { class: 'section' }, 'The credits'),
    el('div', { class: 'card' }, game.credits.length
      ? game.credits.map((c) => el('div', { class: 'meta' },
        `${c.year}  ${c.title} — ${c.billing}, ${genreName(c.genre)}`
        + (c.gross != null ? ` · ${boxOffice(c.gross)}` : c.year < game.year ? ' · unreleased' : '')))
      : el('p', {}, 'None.')),
    game.turnedDown.length ? el('h3', { class: 'section' }, 'And what they passed on') : null,
    game.turnedDown.length
      ? el('div', { class: 'card' }, game.turnedDown.slice(-12).map(
        (c) => el('div', { class: 'meta' }, `${c.year}  ${c.title} — ${c.billing}, $${c.budget.toFixed(0)}M, ${c.director}`)))
      : null,
    el('div', { style: 'margin-top:20px' },
      el('button', {
        class: 'primary',
        onclick: () => { clearSave(); game = null; screenCreate(); },
      }, 'Again')),
  );
}

// Enter does the obvious thing on every screen.
document.addEventListener('keydown', (e) => {
  if (e.key !== 'Enter' || e.target.tagName === 'INPUT') return;
  const primary = stage.querySelector('button.primary:not([disabled])');
  if (primary) { e.preventDefault(); primary.click(); }
});

screenCreate();
