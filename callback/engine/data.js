// Static world data: genres, palette weights, archetypal shapes, the position
// read table, and the name pools the world sim draws NPCs from.
//
// Sourced from callback/docs/callback-design-doc-v8.md §5.3–§5.7 and §9.1.

export const DIALS = ['pace', 'colour', 'scale', 'intensity', 'clarity', 'texture'];

// The six axes a film is built from — read-only, never chosen by the
// player, the shape they are reacting to rather than picking. DIALS and
// PALETTE_WEIGHTS/SHAPES below are the tuned numbers; DIAL_LABELS is only
// the plain-English pole a player sees at each end of the bar.
export const DIAL_LABELS = {
  pace: ['Slow-burn', 'Fast-paced'],
  colour: ['Muted', 'Vivid'],
  scale: ['Intimate', 'Epic'],
  intensity: ['Gentle', 'Intense'],
  clarity: ['Subtle', 'On-the-nose'],
  texture: ['Steady', 'Frantic'],
};
export const DIAL_AXIS_LABELS = {
  pace: 'Pace', colour: 'Colour', scale: 'Scale',
  intensity: 'Intensity', clarity: 'How it spells things out', texture: 'Rhythm',
};

export const GENRE_NAMES = {
  drama: 'drama', comedy: 'comedy', action: 'action', horror: 'horror',
  thriller: 'thriller', romance: 'romance', scifi: 'science fiction',
  period: 'period', musical: 'musical', family: 'family',
};

export const GENRES = [
  'drama', 'comedy', 'action', 'horror', 'thriller',
  'romance', 'scifi', 'period', 'musical', 'family',
];

// Per-genre palette weights. Audience and critic weights deliberately disagree
// by different amounts per genre (§5.3): horror aligns, drama opposes.
export const PALETTE_WEIGHTS = {
  drama:    { aud: { pace: 6, colour: 4, scale: 2, intensity: 5, clarity: 9, texture: 3 },
              crit:{ pace: -4, colour: -5, scale: -6, intensity: -2, clarity: -11, texture: -4 } },
  comedy:   { aud: { pace: 10, colour: 7, scale: 1, intensity: -2, clarity: 8, texture: 6 },
              crit:{ pace: 6, colour: 2, scale: -5, intensity: -3, clarity: 2, texture: 3 } },
  action:   { aud: { pace: 9, colour: 5, scale: 9, intensity: 8, clarity: 7, texture: 8 },
              crit:{ pace: 2, colour: -2, scale: -4, intensity: -3, clarity: -6, texture: 1 } },
  horror:   { aud: { pace: -3, colour: -6, scale: -7, intensity: -4, clarity: -8, texture: 2 },
              crit:{ pace: -5, colour: -7, scale: -8, intensity: -6, clarity: -9, texture: 1 } },
  thriller: { aud: { pace: 7, colour: -2, scale: 2, intensity: 6, clarity: 5, texture: 5 },
              crit:{ pace: 3, colour: -4, scale: -5, intensity: 1, clarity: -7, texture: 2 } },
  romance:  { aud: { pace: 2, colour: 8, scale: -1, intensity: 1, clarity: 7, texture: -2 },
              crit:{ pace: -2, colour: 1, scale: -6, intensity: 3, clarity: -6, texture: -3 } },
  scifi:    { aud: { pace: 6, colour: 6, scale: 9, intensity: 5, clarity: 6, texture: 5 },
              crit:{ pace: -3, colour: 2, scale: 3, intensity: -2, clarity: -8, texture: -1 } },
  period:   { aud: { pace: 3, colour: 5, scale: 7, intensity: 2, clarity: 6, texture: -3 },
              crit:{ pace: -3, colour: 3, scale: 4, intensity: 2, clarity: -5, texture: -4 } },
  musical:  { aud: { pace: 8, colour: 10, scale: 7, intensity: 3, clarity: 6, texture: 7 },
              crit:{ pace: 4, colour: 6, scale: 1, intensity: 2, clarity: -2, texture: 5 } },
  family:   { aud: { pace: 6, colour: 9, scale: 5, intensity: -6, clarity: 9, texture: 4 },
              crit:{ pace: 1, colour: 3, scale: -3, intensity: -4, clarity: -3, texture: 0 } },
};

