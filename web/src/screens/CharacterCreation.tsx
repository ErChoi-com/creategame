import { useState } from 'react';
import { api, type NewGame, type Options } from '../api';
import { ErrorNote } from '../components/Data';
import { Button, ChoiceGroup, TextField } from '../components/Inputs';
import { Section } from '../components/Layout';
import { toItems } from '../lib/options';

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
      <header className="rise">
        <p className="eyebrow">A Hollywood life, 22 to 82</p>
        <h1 className="display" style={{ marginTop: 18 }}>Call<em>back</em></h1>
        <p className="lede" style={{ marginTop: 28 }}>You do not control whether the film is good. You control what you say yes to.</p>
      </header>

      <Section title="Where you came from" index="01 / Background" style={{ marginTop: 80 }}>
        <ChoiceGroup label="Background" columns="auto" value={background} onChange={setBackground}
          items={options.backgrounds.map(([key, name, tagline]) => ({ value: key, label: name, sub: tagline }))} />
      </Section>

      <Section title="What you’re chasing" index="02 / Ambition" hint="What your obituary will measure you against.">
        <ChoiceGroup label="Ambition" columns="auto" value={ambition} onChange={setAmbition} items={toItems(options.ambitions, 'ambitions')} />
      </Section>

      <section className="spread rise" style={{ marginTop: 56 }}>
        <TextField label="Seed" value={seed} onChange={setSeed} placeholder="random" numeric />
        <Button variant="primary" disabled={!background || !ambition || busy} onClick={start}>
          {busy ? 'Rolling…' : 'Take the bus to L.A. →'}
        </Button>
      </section>
      <ErrorNote error={error} />
    </main>
  );
}
