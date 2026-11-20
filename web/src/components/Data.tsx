import { useEffect, useState, type ReactNode } from 'react';

export function Tag({ children, accent }: { children: ReactNode; accent?: boolean }) {
  return <span className={accent ? 'tag tag-accent' : 'tag'}>{children}</span>;
}

export function TagList({ tags }: { tags: (string | { label: string; accent?: boolean })[] }) {
  if (!tags.length) return null;
  return (
    <>
      {tags.map((t) => typeof t === 'string'
        ? <Tag key={t}>{t}</Tag>
        : <Tag key={t.label} accent={t.accent}>{t.label}</Tag>)}
    </>
  );
}

/** The calendar widget (ux/02): quarter blocks, filled as they're spent. */
export function Quarters({ used, total = 4, size = 12 }: { used: number; total?: number; size?: number }) {
  return (
    <span className="row" style={{ gap: 6 }} role="img" aria-label={`${used} of ${total} quarters`}>
      {Array.from({ length: total }, (_, i) => (
        <span key={i} style={{
          width: size, height: size, borderRadius: '50%',
          border: `1px solid ${i < used ? 'var(--accent)' : 'var(--line-strong)'}`,
          background: i < used ? 'var(--accent)' : 'transparent',
          boxShadow: i < used ? '0 0 12px var(--accent-glow)' : 'none',
        }} />
      ))}
    </span>
  );
}

/** ux/05's attribution card: ordered cause → effect lines, max four, revealed in order. */
export function Attribution({ lines }: { lines: [label: string, value: ReactNode][] }) {
  return (
    <dl className="reveal" style={{ borderTop: '1px solid var(--line)' }}>
      {lines.slice(0, 4).map(([k, v]) => (
        <div key={k} className="spread" style={{ padding: '18px 0', borderBottom: '1px solid var(--line)' }}>
          <dt className="eyebrow">{k}</dt>
          <dd className="title" style={{ textAlign: 'right' }}>{v}</dd>
        </div>
      ))}
    </dl>
  );
}

/** Label/value rows for detail panels. Rows with null/undefined/'' values are skipped. */
export function KeyValueList({ rows }: { rows: [label: string, value: ReactNode][] }) {
  const shown = rows.filter(([, v]) => v !== null && v !== undefined && v !== '');
  return (
    <dl>
      {shown.map(([k, v]) => (
        <div key={k} className="spread" style={{ padding: '10px 0', borderBottom: '1px solid var(--line)' }}>
          <dt className="mono faint">{k}</dt>
          <dd style={{ textAlign: 'right' }}>{v}</dd>
        </div>
      ))}
    </dl>
  );
}

/** A plain list of sentences (trades, declined roles, events). */
export function Ledger({ items, empty }: { items: ReactNode[]; empty?: ReactNode }) {
  if (!items.length) return <EmptyState>{empty ?? 'Nothing here.'}</EmptyState>;
  return (
    <ul style={{ listStyle: 'none', padding: 0 }}>
      {items.map((it, i) => (
        <li key={i} style={{ padding: '12px 0', borderBottom: '1px solid var(--line)' }}>{it}</li>
      ))}
    </ul>
  );
}

/** ux/05: "silence is a valid screen state." A quiet line, not filler. */
export function EmptyState({ children }: { children: ReactNode }) {
  return <p className="dim" style={{ padding: '18px 0', fontStyle: 'italic' }}>{children}</p>;
}

export function Busy({ label = 'Rolling' }: { label?: string }) {
  const [dots, setDots] = useState('');
  useEffect(() => {
    const t = setInterval(() => setDots((d) => (d.length >= 3 ? '' : d + '.')), 280);
    return () => clearInterval(t);
  }, []);
  return <p className="eyebrow" role="status" style={{ padding: '24px 0' }}>{label}{dots}</p>;
}

export function ErrorNote({ error }: { error: string | null | undefined }) {
  if (!error) return null;
  return <p className="mono" role="alert" style={{ color: 'var(--danger)', marginTop: 16 }}>{error}</p>;
}
