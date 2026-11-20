// One acting project, Offer Board → Post & Release → Season (ux/03), declared as flow steps.
// Implements gameplay-simplification-review.md §4: one push per beat, auto unless opened, don't
// ask what the engine ignores.
import { useCallback, useState } from 'react';
import type { Listing, ReleaseSummary } from '../api';
import { Attribution, Busy, EmptyState, KeyValueList, Quarters, TagList } from '../components/Data';
import { type FlowStep, type StepProps, useAction, useOnce } from '../components/Flow';
import { Button, ChoiceGroup, Segmented, Toggle } from '../components/Inputs';
import { Card, CardGrid, Screen, Section } from '../components/Layout';
import { AWARD_LABELS, CARRYING_DIAL, DEFAULT_POSITION } from '../lib/content';
import { billingLabel, filmTitle, genreLabel, listingTags, money, pretty, whyThisRole } from '../lib/copy';
import type { FlowBase } from '../lib/game';
import { toItems } from '../lib/options';

export interface ActingCtx extends FlowBase {
  listing?: Listing;
  title?: string;
  approvals?: boolean;
  release?: ReleaseSummary;
}

const BOARD_CAP = 6;

// ---------------------------------------------------------------- 1. the offer board

function OfferBoard({ ctx, next, finish, fail }: StepProps<ActingCtx>) {
  const g = ctx.game.api;
  const { busy, run } = useAction();
  const loaded = useOnce(useCallback(() => g.offerBoard(), [g]), fail);
  const [extra, setExtra] = useState<Listing[]>([]);
  const [pushed, setPushed] = useState(false);
  if (!loaded) return <Screen eyebrow={`Age ${ctx.status.age} · the offer board`} title="Checking the phone…"><Busy /></Screen>;

  const all = [...loaded, ...extra];
  const open = all.filter((o) => o.available).sort((a, b) => b.fee_millions - a.fee_millions).slice(0, BOARD_CAP);
  const missed = all.length - all.filter((o) => o.available).length;

  const take = (o: Listing) => run(async () => {
    await g.accept(o.index);
    next({ listing: o, title: filmTitle(ctx.game.seed, ctx.status.age, o.index) });
  }, fail);
  const pushHarder = () => run(async () => { setExtra(await g.moreListings()); setPushed(true); }, fail);
  const pass = () => run(async () => {
    const gone = await g.declineBoard();
    finish({ outcome: gone.length ? `You passed. ${gone.length} film${gone.length > 1 ? 's' : ''} went to someone else.` : 'A quiet year. Nothing came through.' });
  }, fail);

  return (
    <Screen
      eyebrow={`Age ${ctx.status.age} · the offer board`}
      title={open.length ? 'This year’s offers' : 'Nothing came through'}
      lede={`${missed} audition${missed === 1 ? '' : 's'} went nowhere this year.${open.length ? ' These came back.' : ' It happens. It happens a lot.'}`}
      footer={<>
        <Button variant="ghost" onClick={pushHarder} disabled={pushed || busy}>
          {pushed ? 'Your agent pushed. That’s all of it.' : 'Have your agent push harder'}
        </Button>
        <Button onClick={pass} disabled={busy}>Pass this year</Button>
      </>}
    >
      {open.length ? (
        <CardGrid min={280}>
          {open.map((o) => (
            <Card
              key={o.index}
              eyebrow={`${billingLabel(o.billing)} · ${genreLabel(o.genre)}${o.secondary_genre ? ` / ${genreLabel(o.secondary_genre)}` : ''}`}
              title={filmTitle(ctx.game.seed, ctx.status.age, o.index)}
              tags={<TagList tags={[...(o.guaranteed ? [{ label: 'Guaranteed', accent: true }] : []), ...listingTags(o)]} />}
              highlight={o.guaranteed}
              actions={<>
                <span className="mono" style={{ marginRight: 'auto' }}>{money(o.fee_millions)}</span>
                <Quarters used={o.quarters_required} size={9} />
                <Button variant="primary" onClick={() => take(o)} disabled={busy}>Take it</Button>
              </>}
            >
              <p>“{whyThisRole(o)}”</p>
              <p className="faint" style={{ marginTop: 8, fontSize: 13 }}>{o.studio_name}</p>
            </Card>
          ))}
        </CardGrid>
      ) : <EmptyState>The phone didn’t ring. Your agent says next year. Your agent always says next year.</EmptyState>}
    </Screen>
  );
}

// ---------------------------------------------------------------- 2. holdout

