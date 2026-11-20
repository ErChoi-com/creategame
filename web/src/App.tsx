import { useCallback, useEffect, useState } from 'react';
import { api, gameApi, type NewGame, type Options, type Status } from './api';
import { CharacterCreation } from './screens/CharacterCreation';
import { Hub } from './screens/Hub';
import { Obituary } from './screens/Obituary';
import { Busy, ErrorNote } from './components/ui';

export interface Game { id: string; seed: number; intro: string; ambition: string; api: ReturnType<typeof gameApi> }

const SAVE_KEY = 'callback.game';

export default function App() {
  const [options, setOptions] = useState<Options | null>(null);
  const [game, setGame] = useState<Game | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Pointer parallax for the key light (styles.css .stage::before).
  useEffect(() => {
    const onMove = (e: PointerEvent) => {
      document.documentElement.style.setProperty('--px', String(e.clientX / window.innerWidth - 0.5));
      document.documentElement.style.setProperty('--py', String(e.clientY / window.innerHeight - 0.5));
    };
    window.addEventListener('pointermove', onMove);
    return () => window.removeEventListener('pointermove', onMove);
  }, []);

  useEffect(() => {
    api.options().then(setOptions).catch((e) => setError(`Can't reach the engine: ${e.message}. Is web_server.py running?`));
  }, []);

  // Resume a game still held by the server after a page reload.
  useEffect(() => {
    let saved: { id: string; seed: number; intro: string; ambition: string } | null = null;
    try { saved = JSON.parse(localStorage.getItem(SAVE_KEY) ?? 'null'); } catch { /* storage unavailable */ }
    if (!saved) return;
    const g = { ...saved, api: gameApi(saved.id) };
    g.api.status().then((s) => { setGame(g); setStatus(s); }).catch(() => {
      try { localStorage.removeItem(SAVE_KEY); } catch { /* ignore */ }
    });
  }, []);

  const refresh = useCallback(async () => {
    if (game) setStatus(await game.api.status());
  }, [game]);

  const begin = (ng: NewGame, ambition: string) => {
    const g = { id: ng.game_id, seed: ng.seed, intro: ng.intro, ambition, api: gameApi(ng.game_id) };
    try { localStorage.setItem(SAVE_KEY, JSON.stringify({ id: g.id, seed: g.seed, intro: g.intro, ambition })); } catch { /* ignore */ }
    setGame(g);
    setStatus(ng.status);
  };

  const quit = () => {
    try { localStorage.removeItem(SAVE_KEY); } catch { /* ignore */ }
    setGame(null);
    setStatus(null);
  };

  return (
    <div className="stage">
      {!options && !error && <div className="shell"><Busy label="Loading the reel" /></div>}
      <div className="shell"><ErrorNote error={error} /></div>
      {options && !game && <CharacterCreation options={options} onBegin={begin} />}
      {options && game && status && !status.is_over && (
        <Hub game={game} options={options} status={status} setStatus={setStatus} refresh={refresh} onQuit={quit} />
      )}
      {game && status?.is_over && <Obituary game={game} status={status} onAgain={quit} />}
    </div>
  );
}
