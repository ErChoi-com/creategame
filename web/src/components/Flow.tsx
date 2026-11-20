import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { Busy, ErrorNote } from './Data';

/**
 * A multi-step decision sequence declared as data. Each step can:
 *   - when(ctx):   decide whether it applies at all (e.g. "holdout only if indispensable"); may
 *                  return a context patch instead of `true` to hand the step data it fetched
 *   - onSkip(ctx): resolve itself with a sensible default when it doesn't apply
 *                  ("auto unless opened", gameplay-simplification-review §4)
 *   - render(p):   draw its screen, then call next(patch) or finish(patch)
 * The context object accumulates what earlier steps learned.
 */
export interface FlowStep<C> {
  id: string;
  when?: (ctx: C) => boolean | Partial<C> | null | Promise<boolean | Partial<C> | null>;
  onSkip?: (ctx: C) => Promise<Partial<C> | void>;
  render: (p: StepProps<C>) => ReactNode;
}

export interface StepProps<C> {
  ctx: C;
  next: (patch?: Partial<C>) => void;
  finish: (patch?: Partial<C>) => void;
  fail: (e: unknown) => void;
}

export function Flow<C>({ steps, initial, onDone }: { steps: FlowStep<C>[]; initial: C; onDone: (ctx: C) => void }) {
  const [index, setIndex] = useState<number | null>(null); // null while resolving which step is next
  const [ctx, setCtx] = useState<C>(initial);
  const [error, setError] = useState<string | null>(null);
  const started = useRef(false);

  const advance = useCallback(async (from: number, current: C) => {
    setIndex(null);
    let c = current;
    for (let i = from; i < steps.length; i++) {
      const s = steps[i];
      try {
        const applies = s.when ? await s.when(c) : true;
        if (applies) {
          if (typeof applies === 'object') c = { ...c, ...applies };
          setCtx(c);
          setIndex(i);
          return;
        }
        if (s.onSkip) {
          const patch = await s.onSkip(c);
          if (patch) c = { ...c, ...patch };
        }
      } catch (e) {
        setCtx(c);
        setError((e as Error).message);
        return;
      }
    }
    onDone(c);
  }, [steps, onDone]);

  useEffect(() => {
    if (started.current) return; // StrictMode runs effects twice; engine calls must run once
    started.current = true;
    void advance(0, initial);
  }, [advance, initial]);

  if (error) {
    return (
      <div className="push"><div className="push-inner">
        <p className="eyebrow">Something broke on set</p>
        <ErrorNote error={error} />
        <button className="btn" style={{ marginTop: 24 }} onClick={() => onDone(ctx)}>Back to the hub</button>
      </div></div>
    );
  }
  if (index === null) return <div className="push"><div className="push-inner"><Busy /></div></div>;

  const step = steps[index];
  return (
    <div key={step.id}>
      {step.render({
        ctx,
        next: (patch) => void advance(index + 1, { ...ctx, ...patch }),
        finish: (patch) => onDone({ ...ctx, ...patch }),
        fail: (e) => setError(e instanceof Error ? e.message : String(e)),
      })}
    </div>
  );
}

/** Run an async action from a step with a busy flag and error capture. */
export function useAction() {
  const [busy, setBusy] = useState(false);
  const run = useCallback(async <T,>(fn: () => Promise<T>, fail: (e: unknown) => void): Promise<T | undefined> => {
    setBusy(true);
    try {
      return await fn();
    } catch (e) {
      fail(e);
      return undefined;
    } finally {
      setBusy(false);
    }
  }, []);
  return { busy, run };
}

/** Load data once on mount (guarded against StrictMode's double effect). */
export function useOnce<T>(load: () => Promise<T>, fail: (e: unknown) => void): T | null {
  const [data, setData] = useState<T | null>(null);
  const done = useRef(false);
  useEffect(() => {
    if (done.current) return;
    done.current = true;
    load().then(setData).catch(fail);
  }, [load, fail]);
  return data;
}