function Holdout({ ctx, next, finish, fail }: StepProps<ActingCtx>) {
  const { busy, run } = useAction();
  const hold = () => run(async () => {
    const r = await ctx.game.api.requestHoldout();
    if (!r.proceeds) return finish({ outcome: 'They called your bluff and recast the part.' });
    next({ outcome: r.paid ? `They paid. Your fee went up ${r.raise_multiplier}×.` : undefined });
  }, fail);
  return (
    <Screen eyebrow={`${ctx.title} · the franchise`} title="They can’t do this one without you."
      lede="You could hold out for more. They could also call your bluff.">
      <ChoiceGroup label="Holdout" value={null} onChange={(v) => (v === 'hold' ? hold() : next())} items={[
        { value: 'hold', label: 'Hold out for more', sub: 'Big raise, or recast. Agents say it’s usually the raise.', disabled: busy },
        { value: 'sign', label: 'Sign at the original terms', sub: 'Stay friends with the studio.', disabled: busy },
      ]} />
    </Screen>
  );
}

// ---------------------------------------------------------------- 3. the deal (at most two live options)

function Deal({ ctx, next, fail }: StepProps<ActingCtx>) {
  const g = ctx.game.api;
  const { busy, run } = useAction();
  const fork = useOnce(useCallback(async () => {
    if (await g.approvalsAvailable()) return 'approvals' as const;
    if (await g.bonusAvailable('first_dollar_gross')) return 'first_dollar_gross' as const;
    return 'net_points' as const; // `when` guaranteed one of these is live
  }, [g]), fail);
  if (!fork) return <Screen eyebrow={`${ctx.title} · the deal`} title="Your agent is on the phone"><Busy /></Screen>;
  const fee = ctx.listing ? money(ctx.listing.fee_millions) : '';
  const items = fork === 'approvals'
    ? [{ value: 'money', label: 'Take the money', sub: `${fee}, standard billing.` },
       { value: 'say', label: 'Take less, get more say', sub: 'A smaller fee for script and co-star approval.' }]
    : [{ value: 'money', label: 'Take the fee', sub: `${fee}, clean.` },
       { value: 'say', label: fork === 'first_dollar_gross' ? 'Take first-dollar gross' : 'Take a backend point',
         sub: fork === 'first_dollar_gross' ? 'Paid from dollar one, whatever the film does.' : 'A share of real profit, if the studio ever admits to any.' }];
  const choose = (v: string) => run(async () => {
    const say = v === 'say';
    await g.chooseDeal(fork === 'approvals' && say, fork !== 'approvals' && say, fork === 'approvals' ? 'net_points' : fork);
    next({ approvals: fork === 'approvals' && say });
  }, fail);
  return (
    <Screen eyebrow={`${ctx.title} · the deal`} title={`${ctx.title}: the deal`}>
      <ChoiceGroup label="The deal" value={null} onChange={choose} items={items.map((i) => ({ ...i, disabled: busy }))} />
    </Screen>
  );
}

function ScriptNotes({ ctx, next, fail }: StepProps<ActingCtx>) {
  const { busy, run } = useAction();
  return (
    <Screen eyebrow={`${ctx.title} · script approval`} title="You earned a say. Use it?">
      <ChoiceGroup label="Script note" value={null}
        onChange={(k) => run(async () => { await ctx.game.api.chooseScriptNote(k); next(); }, fail)}
        items={toItems(ctx.options.script_notes).map((i) => ({ ...i, disabled: busy }))} />
    </Screen>
  );
}

// ---------------------------------------------------------------- 4. prep

function Prep({ ctx, next, fail }: StepProps<ActingCtx>) {
  const { busy, run } = useAction();
  return (
    <Screen eyebrow={`${ctx.title} · prep`} title="How do you get there?" lede="The last calm screen before the shoot.">
      <ChoiceGroup label="Prep" columns="auto" value={null}
        onChange={(k) => run(async () => { await ctx.game.api.choosePrep(k); next(); }, fail)}
        items={toItems(ctx.options.prep, 'prep').map((i) => ({ ...i, label: pretty(String(i.value)), disabled: busy }))} />
    </Screen>
  );
}

// ---------------------------------------------------------------- 5. the shoot: one read per scene

