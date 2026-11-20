// ux/04's pull surfaces: always reachable, never interrupting. Tabs are declared as config below.
import { useCallback, useEffect, useState, type ReactNode } from 'react';
import type { Status } from '../api';
import { Busy, EmptyState, ErrorNote, KeyValueList, Ledger } from '../components/Data';
import { Button, Tabs } from '../components/Inputs';
import { AGENT_PHRASE, INTERACT_ACTIONS } from '../lib/content';
import { humanize, npcName } from '../lib/names';
import { genreLabel, pretty } from '../lib/copy';
import type { Game } from '../lib/game';

type PanelProps = { game: Game; status: Status; refresh: () => Promise<void> };

/** Fetch-on-open panel data, re-fetched when the year changes. */
function usePanel<T>(load: () => Promise<T>, age: number) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const reload = useCallback(() => load().then(setData).catch((e) => setError(e.message)), [load]);
  useEffect(() => { void reload(); }, [reload, age]);
  return { data, error, reload };
}

function CareerPanel({ status, game }: PanelProps) {
  const p = status.persona_status;
  return (
    <KeyValueList rows={[
      ['Chasing', game.ambition],
      ['How the town reads you', p ? `${genreLabel(p.top_genre)}, the ${pretty(p.top_archetype).toLowerCase()}` : null],
      ['Typecast', p ? (p.legibility_band === 'high' ? 'They know exactly what to do with you, and only that.' : p.legibility_band === 'low' ? 'Hard to pin down.' : 'Getting a reputation.') : null],
      ['Same lane, in a row', p?.consecutive_same_lane ? `${p.consecutive_same_lane} film(s)` : null],
      ['Franchises', status.franchise_status?.length ? `${status.franchise_status.length} you're part of` : null],
      ['Directing', status.is_directing ? `Yes, ${status.director_status?.credits ?? 0} credit(s)` : status.directing_unlocked ? 'Open to you' : null],
    ]} />
  );
}

function RolodexPanel({ game, status }: PanelProps) {
  const { data, error, reload } = usePanel(useCallback(() => game.api.rolodex(), [game]), status.age);
  const [note, setNote] = useState<string | null>(null);
  if (!data) return error ? <ErrorNote error={error} /> : <Busy />;
  return (
    <>
      {note && <p className="accent" style={{ padding: '12px 0' }}>{humanize(note)}</p>}
      <Ledger
        empty="Nobody yet. Work, and people find you."
        items={data.map((n) => (
          <div className="spread">
            <span><span className="title" style={{ fontSize: 18 }}>{npcName(n.id)}</span> <span className="faint mono">{pretty(n.type)}</span>
              <span className="dim" style={{ display: 'block', fontSize: 13 }}>{n.relationship}</span></span>
            <span className="row" style={{ gap: 4 }}>
              {INTERACT_ACTIONS.map(([a, label]) => (
                <Button key={a} variant="ghost" onClick={async () => { setNote(await game.api.interact(n.id, a)); void reload(); }}>{label}</Button>
              ))}
            </span>
          </div>
        ))}
      />
    </>
  );
}

function LeveragePanel({ game, status, refresh }: PanelProps) {
  const l = status.leverage_status;
  const [note, setNote] = useState<string | null>(null);
  return (
    <>
      <KeyValueList rows={[
        ['Representation', l ? AGENT_PHRASE[l.agent_tier] ?? pretty(l.agent_tier) : null],
        ['Next step up', l?.next_tier ? AGENT_PHRASE[l.next_tier] ?? pretty(l.next_tier) : 'Top of the ladder'],
        ['Auditions this year', status.application_status ? `${status.application_status.applications_this_year} · ${status.application_status.fatigue_band}` : null],
      ]} />
      {l?.next_tier && (
        <div style={{ marginTop: 18 }}>
          <Button onClick={async () => { setNote(await game.api.tryAdvanceAgent()); await refresh(); }}>Try for better representation</Button>
        </div>
      )}
      {note && <p className="accent" style={{ marginTop: 12 }}>{humanize(note)}</p>}
    </>
  );
}

function TradesPanel({ game, status }: PanelProps) {
  const { data, error } = usePanel(useCallback(() => game.api.trades(), [game]), status.age);
  if (!data) return error ? <ErrorNote error={error} /> : <Busy />;
  return data.length ? <Ledger items={data.map(humanize)} /> : <EmptyState>A quiet week in the trades.</EmptyState>;
}

const TABS: { id: string; label: string; render: (p: PanelProps) => ReactNode }[] = [
  { id: 'career', label: 'Career', render: (p) => <CareerPanel {...p} /> },
  { id: 'rolodex', label: 'Rolodex', render: (p) => <RolodexPanel {...p} /> },
  { id: 'leverage', label: 'Leverage', render: (p) => <LeveragePanel {...p} /> },
  { id: 'trades', label: 'Trades', render: (p) => <TradesPanel {...p} /> },
];

export function PullTabs(props: PanelProps) {
  const [tab, setTab] = useState(TABS[0].id);
  const active = TABS.find((t) => t.id === tab) ?? TABS[0];
  return (
    <section style={{ marginTop: 56 }}>
      <Tabs tabs={TABS} active={tab} onChange={setTab} />
      <div style={{ paddingTop: 12 }} key={tab}>{active.render(props)}</div>
    </section>
  );
}