// Genre economics (§9.1): budget centre in $M, demand baseline, volatility.
export const GENRE_ECON = {
  drama:    { budget: 22,  demand: 46, vol: 0.7, critBias: 4 },
  comedy:   { budget: 35,  demand: 58, vol: 1.0, critBias: -4 },
  action:   { budget: 120, demand: 64, vol: 1.1, critBias: -3 },
  horror:   { budget: 12,  demand: 55, vol: 1.5, critBias: -5 },
  thriller: { budget: 45,  demand: 55, vol: 0.9, critBias: 0 },
  romance:  { budget: 28,  demand: 52, vol: 1.0, critBias: -2 },
  scifi:    { budget: 110, demand: 60, vol: 1.2, critBias: 1 },
  period:   { budget: 48,  demand: 44, vol: 0.8, critBias: 5 },
  musical:  { budget: 60,  demand: 47, vol: 1.4, critBias: 2 },
  family:   { budget: 80,  demand: 62, vol: 0.9, critBias: -1 },
};

export const ARCHETYPES = [
  'leading_hero', 'romantic_lead', 'villain', 'everyman', 'character_actor',
  'ingenue', 'authority', 'comic_relief', 'wildcard',
];

// §5.4 archetypal palette shapes. Coherence is distance to the nearest of these.
export const SHAPES = {
  blockbuster:  { pace: 34, colour: 30, scale: 42, intensity: 30, clarity: 38, texture: 34 },
  art_film:     { pace: -32, colour: -18, scale: -34, intensity: -14, clarity: -38, texture: -28 },
  horror_shape: { pace: -10, colour: -30, scale: -28, intensity: 34, clarity: -20, texture: 12 },
  chamber:      { pace: -20, colour: -6, scale: -42, intensity: -8, clarity: 6, texture: -30 },
  epic:         { pace: -4, colour: 20, scale: 46, intensity: 18, clarity: 20, texture: -6 },
  verite:       { pace: 8, colour: -24, scale: -26, intensity: 14, clarity: -6, texture: 38 },
  neon:         { pace: 18, colour: 44, scale: 4, intensity: 26, clarity: -12, texture: 24 },
};

// A plain, complete phrase for each shape — not the internal key with an
// article guessed onto it ("a horror_shape"), a description a player would
// actually say out loud.
export const SHAPE_LABELS = {
  blockbuster: 'a blockbuster',
  art_film: 'an art film',
  horror_shape: 'a horror movie',
  chamber: 'a small, contained two-hander',
  epic: 'a sweeping epic',
  verite: 'a fly-on-the-wall drama',
  neon: 'a neon-lit, stylised piece',
};

// §5.5 the four performance dials and four positions. The internal keys
// (with/beneath/beyond/against, energy/volume/warmth/speed) are unchanged —
// every tuned number in READ and every calibrated sim policy keys off them —
// but nothing prints a raw key to the player. PERF_DIAL_LABELS and
// POSITION_LABELS are the plain-language surface the interface uses instead.
export const PERF_DIALS = ['energy', 'volume', 'warmth', 'speed'];
export const PERF_DIAL_LABELS = {
  energy: 'Energy', volume: 'Size', warmth: 'Warmth', speed: 'Tempo',
};
export const PERF_DIAL_HINTS = {
  energy: 'What you bring into the room before you say anything',
  volume: 'How much of the frame you take up',
  warmth: 'Whether the character lets anyone in',
  speed: 'The clock you are playing the scene on',
};

