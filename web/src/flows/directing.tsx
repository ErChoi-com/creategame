// The directing career as flow steps. Per gameplay-simplification-review.md §4, development is one
// standing order per project per year; the UI spends the quarters, the player sets the orders.
import { useCallback, useState } from 'react';
import type { DirectingResult, DirectorProject, DirectorStatus, HireOffer } from '../api';
import { Busy, EmptyState, Ledger, Quarters, TagList } from '../components/Data';
import { type FlowStep, type StepProps, useAction, useOnce } from '../components/Flow';
import { Button, ChoiceGroup, Segmented } from '../components/Inputs';
import { Card, CardGrid, Screen, Section } from '../components/Layout';
import { PRIMARY_DEV_ACTIONS } from '../lib/content';
import { genreLabel, money } from '../lib/copy';
import type { FlowBase } from '../lib/game';
import { toItems } from '../lib/options';

export interface DirectingCtx extends FlowBase {
  hireOffer?: HireOffer;
  results?: string[];
}

/** One plain sentence per development/production outcome (ux/05 attribution register). */
export function directingLine(project: string, r: DirectingResult): string {
  if (r.error) return `${project}: ${r.error}.`;
  if (r.greenlit && !r.resolved) return `${project} is greenlit. Cameras are rolling${r.quarters_remaining_in_shoot ? `, ${r.quarters_remaining_in_shoot} quarter(s) to go` : ''}.`;
  if (r.greenlit) return `${project} wrapped.`;
  if (r.blocked_on_money) return `${project} is ready to shoot, but you're ${money(r.shortfall ?? 0)} short.`;
  if (r.dead) return `${project} died in development hell.`;
  if (r.frozen) return `${project} went in the drawer.`;
  return `${project} is still in development. Momentum: ${r.momentum_band}.`;
}

const projectKey = (p: DirectorProject) => `${p.genre}:${p.budget_ask}`;
const projectName = (p: DirectorProject) => `The ${genreLabel(p.genre).toLowerCase()} (${money(p.budget_ask)})`;
const isActive = (p: DirectorProject) => !p.frozen && !p.shooting;

// ---------------------------------------------------------------- become a director

function StepBehind({ ctx, next, finish, fail }: StepProps<DirectingCtx>) {
  const { busy, run } = useAction();
  return (
    <Screen eyebrow="A second career" title="Step behind the camera?"
      lede="Directing runs on the same calendar. Projects take years, and most of them die."
      footer={<>
        <Button variant="ghost" onClick={() => finish()}>Not yet</Button>
        <Button variant="primary" disabled={busy} onClick={() => run(async () => { await ctx.game.api.becomeDirector(); next(); }, fail)}>
          Call action
        </Button>
      </>} />
  );
}

// ---------------------------------------------------------------- a studio calls (hire offer)

function Hire({ ctx, next, fail }: StepProps<DirectingCtx>) {
  const { busy, run } = useAction();
  const o = ctx.hireOffer!;
  const accept = () => run(async () => {
    const r = await ctx.game.api.acceptHireOffer();
    next({ results: [directingLine(`${o.studio_name}'s ${genreLabel(o.genre).toLowerCase()}`, r)] });
  }, fail);
  return (
    <Screen eyebrow="The phone rings" title={`${o.studio_name} wants you to direct.`}
      lede={`A ${genreLabel(o.genre).toLowerCase()} picture, about ${money(o.budget_millions)}, already greenlit. Their film, your name on it.`}>
      <ChoiceGroup label="Hire offer" value={null}
        onChange={(v) => (v === 'yes' ? accept() : run(async () => { await ctx.game.api.declineHireOffer(); next(); }, fail))}
        items={[
          { value: 'yes', label: 'Take the job', sub: 'Skip development hell. Spend the quarters.', disabled: busy },
          { value: 'no', label: 'Pass', sub: 'Keep the year for your own slate.', disabled: busy },
        ]} />
    </Screen>
  );
}

// ---------------------------------------------------------------- the slate: pitch + standing orders

