// Save verification in the real page: play a while, reload, continue, and
// check the career is byte-for-byte the same one.
//
//   node callback/sim/save-test.mjs

import { chromium } from 'playwright';

const URL = process.env.CALLBACK_URL || 'http://localhost:8777/callback/web/index.html';
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || '/opt/pw-browsers/chromium',
});
const page = await browser.newPage();
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));

await page.goto(URL);
await page.click('text=Start working');

// Play a few dozen clicks.
for (let i = 0; i < 120; i++) {
  const buttons = [];
  for (const b of await page.$$('button')) if (await b.isEnabled()) buttons.push(b);
  const prim = buttons.find(async () => true);
  const primary = await page.$('button.primary');
  if (primary && await primary.isEnabled()) await primary.click();
  else {
    const adv = await page.$('button:has-text("Let the quarter go by")');
    if (adv) await adv.click(); else if (buttons.length) await buttons[0].click();
  }
  void prim;
  await page.waitForTimeout(2);
}

const before = await page.evaluate(() => JSON.parse(localStorage.getItem('callback.save.v1')));
const hudBefore = await page.textContent('#hud-when');
const nameBefore = await page.textContent('#hud-name');

await page.reload();
const continueCard = await page.$('text=Carry on with the career you were having');
if (!continueCard) {
  console.log('<<< no continue option after reload');
  await browser.close();
  process.exit(1);
}
await continueCard.click();
await page.waitForTimeout(300);

const after = await page.evaluate(() => JSON.parse(localStorage.getItem('callback.save.v1')));
const hudAfter = await page.textContent('#hud-when');
const nameAfter = await page.textContent('#hud-name');

// Resuming can legitimately append (re-opening the board, say). The invariant
// is that everything the save recorded is still there, unchanged, in order.
const prefix = after.journal.slice(0, before.journal.length);
const sameJournal = JSON.stringify(before.journal) === JSON.stringify(prefix);
const sameWhen = hudBefore === hudAfter;
const sameWho = nameBefore === nameAfter;

console.log('journal length %d', before.journal.length);
console.log('  saved history intact after reload: %s (%d -> %d calls)',
  sameJournal, before.journal.length, after.journal.length);
console.log('  same actor: %s (%s)', sameWho, nameAfter);
console.log('  same point in time: %s (%s)', sameWhen, hudAfter);
console.log('  page errors: %d', errors.length);
for (const e of errors.slice(0, 4)) console.log('   ', e);

await browser.close();
process.exitCode = sameJournal && sameWhen && sameWho && !errors.length ? 0 : 1;
