import { useCallback, useState } from 'react';
import type { Status } from '../api';
import { Attribution, Busy, ErrorNote, Ledger } from '../components/Data';
import { useOnce } from '../components/Flow';
import { Button } from '../components/Inputs';
import { Section } from '../components/Layout';
import { genreLabel, standingPhrase } from '../lib/copy';
import type { Game } from '../lib/game';

export function Obituary({ game, status, onAgain }: { game: Game; status: Status; onAgain: () => void }) {
  const [error, setError] = useState<string | null>(null);
  const ob = useOnce(useCallback(() => game.api.obituary(), [game]), (e) => setError(String(e)));
  return (
    <main className="shell" style={{ paddingTop: 'clamp(48px, 12vh, 140px)', paddingBottom: 96, maxWidth: 880 }}>
      <p className="eyebrow rise">In memoriam · {status.age}</p>
      <h1 className="display rise" style={{ marginTop: 18, fontSize: 'clamp(44px, 8vw, 104px)' }}>
        A life in <em>pictures</em>
      </h1>
      <ErrorNote error={error} />
      {!ob ? <Busy label="Writing it up" /> : (
        <>
          <p className="lede rise" style={{ marginTop: 28 }}>
            They came to chase {game.ambition.toLowerCase()}. They left {standingPhrase(status.standing_summary)}.
          </p>
          <div style={{ marginTop: 40 }}>
            <Attribution lines={[
              ['Credits', String(ob.credits)],
              ['Roles turned down', String(ob.declined.length)],
              ['Relationships kept', String(ob.kept)],
              ['Relationships lost', String(ob.lost)],
            ]} />
          </div>
          {ob.best_hidden_performance && (
            <Section title="The one nobody noticed">
              <p className="dim">A {genreLabel(ob.best_hidden_performance.genre).toLowerCase()} film: {ob.best_hidden_performance.band} work, and almost nobody saw it.</p>
            </Section>
          )}
          <Section title="The ones that got away" hint="Roles you passed on, and what became of them.">
            <Ledger items={ob.declined.slice(0, 6).map((d) => `A ${genreLabel(d.genre).toLowerCase()} film: ${d.roi_band}, ${d.critic_band} reviews.`)}
              empty="You said yes to everything. Some would call that a career." />
          </Section>
          <div style={{ marginTop: 48 }}><Button variant="primary" onClick={onAgain}>Another life →</Button></div>
        </>
      )}
    </main>
  );
}
