import { useState } from 'react';
import { api, type NewGame, type Options } from '../api';
import { Choice, ErrorNote } from '../components/ui';

const AMBITION_GLOSS: Record<string, string> = {
  work: 'To be good. Really good. Whatever it costs.',
  prize: 'A statue on the mantel, and a speech you rehearsed in the car.',
  fortune: 'Never worry about rent again. Then never worry about anything.',
  run: 'Decades. Still working when the others have faded.',
  franchise: 'Your face on the lunchbox. Your name on the sequel.',
  voice: 'To say something with it, while they still hand you the microphone.',
};

export function CharacterCreation({ options, onBegin }: { options: Options; onBegin: (g: NewGame, ambition: string) => void }) {
  const [background, setBackground] = useState<string | null>(null);
  const [ambition, setAmbition] = useState<string | null>(null);
  const [seed, setSeed] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = async () => {
    if (!background || !ambition) return;
    setBusy(true);
    setError(null);
    try {
      const ng = await api.newGame(background, ambition, seed ? Number(seed) : undefined);
      onBegin(ng, options.ambitions.find(([k]) => k === ambition)?.[1] ?? ambition);
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  };

  return (
    <main className="shell" style={{ paddingTop: 'clamp(48px, 12vh, 140px)', paddingBottom: 96 }}>
      <section className="rise">
        <p className="eyebrow">A Hollywood life, 22 to 82</p>
        <h1 className="display" style={{ marginTop: 18 }}>
          Call<em>back</em>
        </h1>
        <p className="lede" style={{ marginTop: 28 }}>
          You do not control whether the film is good. You control what you say yes to.
        </p>
      </section>

      <section style={{ marginTop: 80 }} className="rise">
        <div className="spread" style={{ marginBottom: 18 }}>
          <h2 className="title">Where you came from</h2>
          <span className="eyebrow">01 / Background</span>
        </div>
        <div className="choices" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))' }}>
          {options.backgrounds.map(([key, name, tagline]) => (
            <Choice key={key} label={name} sub={tagline} selected={background === key} onClick={() => setBackground(key)} />
          ))}
        </div>
      </section>

      <section style={{ marginTop: 56 }} className="rise">
        <div className="spread" style={{ marginBottom: 6 }}>
          <h2 className="title">What you're chasing</h2>
          <span className="eyebrow">02 / Ambition</span>
        </div>
        <p className="dim" style={{ marginBottom: 18 }}>What your obituary will measure you against.</p>
        <div className="choices" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))' }}>
          {options.ambitions.map(([key, label]) => (
            <Choice key={key} label={label} sub={AMBITION_GLOSS[key]} selected={ambition === key} onClick={() => setAmbition(key)} />
          ))}
        </div>
      </section>

      <section style={{ marginTop: 56 }} className="spread rise">
        <label className="row mono faint">
          Seed
          <input
            value={seed}
            onChange={(e) => setSeed(e.target.value.replace(/\D/g, '').slice(0, 9))}
            placeholder="random"
            inputMode="numeric"
            style={{ background: 'transparent', border: 0, borderBottom: '1px solid var(--line-strong)', color: 'var(--ink)', font: 'inherit', width: 110, padding: '6px 2px' }}
          />
        </label>
        <button className="btn btn-primary" disabled={!background || !ambition || busy} onClick={start}>
          {busy ? 'Rolling…' : 'Take the bus to L.A. →'}
        </button>
      </section>
      <ErrorNote error={error} />
    </main>
  );
}
