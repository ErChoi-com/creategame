// rolodex/npc.py: "a naming/generation layer is a UI concern, not this engine's". This is that
// layer: a stable display name derived from an NPC id, so "n_002" is always the same person.
const FIRST = ['Maya', 'Theo', 'Priya', 'Jonah', 'Ines', 'Marcus', 'Lena', 'Dev', 'Rosa', 'Felix', 'Noor', 'Caleb', 'Ada', 'Sami', 'June', 'Rafael', 'Willa', 'Kenji', 'Odette', 'Booker', 'Clara', 'Emeka', 'Hollis', 'Vera'];
const LAST = ['Okonkwo', 'Hartley', 'Varga', 'Ricci', 'Castellanos', 'Lindqvist', 'Abernathy', 'Moreau', 'Nakamura', 'Whitlock', 'Delacroix', 'Osei', 'Brennan', 'Szabo', 'Kowalczyk', 'Achterberg', 'Fairbanks', 'Ibarra', 'Quill', 'Mbeki', 'Sorensen', 'Halloway', 'Petrov', 'Calloway'];

function hash(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return h >>> 0;
}

export function npcName(id: string): string {
  const h = hash(id);
  return `${FIRST[h % FIRST.length]} ${LAST[(h >>> 8) % LAST.length]}`;
}

/** Replace raw engine ids ("NPC-n_002", "n_002") inside engine-written sentences. */
export function humanize(text: string): string {
  return text.replace(/NPC-(n_\d+)/g, (_, id) => npcName(id)).replace(/\b(n_\d+)\b/g, (_, id) => npcName(id));
}
