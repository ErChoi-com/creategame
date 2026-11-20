// ux/03 §7: the Reckoning. A sentence, not a chart. Calls Session.end_year() exactly once.
import { useCallback } from 'react';
import type { Status, YearEvent } from '../api';
import { Busy, Ledger } from '../components/Data';
import { useOnce } from '../components/Flow';
import { Button } from '../components/Inputs';
import { Screen, Section } from '../components/Layout';
import { genreLabel, money, standingSentence } from '../lib/copy';
import type { Game } from '../lib/game';
import { humanize } from '../lib/names';

function eventLine(e: YearEvent): string {
  const film = e.genre ? `Your ${genreLabel(String(e.genre)).toLowerCase()}` : 'Your film';
  if (e.greenlit && e.resolved) {
    const pay = typeof e.director_income_millions === 'number' && e.director_income_millions !== 0
      ? ` You ${e.director_income_millions > 0 ? 'cleared' : 'lost'} ${money(Math.abs(e.director_income_millions))}.` : '';
    return `${film} came out: ${e.critic_band} reviews, ${e.roi_band}.${pay}`;
  }
  return `${film}: ${Object.entries(e).filter(([, v]) => typeof v === 'string').map(([, v]) => v).slice(0, 2).join(', ')}.`;
}

export function Reckoning({ game, before, onDone, fail }: {
  game: Game;
  before: Status;
  onDone: (s: Status) => void;
  fail: (e: unknown) => void;
}) {
  const data = useOnce(useCallback(async () => {
    const events = await game.api.endYear();
    const status = await game.api.status();
    const trades = status.age % 5 === 0 ? await game.api.trades() : [];
    return { events, status, trades };
  }, [game]), fail);

  if (!data) return <Screen eyebrow={`Age ${before.age}`} title="The year closes"><Busy label="Counting it up" /></Screen>;
  const { events, status, trades } = data;
  return (
    <Screen
      eyebrow={`The reckoning · age ${before.age} → ${status.age}`}
      title={standingSentence(before.standing_summary, status.standing_summary)}
      footer={<Button variant="primary" onClick={() => onDone(status)}>{status.is_over ? 'Read the obituary' : `Age ${status.age} →`}</Button>}
    >
      {events.length > 0 && (
        <Section title="What wrapped" style={{ marginTop: 0 }}>
          <Ledger items={events.map(eventLine)} />
        </Section>
      )}
      {trades.length > 0 && (
        <Section title="The trades">
          <Ledger items={trades.map((t) => <span className="dim">{humanize(t)}</span>)} />
        </Section>
      )}
    </Screen>
  );
}