function Shoot({ ctx, next, fail }: StepProps<ActingCtx>) {
  const g = ctx.game.api;
  const episodes = useOnce(useCallback(() => g.episodeLabels(), [g]), fail);
  const { busy, run } = useAction();
  const [beat, setBeat] = useState(0);
  const [read, setRead] = useState<string | null>(null);
  const [byDial, setByDial] = useState(false);
  const [dials, setDials] = useState<Record<string, string>>({});
  if (!episodes) return <Screen eyebrow={`${ctx.title} · the shoot`} title="Call sheet’s out"><Busy /></Screen>;

  const scenes = ctx.options.scenes;
  const total = episodes.length * scenes.length;
  const episode = episodes[Math.floor(beat / scenes.length)];
  const scene = scenes[beat % scenes.length];
  const carrying = CARRYING_DIAL[ctx.listing?.genre ?? ''] ?? 'energy';
  const positions = toItems(ctx.options.positions, 'positions');
  const dialLabel = Object.fromEntries(ctx.options.dials);

  const commit = () => run(async () => {
    const choices = Object.fromEntries(ctx.options.dials.map(([d]) => [d, byDial ? dials[d] ?? DEFAULT_POSITION : d === carrying ? read! : DEFAULT_POSITION]));
    await g.playScene(choices);
    if (beat + 1 >= total) return next();
    setBeat(beat + 1); setRead(null); setDials({});
  }, fail);

  return (
    <Screen
      eyebrow={`${ctx.title} · the shoot${episode ? ` · ${episode}` : ''}`}
      title={`Scene ${(beat % scenes.length) + 1} of ${scenes.length}: ${scene}`}
      lede={byDial ? 'Every dial, your call.' : `${dialLabel[carrying]} carries this one. How do you play it?`}
      footer={<>
        <Toggle checked={byDial} onChange={setByDial}>Work it dial by dial</Toggle>
        <Button variant="primary" disabled={busy || (!byDial && !read)} onClick={commit}>
          {beat + 1 >= total ? 'That’s a wrap' : 'Next scene →'}
        </Button>
      </>}
    >
      <div className="row" style={{ marginBottom: 20 }}><Quarters used={beat} total={total} size={8} /></div>
      {byDial ? (
        <div className="stack" style={{ ['--stack' as string]: '18px' }}>
          {ctx.options.dials.map(([d, label]) => (
            <div key={d} className="spread">
              <span className="eyebrow">{label}{d === carrying ? ' · carries the scene' : ''}</span>
              <Segmented label={label} items={positions} value={dials[d] ?? DEFAULT_POSITION} onChange={(v) => setDials({ ...dials, [d]: v })} />
            </div>
          ))}
        </div>
      ) : (
        <ChoiceGroup label="Your read" columns="auto" value={read} onChange={setRead} items={positions} />
      )}
    </Screen>
  );
}

// ---------------------------------------------------------------- 6. rating (only a real fight)

function Rating({ ctx, next, fail }: StepProps<ActingCtx>) {
  const { busy, run } = useAction();
  return (
    <Screen eyebrow={`${ctx.title} · the rating`} title="It’s landing right on the line.">
      <ChoiceGroup label="Rating" value={null}
        onChange={(k) => run(async () => { await ctx.game.api.chooseRatingStance(k); next(); }, fail)}
        items={toItems(ctx.options.rating_cut).map((i) => ({ ...i, disabled: busy }))} />
    </Screen>
  );
}

// ---------------------------------------------------------------- 7. release request

function Release({ ctx, next, fail }: StepProps<ActingCtx>) {
  const { busy, run } = useAction();
  const [ask, setAsk] = useState<string>('wide');
  const [keep, setKeep] = useState(false);
  const go = () => run(async () => next({ release: await ctx.game.api.chooseRelease(ask, keep ? 'self' : 'best') }), fail);
  return (
    <Screen
      eyebrow={`${ctx.title} · post & release`}
      title="Your ask to the studio"
      lede="It’s a request. The studio usually decides."
      footer={<>
        <Toggle checked={keep} onChange={setKeep}>If it goes to auction, keep it and release it ourselves</Toggle>
        <Button variant="primary" onClick={go} disabled={busy}>{busy ? 'Opening…' : 'Release it'}</Button>
      </>}
    >
      <ChoiceGroup label="Release" columns="auto" value={ask} onChange={setAsk}
        items={toItems(ctx.options.release, 'release', ['shelved'])} />
    </Screen>
  );
}

// ---------------------------------------------------------------- 8. the reveal (ux/03 §5)

