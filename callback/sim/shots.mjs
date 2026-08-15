// Screenshot pass over the main screens, for looking at the thing.
//   node callback/sim/shots.mjs [outdir]
import { chromium } from 'playwright';
import { mkdirSync } from 'fs';

const out = process.argv[2] || '/tmp/shots';
mkdirSync(out, { recursive: true });
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const p = await b.newPage({ viewport: { width: 1280, height: 950 } });
const shot = (n) => p.screenshot({ path: `${out}/${n}.png`, fullPage: true });

await p.goto('http://localhost:8777/callback/web/index.html');
await shot('01-create');
await p.click('text=Start working');
await p.waitForTimeout(200);
await shot('02-board');

// Walk forward until we hit each interesting screen once.
const want = new Set(['film', 'release', 'yearend', 'event', 'obit']);
for (let i = 0; i < 900 && want.size; i++) {
  const h2 = ((await p.textContent('h2').catch(() => '')) || '').trim();
  if (want.has('film') && h2.startsWith('The film they are making')) { await shot('04-film'); want.delete('film'); }
  if (want.has('release') && h2.endsWith('is out')) { await shot('05-release'); want.delete('release'); }
  if (want.has('yearend') && /is over$/.test(h2)) { await shot('06-yearend'); want.delete('yearend'); }
  if (want.has('event') && /^\d{4}$/.test(h2)) { await shot('09-event'); want.delete('event'); }
  if (want.has('obit') && (await p.$('text=The credits'))) { await shot('10-obituary'); want.delete('obit'); }
  const prim = await p.$('button.primary');
  const cards = await p.$$('.card.pick');
  if (cards.length && i % 3 === 0) await cards[0].click();
  else if (prim && await prim.isEnabled()) await prim.click();
  else {
    const adv = await p.$('button:has-text("Let the quarter go by")');
    if (adv) await adv.click();
  }
  await p.waitForTimeout(4);
}
// A year with a season in it, and the side screens.
for (let i = 0; i < 600; i++) {
  const h2 = ((await p.textContent('h2').catch(() => '')) || '').trim();
  if (/is over$/.test(h2) && (await p.$('text=The season'))) { await shot('11-season'); break; }
  const prim = await p.$('button.primary');
  if (prim && await prim.isEnabled()) await prim.click();
  else {
    const adv = await p.$('button:has-text("Let the quarter go by")');
    if (adv) await adv.click(); else break;
  }
  await p.waitForTimeout(3);
}
const rolo = await p.$('button:has-text("The Rolodex")');
if (rolo) { await rolo.click(); await p.waitForTimeout(80); await shot('07-rolodex'); await p.click('button.primary'); }
const ord = await p.$('button:has-text("Standing orders")');
if (ord) { await ord.click(); await p.waitForTimeout(80); await shot('08-orders'); }
// narrow layout
await p.setViewportSize({ width: 430, height: 900 });
await p.waitForTimeout(120);
await shot('12-mobile');
console.log('shots in', out);
await b.close();
