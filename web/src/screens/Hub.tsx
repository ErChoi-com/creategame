// ux/02's hub: identity strip, the calendar, exactly one "what's happening" card, the pull tabs.
// Pushed decisions (acting, directing, the reckoning) render as full-screen flows on top.
import { useMemo, useState } from 'react';
import type { Options, Status } from '../api';
import { ErrorNote, Quarters } from '../components/Data';
import { Flow } from '../components/Flow';
import { Button } from '../components/Inputs';
import { actingSteps, type ActingCtx } from '../flows/acting';
import { directingSteps, type DirectingCtx } from '../flows/directing';
import { AGENT_PHRASE } from '../lib/content';
import { standingPhrase } from '../lib/copy';
import type { Game } from '../lib/game';
import { PullTabs } from './PullTabs';
import { Reckoning } from './Reckoning';

type Push = 'acting' | 'directing' | 'reckoning' | null;

interface YearState { acted: boolean; directed: boolean; lines: string[] }
const freshYear = (): YearState => ({ acted: false, directed: false, lines: [] });

export function Hub({ game, options, status, setStatus, refresh, onQuit }: {
  game: Game;
  options: Options;
  status: Status;
  setStatus: (s: Status) => void;
  refresh: () => Promise<void>;
  onQuit: () => void;
}) {
  const [push, setPush] = useState<Push>(null);
  const [year, setYear] = useState<YearState>(freshYear);
  const [error, setError] = useState<string | null>(null);
  const [skipping, setSkipping] = useState(false);

  const used = 4 - (status.actor_quarters_remaining_this_year ?? 4);
  const canDirect = !!status.directing_unlocked && !year.directed;

  // Exactly one card (ux/02): the most relevant thing right now.
  const now = useMemo(() => {
    if (!year.acted) return { eyebrow: 'The phone', line: 'The offer board is up.', cta: 'See the offers', go: 'acting' as Push };
    if (canDirect && status.is_directing) return { eyebrow: 'Your slate', line: 'The slate needs this year’s orders.', cta: 'Open the slate', go: 'directing' as Push };
    return { eyebrow: 'Nothing pushing', line: 'The year is yours to close.', cta: 'Close the year', go: 'reckoning' as Push };
  }, [year, canDirect, status.is_directing]);

  const endFlow = (outcome?: string, mark?: Partial<YearState>) => {
    setPush(null);
    setYear((y) => ({ ...y, ...mark, lines: outcome ? [...y.lines, outcome] : y.lines }));
    void refresh();
  };

  const skipAhead = async (years: number) => {
    setSkipping(true);
    try {
      const r = await game.api.autoPlay(years);
      setStatus(r.status);
      setYear(freshYear());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSkipping(false);
    }
  };

  const base = { game, options, status };
  return (
    <main className="shell" style={{ paddingTop: 40, paddingBottom: 96 }}>
      {/* identity strip */}
      <header className="spread rise" style={{ alignItems: 'flex-end', borderBottom: '1px solid var(--line)', paddingBottom: 28 }}>
        <div>
          <p className="eyebrow">{game.intro}</p>
          <h1 className="display" style={{ fontSize: 'clamp(56px, 11vw, 148px)', marginTop: 10 }}>{status.age}</h1>
        </div>
        <div style={{ textAlign: 'right' }}>
          <p className="headline" style={{ fontSize: 'clamp(24px, 3.4vw, 40px)' }}><em style={{ fontWeight: 400 }}>{standingPhrase(status.standing_summary)}</em></p>
          <p className="mono faint" style={{ marginTop: 8 }}>{status.leverage_status ? AGENT_PHRASE[status.leverage_status.agent_tier] ?? status.leverage_status.agent_tier : ''}</p>
        </div>
      </header>

      {/* the calendar */}
      <section className="spread rise" style={{ padding: '22px 0', borderBottom: '1px solid var(--line)', animationDelay: '0.1s' }}>
        <span className="row"><span className="eyebrow">This year</span><Quarters used={used} /></span>
        <span className="mono faint">{used ? `${used} quarter${used > 1 ? 's' : ''} on set` : 'Open'}</span>
      </section>

      {/* what's happening */}
      <section className="card rise" style={{ marginTop: 32, padding: 'clamp(24px, 4vw, 44px)', animationDelay: '0.2s' }}>
        <p className="eyebrow">{now.eyebrow}</p>
        <p className="headline" style={{ marginTop: 12 }}>{now.line}</p>
        {year.lines.length > 0 && <p className="dim" style={{ marginTop: 12 }}>{year.lines[year.lines.length - 1]}</p>}
        <div className="row" style={{ marginTop: 28 }}>
          <Button variant="primary" onClick={() => setPush(now.go)}>{now.cta} →</Button>
          {canDirect && now.go !== 'directing' && <Button onClick={() => setPush('directing')}>{status.is_directing ? 'Open the slate' : 'Step behind the camera'}</Button>}
          {now.go !== 'reckoning' && <Button variant="ghost" onClick={() => setPush('reckoning')}>Close the year</Button>}
        </div>
      </section>
      <ErrorNote error={error} />

      <PullTabs game={game} status={status} refresh={refresh} />

      <footer className="spread" style={{ marginTop: 64, paddingTop: 20, borderTop: '1px solid var(--line)' }}>
        <span className="row">
          <span className="mono faint">Skip ahead</span>
          {[1, 5, 10].map((n) => <Button key={n} variant="ghost" disabled={skipping} onClick={() => skipAhead(n)}>{n} yr</Button>)}
        </span>
        <Button variant="ghost" onClick={onQuit}>New career</Button>
      </footer>

      {push === 'acting' && (
        <Flow<ActingCtx> steps={actingSteps} initial={base} onDone={(c) => endFlow(c.outcome, { acted: true })} />
      )}
      {push === 'directing' && (
        <Flow<DirectingCtx> steps={directingSteps} initial={base} onDone={(c) => endFlow(c.outcome, { directed: true })} />
      )}
      {push === 'reckoning' && (
        <Reckoning game={game} before={status} fail={(e) => { setPush(null); setError(String(e)); }}
          onDone={(s) => { setPush(null); setYear(freshYear()); setStatus(s); }} />
      )}
    </main>
  );
}