function Reveal({ ctx, next }: StepProps<ActingCtx>) {
  const r = ctx.release!;
  const [detail, setDetail] = useState(false);
  const series = r.n_episodes !== undefined;
  const lines: [string, string][] = [
    ['Your work', r.performance_band],
    [series ? 'The season' : 'The release', series ? `${r.n_episodes} episodes` : (r.release_label ?? '').split(' — ')[0] + (r.studio_overruled ? ' (overruled)' : '')],
    ['Critics', r.critic_band],
    [series ? 'Audience' : 'Box office', series ? r.audience_band : r.roi_band],
  ];
  return (
    <Screen eyebrow={`${ctx.title} · reception`} title={`${ctx.title}`}
      footer={<>
        <Button variant="ghost" onClick={() => setDetail(!detail)}>{detail ? 'Hide the numbers' : 'See the numbers'}</Button>
        <Button variant="primary" onClick={() => next({ outcome: `${ctx.title}: ${r.critic_band} reviews, ${r.roi_band}.` })}>Continue</Button>
      </>}
    >
      <Attribution lines={lines} />
      {detail && (
        <div style={{ marginTop: 28 }}>
          <KeyValueList rows={[
            ['Studio', r.studio_name],
            ['Critic score', `${r.critic_score}/100`],
            ['Budget', money(r.budget_millions)],
            ['Marketing', money(r.marketing_millions)],
            ['Gross', r.gross_millions !== undefined ? money(r.gross_millions) : null],
            ['License', r.license_value_millions !== undefined ? money(r.license_value_millions) : null],
            ['ROI', `${r.roi.toFixed(2)}×`],
            ['Rated', r.rating_band ? `${r.rating_band}${r.rating_cut_forced ? ' (studio forced a cut)' : ''}` : null],
            ['Sold to', r.bid_taken ? `${r.bid_taken.studio_name}, ${money(r.bid_taken.payout_millions)}${r.bid_taken.kept_it ? ' (kept it)' : ''}` : null],
            ['Your bonus', r.box_office_bonus_millions ? money(r.box_office_bonus_millions) : null],
            ['Renewed', series && r.renewable ? (r.renewed ? 'Yes' : 'No') : null],
          ]} />
        </div>
      )}
    </Screen>
  );
}

// ---------------------------------------------------------------- 9. the season: awards, if it fires

function Awards({ ctx, finish, fail }: StepProps<ActingCtx>) {
  const g = ctx.game.api;
  const cats = useOnce(useCallback(() => g.awardCategories(), [g]), fail);
  const [cat, setCat] = useState<string | null>(null);
  const { busy, run } = useAction();
  if (!cats) return <Screen eyebrow="Awards season" title="The trades are talking"><Busy /></Screen>;
  const campaign = (spend: number) => run(async () => {
    const r = await g.runAwards(cat ?? cats[0], spend);
    const label = AWARD_LABELS[r.category] ?? pretty(r.category);
    finish({ outcome: r.won ? `${ctx.title} won ${label}.` : r.nominated ? `${ctx.title} was nominated for ${label}. Not this year.` : `You campaigned for ${label}. The voters looked elsewhere.` });
  }, fail);
  return (
    <Screen eyebrow="Awards season" title={`Campaign for ${ctx.title}?`}
      footer={<>
        <Button variant="ghost" onClick={() => finish()} disabled={busy}>Stay quiet</Button>
        <div className="row">
          <Button onClick={() => campaign(1)} disabled={busy}>A quiet push ($1M)</Button>
          <Button variant="primary" onClick={() => campaign(3)} disabled={busy}>Go hard ($3M)</Button>
        </div>
      </>}
    >
      <Section title="Category" style={{ marginTop: 0 }}>
        <ChoiceGroup label="Category" columns="auto" dense value={cat ?? cats[0]} onChange={setCat}
          items={cats.map((c) => ({ value: c, label: AWARD_LABELS[c] ?? pretty(c) }))} />
      </Section>
    </Screen>
  );
}

export const actingSteps: FlowStep<ActingCtx>[] = [
  { id: 'board', render: (p) => <OfferBoard {...p} /> },
  { id: 'holdout', when: (c) => c.game.api.holdoutAvailable(), render: (p) => <Holdout {...p} /> },
  {
    id: 'deal',
    when: async (c) => (await c.game.api.approvalsAvailable()) || (await c.game.api.bonusAvailable('net_points')),
    onSkip: async (c) => { await c.game.api.chooseDeal(false); },
    render: (p) => <Deal {...p} />,
  },
  { id: 'notes', when: async (c) => !!c.approvals && (await c.game.api.scriptNotesAvailable()), render: (p) => <ScriptNotes {...p} /> },
  { id: 'prep', render: (p) => <Prep {...p} /> },
  { id: 'shoot', render: (p) => <Shoot {...p} /> },
  { id: 'rating', when: async (c) => (await c.game.api.ratingPreview()).cut_available, render: (p) => <Rating {...p} /> },
  { id: 'release', render: (p) => <Release {...p} /> },
  { id: 'reveal', render: (p) => <Reveal {...p} /> },
  {
    id: 'awards',
    when: async (c) => (await c.game.api.awardsAvailable()) && (await c.game.api.awardCategories()).length > 0,
    render: (p) => <Awards {...p} />,
  },
];
