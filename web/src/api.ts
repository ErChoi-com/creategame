// Typed client for callback/engine/simulation/web_server.py. Every shape here mirrors a plain-data
// dict that Session returns. The frontend never sees an engine type, the same contract cli.py keeps.

export type Option = [key: string, label: string];

export interface Options {
  backgrounds: [key: string, name: string, tagline: string][];
  ambitions: Option[];
  prep: Option[];
  dials: Option[];
  positions: Option[];
  scenes: string[];
  release: Option[];
  rating_cut: Option[];
  script_notes: Option[];
  orientations: Option[];
  bonus_types: Option[];
  director_genres: Option[];
  director_budget_tiers: Option[];
  director_dev_actions: Option[];
  attach_star_types: Option[];
}

export interface Status {
  game_id: string;
  age: number;
  is_over: boolean;
  standing_summary: string;
  persona_status?: { legibility_band: string; top_genre: string; top_archetype: string; consecutive_same_lane: number };
  application_status?: { agent_tier: string; applications_this_year: number; fatigue_band: string };
  leverage_status?: { agent_tier: string; scarcity: number; next_tier: string | null };
  franchise_status?: Record<string, unknown>[];
  multi_picture_deal_status?: Record<string, unknown> | null;
  directing_unlocked?: boolean;
  is_directing?: boolean;
  actor_quarters_remaining_this_year?: number;
  quarters_remaining_this_year?: number;
  director_status?: DirectorStatus;
}

export interface Listing {
  index: number;
  genre: string;
  secondary_genre: string | null;
  billing: 'lead' | 'supporting' | 'bit' | string;
  budget_millions: number;
  fee_millions: number;
  available: boolean;
  union: boolean;
  studio_name: string;
  studio_tagline: string;
  franchise_id: string | null;
  installment_number: number;
  franchise_scale: string;
  source_material: string | null;
  demand_band: string;
  buzz_band: string;
  director: { id: string | null; known: boolean; relationship: string | null };
  project_type: 'film' | 'series' | string;
  n_episodes: number | null;
  is_animation: boolean;
  in_your_lane: boolean;
  breaking_type: boolean;
  typecasting_note: string | null;
  quarters_required: number;
  guaranteed: boolean;
}

export interface HoldoutResult { paid: boolean; recast: boolean; raise_multiplier: number; proceeds: boolean }

export interface ReleaseSummary {
  studio_name: string;
  performance_band: string;
  critic_band: string;
  critic_score: number;
  audience_band: string;
  roi_band: string;
  roi: number;
  budget_millions: number;
  marketing_millions: number;
  rating_band?: string | null;
  rating_cut_forced?: boolean;
  rating_studio_pressure?: boolean;
  // films
  release_label?: string;
  requested_release?: string;
  studio_overruled?: boolean;
  gross_millions?: number;
  weekly_gross?: number[] | null;
  franchise_installment?: number;
  box_office_bonus_millions?: number;
  director_note_choice?: string;
  bid_taken?: { studio_name: string; payout_millions: number; kept_it: boolean; offers: number };
  // series (§5.18)
  n_episodes?: number;
  license_value_millions?: number;
  average_retention_pct?: number;
  renewable?: boolean;
  renewed?: boolean | null;
}

export interface DirectorProject {
  index: number;
  genre: string;
  budget_ask: number;
  momentum_band: string;
  script_quality_read: string;
  quarters_in_dev: number;
  self_financed: boolean;
  frozen: boolean;
  shooting: boolean;
  quarters_remaining_in_shoot: number | null;
  attachments: string[];
}

export interface DirectorStatus {
  credits: number;
  standing: string;
  max_projects: number;
  can_start_new_project: boolean;
  quarters_this_year: number;
  quarters_per_year: number;
  projects: DirectorProject[];
}

export interface DirectingResult {
  greenlit: boolean;
  resolved: boolean;
  shooting: boolean;
  quarters_remaining_in_shoot: number | null;
  dead: boolean;
  frozen: boolean;
  momentum_band: string;
  blocked_on_money?: boolean;
  shortfall?: number | null;
  error?: string;
}

