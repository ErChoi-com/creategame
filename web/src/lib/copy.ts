// Player-facing copy: the words-not-numbers pass (callback/docs/ux/05). Session already hands over
// bands ("cold", "a runaway hit"). This file only turns them into sentences and adds film titles,
// which are presentation flavour and never feed back into the engine.
import type { Listing } from '../api';
import { STANDING_ORDER, STANDING_PHRASE } from './content';
import { npcName } from './names';

export const cap = (s: string) => (s ? s[0].toUpperCase() + s.slice(1) : s);
export const pretty = (key: string) => cap(key.replace(/_/g, ' '));

export function money(millions: number): string {
  if (millions <= 0) return '$0';
  if (millions < 1) return `$${Math.max(1, Math.round(millions * 1000))}K`;
  return `$${millions.toFixed(millions < 10 ? 1 : 0)}M`;
}

const GENRE_LABEL: Record<string, string> = { scifi: 'Sci-fi', superhero: 'Superhero', period: 'Period piece' };
export const genreLabel = (g: string | null | undefined) => (g ? GENRE_LABEL[g] ?? cap(g) : '');

export const billingLabel = (b: string) =>
  ({ lead: 'Lead', supporting: 'Supporting', bit: 'Bit part' } as Record<string, string>)[b] ?? cap(b);

/** ux/03 §1: one sentence of why this role reached you, keyed to what actually drove the offer. */
export function whyThisRole(o: Listing): string {
  if (o.guaranteed) return `${o.studio_name} owes you this one. It's in your deal.`;
  if (o.typecasting_note) return cap(o.typecasting_note.replace(/\.$/, '')) + '.';
  if (o.director.known && o.director.id) return `${npcName(o.director.id)} is directing, ${o.director.relationship ?? 'someone you know'}. They asked for you.`;
  if (o.installment_number >= 2) return `Installment ${o.installment_number} of ${o.franchise_scale}. The machine wants a familiar face.`;
  if (o.breaking_type) return `Against type. Somebody's betting you can stretch.`;
  if (o.in_your_lane) return `A role that fits how you've been reading lately.`;
  if (o.buzz_band && o.buzz_band !== 'quiet') return `There's ${o.buzz_band} around this one already.`;
  return `${genreLabel(o.genre)} is ${o.demand_band} right now, and they need bodies.`;
}

export function listingTags(o: Listing): string[] {
  const tags: string[] = [];
  if (o.project_type === 'series') tags.push(`Series · ${o.n_episodes ?? '?'} eps`);
  if (o.is_animation) tags.push('Voice');
  if (o.installment_number >= 1 && o.franchise_id) tags.push(o.installment_number === 1 ? 'Franchise launch' : `Sequel #${o.installment_number}`);
  if (o.source_material) tags.push(`From a ${o.source_material.replace(/_/g, ' ')}`);
  if (!o.union) tags.push('Non-union');
  return tags;
}

// Deterministic film titles, purely cosmetic.
const TITLE_A = ['The Long', 'A Quiet', 'The Last', 'Paper', 'Burning', 'The Glass', 'Silver', 'Cold', 'The Second', 'Midnight', 'Small', 'The Hollow', 'Bright', 'The Velvet', 'Lost'];
const TITLE_B = ['Winter', 'Harbor', 'Season', 'Kingdom', 'Hours', 'Machine', 'Country', 'Witness', 'Light', 'Avenue', 'Fever', 'Orchard', 'Signal', 'Debt', 'Coast'];
export function filmTitle(seed: number, age: number, index: number): string {
  const h = Math.abs((seed * 73856093) ^ (age * 19349663) ^ (index * 83492791));
  return `${TITLE_A[h % TITLE_A.length]} ${TITLE_B[(h >> 4) % TITLE_B.length]}`;
}

/** ux/03 §7: Standing's band-level change as a sentence, never a delta number. */
export const standingPhrase = (band: string) => STANDING_PHRASE[band] ?? band;
export function standingSentence(before: string, after: string): string {
  const b = STANDING_ORDER.indexOf(before);
  const a = STANDING_ORDER.indexOf(after);
  if (a > b && b >= 0) return `Your name carries more weight than it did in January. You're ${standingPhrase(after)} now.`;
  if (a < b && a >= 0) return `The calls come a little slower. You've slipped to ${standingPhrase(after)}.`;
  return `Still ${standingPhrase(after)}. The town hasn't changed its mind about you.`;
}