function Slate({ ctx, next, fail }: StepProps<DirectingCtx>) {
  const g = ctx.game.api;
  const initial = useOnce(useCallback(() => g.directorStatus(), [g]), fail);
  const [status, setStatus] = useState<DirectorStatus | null>(null);
  const [orders, setOrders] = useState<Record<string, string>>({});
  const [genre, setGenre] = useState<string | null>(null);
  const [tier, setTier] = useState<string>('low');
  const { busy, run } = useAction();
  const st = status ?? initial;
  if (!st) return <Screen eyebrow="Directing" title="Your slate"><Busy /></Screen>;

  const actions = toItems(ctx.options.director_dev_actions);
  const primary = actions.filter((a) => PRIMARY_DEV_ACTIONS.includes(String(a.value)));
  const active = st.projects.filter(isActive);
  const orderFor = (p: DirectorProject) => orders[projectKey(p)] ?? 'take_to_market';

  const pitch = () => run(async () => {
    if (!genre) return;
    await g.startDirecting(genre, tier);
    setStatus(await g.directorStatus());
    setGenre(null);
  }, fail);

  const runYear = () => run(async () => {
    const lines: string[] = [...(ctx.results ?? [])];
    let s = st;
    const done = new Set<string>();
    // Round-robin the year's quarters across projects that still have an open order.
    for (let guard = 0; guard < 16 && (await g.quartersRemaining()) > 0; guard++) {
      const queue = s.projects.filter((p) => isActive(p) && !done.has(projectKey(p)));
      if (!queue.length) break;
      for (const p of queue) {
        if ((await g.quartersRemaining()) <= 0) break;
        const cur = (await g.directorStatus()).projects.find((q) => projectKey(q) === projectKey(p));
        if (!cur || !isActive(cur)) { done.add(projectKey(p)); continue; }
        const r = await g.advanceDirecting(cur.index, orderFor(p));
        if (r.greenlit || r.dead || r.frozen || r.blocked_on_money || r.error) {
          lines.push(directingLine(projectName(p), r));
          done.add(projectKey(p));
        }
        if (orderFor(p) === 'drawer') done.add(projectKey(p));
      }
      s = await g.directorStatus();
    }
    for (const p of s.projects.filter(isActive)) {
      if (!lines.some((l) => l.startsWith(projectName(p)))) lines.push(`${projectName(p)} is still in development. Momentum: ${p.momentum_band}.`);
    }
    next({ results: lines, outcome: lines[lines.length - 1] });
  }, fail);

  return (
    <Screen
      eyebrow={`Directing · ${st.standing} · ${st.credits} credit${st.credits === 1 ? '' : 's'}`}
      title="Your slate"
      lede="One standing order per project. The year spends itself."
      footer={<>
        <span className="row mono faint">This year <Quarters used={st.quarters_this_year} total={st.quarters_per_year} /></span>
        <Button variant="primary" disabled={busy || !active.length} onClick={runYear}>{busy ? 'Working…' : 'Run the year →'}</Button>
      </>}
    >
      {st.projects.length ? (
        <CardGrid min={300}>
          {st.projects.map((p) => (
            <Card key={projectKey(p)} eyebrow={`${genreLabel(p.genre)} · ${money(p.budget_ask)}`} title={projectName(p)} muted={!isActive(p)}
              tags={<TagList tags={[
                `Momentum: ${p.momentum_band}`,
                `Script: ${p.script_quality_read}`,
                ...(p.self_financed ? ['Your money'] : []),
                ...(p.shooting ? [{ label: 'Shooting', accent: true }] : []),
                ...(p.frozen ? ['In the drawer'] : []),
              ]} />}
            >
              {isActive(p) && (
                <div className="stack" style={{ ['--stack' as string]: '10px', marginTop: 6 }}>
                  <span className="eyebrow">This year’s order</span>
                  <Segmented label="Order" items={primary.map((a) => ({ ...a, label: String(a.label).split(' — ')[0] }))}
                    value={PRIMARY_DEV_ACTIONS.includes(orderFor(p)) ? orderFor(p) : null}
                    onChange={(v) => setOrders({ ...orders, [projectKey(p)]: v })} />
                  <select aria-label="More orders" value={orderFor(p)} onChange={(e) => setOrders({ ...orders, [projectKey(p)]: e.target.value })}
                    className="mono" style={{ background: 'var(--bg)', color: 'var(--ink-dim)', border: '1px solid var(--line)', padding: 8, maxWidth: '100%' }}>
                    {actions.map((a) => <option key={a.value} value={a.value}>{String(a.label)}</option>)}
                  </select>
                </div>
              )}
            </Card>
          ))}
        </CardGrid>
      ) : <EmptyState>Nothing in development. Every career starts with a pitch.</EmptyState>}

      {st.can_start_new_project && (
        <Section title="Pitch something" index={`${st.projects.length} / ${st.max_projects} on the slate`}>
          <ChoiceGroup label="Genre" columns="auto" dense value={genre} onChange={setGenre}
            items={ctx.options.director_genres.map(([k, l]) => ({ value: k, label: l }))} />
          <div style={{ marginTop: 18 }}>
            <span className="eyebrow">Budget</span>
            <div style={{ marginTop: 8 }}><Segmented label="Budget" items={toItems(ctx.options.director_budget_tiers)} value={tier} onChange={setTier} /></div>
            <div style={{ marginTop: 16, textAlign: 'right' }}><Button disabled={!genre || busy} onClick={pitch}>Pitch it</Button></div>
          </div>
        </Section>
      )}
    </Screen>
  );
}

// ---------------------------------------------------------------- the year's directing outcomes

function Results({ ctx, finish }: StepProps<DirectingCtx>) {
  return (
    <Screen eyebrow="Directing · the year" title="How the slate moved"
      footer={<Button variant="primary" onClick={() => finish()}>Back to the hub</Button>}>
      <Ledger items={ctx.results ?? []} empty="A quiet year in development. Nothing moved, nothing died." />
    </Screen>
  );
}

export const directingSteps: FlowStep<DirectingCtx>[] = [
  { id: 'start', when: (c) => !c.status.is_directing, render: (p) => <StepBehind {...p} /> },
  {
    id: 'hire',
    when: async (c) => {
      const offer = await c.game.api.hireOffer();
      return offer ? { hireOffer: offer } : false;
    },
    render: (p) => <Hire {...p} />,
  },
  { id: 'slate', when: async (c) => (await c.game.api.quartersRemaining()) > 0, render: (p) => <Slate {...p} /> },
  { id: 'results', render: (p) => <Results {...p} /> },
];