export interface YearEvent {
  genre?: string;
  greenlit?: boolean;
  resolved?: boolean;
  critic_band?: string;
  audience_band?: string;
  roi_band?: string;
  release_label?: string;
  director_income_millions?: number;
  [key: string]: unknown;
}

export interface Obituary {
  credits: number;
  declined: { genre: string; roi_band: string; critic_band: string }[];
  kept: number;
  lost: number;
  best_hidden_performance: { genre: string; band: string } | null;
}

export interface NewGame { game_id: string; seed: number; intro: string; status: Status }

async function request<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`/api/${path}`, body === undefined
    ? { cache: 'no-store' }
    : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const data = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
  if (!res.ok) throw new Error(data.error ?? `HTTP ${res.status}`);
  return data as T;
}

export const api = {
  options: () => request<Options>('options'),
  newGame: (background: string, ambition: string, seed?: number) =>
    request<NewGame>('games', { background, ambition, seed }),
  status: (id: string) => request<Status>(`games/${id}/status`),
  autoPlay: (id: string, years: number) =>
    request<{ years_played: number; transcript: string; status: Status }>(`games/${id}/auto_play`, { years }),
  call: async <T>(id: string, method: string, args: Record<string, unknown> = {}) =>
    (await request<{ result: T }>(`games/${id}/call`, { method, args })).result,
};

/** Session calls bound to one game, typed per method. */
export function gameApi(id: string) {
  const c = <T>(method: string, args: Record<string, unknown> = {}) => api.call<T>(id, method, args);
  return {
    status: () => api.status(id),
    offerBoard: () => c<Listing[]>('offer_board'),
    moreListings: () => c<Listing[]>('generate_more_listings'),
    accept: (index: number) => c<null>('accept', { index }),
    declineBoard: () => c<{ genre: string; roi_band: string; critic_band: string }[]>('decline_board'),
    holdoutAvailable: () => c<boolean>('holdout_available'),
    requestHoldout: () => c<HoldoutResult>('request_holdout'),
    approvalsAvailable: () => c<boolean>('approvals_available'),
    bonusAvailable: (bonus_type: string) => c<boolean>('box_office_bonus_available', { bonus_type }),
    chooseDeal: (want_approvals: boolean, want_box_office_bonus = false, bonus_type = 'net_points') =>
      c<number | null>('choose_deal', { want_approvals, want_box_office_bonus, bonus_type }),
    scriptNotesAvailable: () => c<boolean>('script_notes_available'),
    chooseScriptNote: (key: string) => c<null>('choose_script_note', { key }),
    choosePrep: (key: string) => c<null>('choose_prep', { key }),
    episodeLabels: () => c<string[]>('episode_labels'),
    playScene: (choices: Record<string, string>) => c<null>('play_scene', { choices }),
    ratingPreview: () => c<{ band: string; cut_available: boolean }>('rating_preview'),
    chooseRatingStance: (key: string) => c<null>('choose_rating_stance', { key }),
    chooseRelease: (strategy: string, bid_policy: 'best' | 'self' = 'best') =>
      c<ReleaseSummary>('choose_release', { strategy, bid_policy }),
    awardsAvailable: () => c<boolean>('awards_campaign_available'),
    awardCategories: () => c<string[]>('available_award_categories'),
    runAwards: (category: string, spend_millions: number) =>
      c<Record<string, unknown>>('run_awards_campaign', { category, spend_millions }),
    trades: () => c<string[]>('trades'),
    rolodex: () => c<{ id: string; type: string; relationship: string }[]>('rolodex_summary'),
    interact: (npc_id: string, action: string) => c<string>('interact', { npc_id, action }),
    becomeDirector: () => c<string>('become_director'),
    directorStatus: () => c<DirectorStatus>('director_status'),
    startDirecting: (genre: string, budget_tier: string) => c<boolean>('start_directing_project', { genre, budget_tier }),
    advanceDirecting: (project_index: number, action: string) =>
      c<DirectingResult>('advance_directing', { project_index, action }),
    endYear: () => c<YearEvent[]>('end_year'),
    obituary: () => c<Obituary>('obituary_summary'),
  };
}

export type GameApi = ReturnType<typeof gameApi>;