export const POSITIONS = ['with', 'beneath', 'beyond', 'against'];
export const POSITION_COST = { with: 0, beneath: 1, beyond: 2, against: 3 };
// A plain-language name and one-line description for each stance, and the
// number of points it costs — 0 to 3, same scale a player already reads as
// "how bold is this."
export const POSITION_LABELS = {
  with: 'Match it', beneath: 'Hold back', beyond: 'Go big', against: 'Play against it',
};
export const POSITION_HINTS = {
  with: 'Do what the scene is already asking for',
  beneath: 'Underplay it — the stiller choice',
  beyond: 'Bigger than the scene asks — it will be noticed',
  against: 'Deliberate counterpoint — the boldest, riskiest choice',
};

// §6.7 approvals and §6.7 positions — two more Sets of internal keys that
// used to print straight to the ledger ("costar, script, cut", "prodco,
// teacher, board"). Note the name collision with POSITIONS above: those are
// scene stances, these are the standing offices (guild seat, jury, your own
// company) a career can accumulate. Different things, same English word —
// which is exactly the kind of overlap this file exists to paper over before
// it reaches a player.
export const APPROVAL_LABELS = {
  costar: 'say over your scene partner',
  script: 'say over the script',
  director: 'say over who directs you',
  cut: 'a seat in the edit',
};

export const CAREER_POSITION_LABELS = {
  guild: 'Guild officer',
  juror: 'Festival juror',
  prodco: 'Your own production company',
  teacher: 'Teaching',
  board: 'Studio board seat',
};

// READ[dial][position] = [forYou, forTheFilm]
export const READ = {
  energy: { with: [0.5, 1.5], beneath: [2.5, 1.0], beyond: [1.0, -0.5], against: [4.5, 0.5] },
  volume: { with: [0.5, 1.5], beneath: [3.0, 1.5], beyond: [0.5, -1.5], against: [3.5, 0.0] },
  warmth: { with: [0.5, 1.5], beneath: [1.5, 0.5], beyond: [2.0, 0.5], against: [4.0, -0.5] },
  speed:  { with: [0.5, 1.5], beneath: [2.0, 1.0], beyond: [2.5, 0.0], against: [3.0, 0.5] },
};

// Genre reweighting of which dials pay (§5.5).
export const GENRE_DIAL_WEIGHT = {
  drama:    { energy: 1.2, volume: 1.1, warmth: 1.2, speed: 0.8 },
  comedy:   { energy: 1.0, volume: 1.0, warmth: 1.1, speed: 1.6 },
  action:   { energy: 0.7, volume: 1.0, warmth: 0.8, speed: 1.2 },
  horror:   { energy: 1.5, volume: 1.3, warmth: 0.9, speed: 1.0 },
  thriller: { energy: 1.3, volume: 1.1, warmth: 0.9, speed: 1.1 },
  romance:  { energy: 0.9, volume: 1.0, warmth: 1.5, speed: 0.9 },
  scifi:    { energy: 1.1, volume: 0.9, warmth: 1.0, speed: 1.0 },
  period:   { energy: 1.0, volume: 1.2, warmth: 1.1, speed: 0.8 },
  musical:  { energy: 1.2, volume: 1.3, warmth: 1.2, speed: 1.2 },
  family:   { energy: 1.0, volume: 0.9, warmth: 1.4, speed: 1.0 },
};

export const BILLING_WEIGHT = { lead: 1.0, supporting: 0.55, bit: 0.2, extra: 0.0 };
export const BILLING_DIFFICULTY = { lead: 74, supporting: 58, bit: 36 };

