// Player-facing glosses, keyed by the engine's own option keys. Screens read option *lists* from
// the engine (/api/options, Session) and look up flavour text here, so adding an option in the
// engine never needs a UI change, only (optionally) a gloss.

export const GLOSS: Record<string, Record<string, string>> = {
  ambitions: {
    work: 'To be good. Really good. Whatever it costs.',
    prize: 'A statue on the mantel, and a speech you rehearsed in the car.',
    fortune: 'Never worry about rent again. Then never worry about anything.',
    run: 'Decades. Still working when the others have faded.',
    franchise: 'Your face on the lunchbox. Your name on the sequel.',
    voice: 'To say something with it, while they still hand you the microphone.',
  },
  prep: {
    table_work: 'Read it until it reads you. Cheap, quiet, rarely wrong.',
    research: 'Slower to start. Nothing rattles you once you’re there.',
    dialect: 'The voice is the door. Miss it and nothing else lands.',
    physical_transformation: 'Weeks of it. People notice. Your body notices too.',
    live_it: 'Stay in it between takes. Brilliant, or unbearable.',
  },
  positions: {
    with: 'Give the scene what it asks for.',
    beneath: 'Less than they expect. Make them lean in.',
    beyond: 'More than the page. Risky, memorable.',
    against: 'The opposite of the obvious read.',
  },
  release: {
    wide: 'Every screen in the country, and a campaign to match.',
    limited: 'A few cities first. Let it find its people.',
    festival: 'Premiere it, and find out if anyone buys.',
    streaming: 'A flat payout up front. No upside, no humiliation.',
  },
  rating_cut: {},
  director_dev_actions: {},
};

/** §5.6's table: the dial most likely carrying each genre's turn. Others fill in automatically. */
export const CARRYING_DIAL: Record<string, string> = {
  horror: 'energy', action: 'speed', drama: 'warmth', comedy: 'speed', romance: 'warmth',
  thriller: 'energy', scifi: 'energy', musical: 'speed', period: 'warmth', family: 'warmth',
  crime: 'energy', fantasy: 'energy', superhero: 'speed', war: 'speed', western: 'warmth',
};
export const DEFAULT_POSITION = 'with';

/** Directing: the four standing orders the review proposes up front; the rest sit behind "more". */
export const PRIMARY_DEV_ACTIONS = ['take_to_market', 'rewrite', 'attach_star', 'drawer'];

/** simulation/bands.py STANDING_BANDS, low to high. */
export const STANDING_ORDER = ['unknown', 'working', 'in-demand', 'sought-after', 'a star'];
/** Each band as something a person would say (ux/05 step 2). */
export const STANDING_PHRASE: Record<string, string> = {
  unknown: 'an unknown',
  working: 'a working actor',
  'in-demand': 'in demand',
  'sought-after': 'sought after',
  'a star': 'a star',
};

/** leverage/catalogue.py AGENT_TIERS, as a sentence fragment. */
export const AGENT_PHRASE: Record<string, string> = {
  unrepresented: 'No agent yet',
  regional: 'A regional agent',
  boutique: 'A boutique agency',
  major: 'A major agency',
  powerhouse: 'A powerhouse agency',
};

export const AWARD_LABELS: Record<string, string> = {
  lead_drama: 'Lead Performance — Drama',
  lead_comedy: 'Lead Performance — Musical/Comedy',
  supporting: 'Supporting Performance',
  ensemble: 'Ensemble Cast',
  breakthrough: 'Breakthrough Performance',
  genre_excellence: 'Genre Excellence',
  voice_performance: 'Voice Performance',
};

export const INTERACT_ACTIONS: [string, string][] = [
  ['check_in', 'Check in'],
  ['show_up', 'Show up for them'],
  ['read_agenda', 'Read what they want'],
  ['vouch', 'Vouch for them'],
];
