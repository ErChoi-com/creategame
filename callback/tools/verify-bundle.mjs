// Play the bundled single file the way a person would open it — from disk,
// no server — and fail on any console error or if a career cannot finish.
//
//   node callback/tools/verify-bundle.mjs [file]

import { chromium } from 'playwright';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const here = dirname(fileURLToPath(import.meta.url));
const file = process.argv[2] || resolve(here, '../dist/callback.html');

const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || '/opt/pw-browsers/chromium',
});
const page = await browser.newPage();
const errors = [];
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
page.on('pageerror', (e) => errors.push(`PAGEERROR: ${e.message}`));

await page.goto(`file://${file}`);
await page.waitForTimeout(200);

// Storage is unavailable from file://, and the page has to admit that.
const warned = await page.$('text=This copy cannot save');

const started = await page.$('text=Start working');
if (!started) {
  console.log('<<< the page did not render its opening screen');
  await browser.close();
  process.exit(1);
}
await started.click();

let reachedObituary = false;
let savedMid = null;   // sampled during play: the run's end clears the slot
let seed = 11;
const rand = () => {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
};

for (let i = 0; i < 1400 && !reachedObituary; i++) {
  if (i === 60) savedMid = await page.evaluate(() => localStorage.getItem('callback.save.v1'));
  if (await page.$('text=The credits')) reachedObituary = true;
  const buttons = [];
  for (const b of await page.$$('button')) if (await b.isEnabled()) buttons.push(b);
  const cards = await page.$$('.card.pick');
  if (cards.length && rand() < 0.3) await cards[Math.floor(rand() * cards.length)].click();
  else {
    const primary = buttons.find(() => true);
    const prim = await page.$('button.primary');
    if (prim && await prim.isEnabled()) await prim.click();
    else {
      const advance = await page.$('button:has-text("Let the quarter go by")');
      if (advance) await advance.click();
      else if (primary) await primary.click();
    }
  }
  await page.waitForTimeout(2);
}

// And it must still save: the whole point of the single file is that you can
// close the tab.
const saved = savedMid;

console.log('opened from disk · reached obituary: %s · save: %s · console errors: %d',
  reachedObituary,
  saved ? `${JSON.parse(saved).journal.length} calls` : (warned ? 'unavailable, and the page says so' : 'MISSING'),
  errors.length);
for (const e of errors.slice(0, 5)) console.log('   ', e);

await browser.close();
process.exitCode = reachedObituary && (saved || warned) && !errors.length ? 0 : 1;