// Project types and the calendar blocks they eat (§4.8). A year is 4 blocks.
export const PROJECT_TYPES = {
  indie: { blocks: 1, budgetMult: 0.25, label: 'Indie feature' },
  studio: { blocks: 2, budgetMult: 1.0, label: 'Studio feature' },
  tentpole: { blocks: 3, budgetMult: 3.0, label: 'Tentpole' },
  tv_season: { blocks: 3, budgetMult: 0.5, label: 'TV season' },
  streaming: { blocks: 2, budgetMult: 0.6, label: 'Streaming series' },
  theatre: { blocks: 2, budgetMult: 0.05, label: 'Theatre run' },
  voice: { blocks: 1, budgetMult: 0.15, label: 'Voice work' },
};

export const GATEKEEPERS = {
  tentpole:   { heat: 0.55, prestige: 0.05, affection: 0.30, notoriety: -0.40 },
  auteur:     { heat: 0.10, prestige: 0.65, affection: 0.05, notoriety: 0.05 },
  indie:      { heat: 0.15, prestige: 0.40, affection: 0.10, notoriety: 0.00 },
  streamer:   { heat: 0.35, prestige: 0.15, affection: 0.30, notoriety: 0.15 },
  network:    { heat: 0.30, prestige: 0.10, affection: 0.45, notoriety: -0.55 },
  franchise:  { heat: 0.45, prestige: 0.10, affection: 0.35, notoriety: -0.30 },
};

export const AGENT_TIERS = {
  none:       { commission: 0.00, offers: 0, negotiate: 0.00, label: 'No representation' },
  boutique:   { commission: 0.10, offers: 1, negotiate: 0.08, label: 'Boutique agency' },
  midtier:    { commission: 0.12, offers: 2, negotiate: 0.18, label: 'Mid-tier agency' },
  powerhouse: { commission: 0.15, offers: 4, negotiate: 0.25, label: 'Powerhouse agency' },
};

export const FIRST_NAMES = [
  'Ada', 'Marcus', 'Ines', 'Theo', 'Rosalind', 'Cal', 'June', 'Otto', 'Nadia',
  'Perry', 'Sabine', 'Wes', 'Lila', 'Gideon', 'Mara', 'Emmett', 'Yusuf', 'Vera',
  'Dov', 'Claudia', 'Reg', 'Simone', 'Hal', 'Antonia', 'Bruno', 'Kit',
];
export const LAST_NAMES = [
  'Ferreira', 'Okonkwo', 'Lindqvist', 'Rao', 'Vance', 'Duplessis', 'Moreau',
  'Halloran', 'Castellanos', 'Whitlock', 'Nakamura', 'Brennan', 'Sorokin',
  'Achebe', 'Marchetti', 'Delgado', 'Straub', 'Fenwick', 'Osei', 'Kowalski',
];
export const TITLE_A = [
  'The Quiet', 'Bad', 'Little', 'The Last', 'Winter in', 'Nobody Calls',
  'Hollow', 'The Long', 'Saltwater', 'A Kind of', 'Nine', 'The Wrong',
  'Dust and', 'The Second', 'Blue', 'Fever', 'The Weight of', 'Every Good',
  'After the', 'The Patient', 'Half a', 'Some Kind of', 'The Burning',
  'North of', 'The Borrowed', 'Two Weeks in', 'The Unquiet', 'Small',
];
export const TITLE_B = [
  'Country', 'Hours', 'Monsters', 'Anniversary', 'Machine', 'Wednesday',
  'Harvest', 'Daughters', 'Ledger', 'Homecoming', 'Season', 'Signal',
  'Inheritance', 'Ceremony', 'Vault', 'Undertow', 'Arrangement', 'Boys',
  'Radio', 'Wilderness', 'Confession', 'Orchard', 'Hotel', 'Sisters',
  'Departure', 'Argument', 'Bridge', 'November', 'Verdict', 'Kingdom',
];
// A few titles are just a noun, and a few are a place and a year.
export const TITLE_SOLO = [
  'Undertow', 'Ravenswood', 'Blackwater', 'Coldharbour', 'Marchmont',
  'The Understudy', 'Gethsemane', 'Pale Fire Road', 'Sixty-One', 'Thaw',
];
