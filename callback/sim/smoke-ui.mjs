// Headless play-through of the web UI: starts a career, clicks through several
// hundred screens at random, and fails on any console error or if a full career
// never reaches the obituary.
//
//   python3 -m http.server 8777      # from the repo root, in another shell
//   node callback/sim/smoke-ui.mjs
//
// Requires the playwright devDependency; uses the preinstalled Chromium.

import { chromium } from 'playwright';

// Deterministic wander, so a failure is reproducible.
let seed = Number(process.env.SEED || 7) >>> 0;
const rand = () => {
  seed = (seed + 0x6d2b79f5) >>> 0;
  let t = seed;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

const URL = process.env.CALLBACK_URL || 'http://localhost:8777/callback/web/index.html';
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || '/opt/pw-browsers/chromium',
});
const page = await browser.newPage();

const errors = [];
page.on('console', (m) => {
  if (m.type() === 'error' && !m.text().includes('404')) errors.push(m.text());
});
page.on('pageerror', (e) => errors.push(`PAGEERROR: ${e.message}`));

await page.goto(URL);
await page.click('text=Start working');
await page.waitForTimeout(200);

let reachedObituary = false;
const screens = new Set();

const MAX_CLICKS = Number(process.env.CLICKS || 2000);
for (let i = 0; i < MAX_CLICKS && !reachedObituary; i++) {
  const h2 = (await page.textContent('h2').catch(() => '')) || '';
  screens.add(h2.trim().slice(0, 18));
  if (process.env.TRACE) console.log(i, h2.trim().slice(0, 40));
  if (await page.$('text=The credits')) reachedObituary = true;

  const cards = await page.$$('.card.pick');
  const buttons = [];
  for (const b of await page.$$('button')) {
    if (await b.isEnabled()) buttons.push(b);
  }
  // Mostly drive forward; sometimes wander into a card or a side screen, which
  // is how the pull layer gets exercised.
  // Side screens (orders, Rolodex, a moves list) are dead ends by design: a
  // random walker will sit in them forever, so leave them promptly.
  const sideScreen = /^(Standing orders|The Rolodex|About |Awards season)/.test(h2.trim())
    || h2.trim() === '' || /^[A-Z][a-z]+ [A-Z]/.test(h2.trim());
  // Wander a third of the time; otherwise drive the career forward.
  const roll = sideScreen ? 0.95 : rand();
  if (cards.length && roll < 0.35) {
    await cards[Math.floor(rand() * cards.length)].click();
  } else if (buttons.length && roll < 0.55) {
    await buttons[Math.floor(rand() * buttons.length)].click();
  } else {
    let clicked = false;
    for (const b of buttons) {
      const cls = await b.getAttribute('class');
      if (cls && cls.includes('primary')) { await b.click(); clicked = true; break; }
    }
    if (!clicked) {
      // Always able to move time forward, whatever else is on screen.
      const advance = await page.$('button:has-text("Let the quarter go by")');
      if (advance) await advance.click();
      else if (buttons.length) await buttons[buttons.length - 1].click();
      else if (cards.length) await cards[0].click();
    }
  }
  await page.waitForTimeout(2);
}

console.log('screens visited: %d | reached obituary: %s | console errors: %d',
  screens.size, reachedObituary, errors.length);
for (const e of errors.slice(0, 8)) console.log('  ', e);

await browser.close();
process.exitCode = errors.length === 0 && reachedObituary ? 0 : 1;
