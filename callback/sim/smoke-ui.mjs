// Headless play-through of the web UI: starts a career, clicks through several
// hundred screens at random, and fails on any console error or if a full career
// never reaches the obituary.
//
//   python3 -m http.server 8777      # from the repo root, in another shell
//   node callback/sim/smoke-ui.mjs
//
// Requires the playwright devDependency; uses the preinstalled Chromium.

import { chromium } from 'playwright';

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

for (let i = 0; i < 600; i++) {
  const h2 = (await page.textContent('h2').catch(() => '')) || '';
  screens.add(h2.trim().slice(0, 18));
  if (await page.$('text=The credits')) reachedObituary = true;

  const onBoard = /^\d{4} ·/.test(h2.trim());
  const cards = await page.$$('.card.pick');
  if (onBoard && cards.length && Math.random() < 0.75) {
    await cards[Math.floor(Math.random() * cards.length)].click();
  } else {
    const primary = await page.$('button.primary');
    if (primary) await primary.click();
    else {
      const buttons = await page.$$('button');
      if (buttons.length) await buttons[buttons.length - 1].click();
      else if (cards.length) await cards[0].click();
    }
  }
  await page.waitForTimeout(4);
}

console.log('screens visited: %d | reached obituary: %s | console errors: %d',
  screens.size, reachedObituary, errors.length);
for (const e of errors.slice(0, 8)) console.log('  ', e);

await browser.close();
process.exitCode = errors.length === 0 && reachedObituary ? 0 : 1;
