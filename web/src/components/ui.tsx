import { useEffect, useState, type ReactNode } from 'react';

/** A push screen: a full-screen card over the hub (ux/02 "the push interrupt"). */
export function Push({ eyebrow, title, children, footer, onBack }: {
  eyebrow: string;
  title: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  onBack?: () => void;
}) {
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);
  return (
    <div className="push" role="dialog" aria-modal="true">
      <div className="push-inner">
        <header className="push-head rise">
          <div className="spread">
            <span className="eyebrow">{eyebrow}</span>
            {onBack && <button className="btn btn-ghost" onClick={onBack}>← Back to the hub</button>}
          </div>
          <h1 className="headline" style={{ marginTop: 14 }}>{title}</h1>
        </header>
        <div className="rise" style={{ animationDelay: '0.12s' }}>{children}</div>
        {footer && <footer className="push-foot">{footer}</footer>}
      </div>
    </div>
  );
}

export function Choice({ label, sub, selected, onClick, disabled, aside }: {
  label: ReactNode;
  sub?: ReactNode;
  selected?: boolean;
  onClick: () => void;
  disabled?: boolean;
  aside?: ReactNode;
}) {
  return (
    <button className="choice" aria-pressed={!!selected} onClick={onClick} disabled={disabled}>
      <span className="spread" style={{ alignItems: 'center' }}>
        <span className="label">{label}</span>
        {aside}
      </span>
      {sub && <span className="sub">{sub}</span>}
    </button>
  );
}

/** The calendar widget (ux/02): four quarter blocks, filled as they're spent. */
export function Quarters({ used, total = 4, size = 12 }: { used: number; total?: number; size?: number }) {
  return (
    <span className="row" style={{ gap: 6 }} aria-label={`${used} of ${total} quarters spent`}>
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

/** ux/05's attribution card: an ordered list of causes, at most four lines, revealed in order. */
export function Attribution({ lines }: { lines: [string, string][] }) {
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

export function Busy({ label = 'Rolling' }: { label?: string }) {
  const [dots, setDots] = useState('');
  useEffect(() => {
    const t = setInterval(() => setDots((d) => (d.length >= 3 ? '' : d + '.')), 280);
    return () => clearInterval(t);
  }, []);
  return <p className="eyebrow" style={{ padding: '24px 0' }}>{label}{dots}</p>;
}

export function ErrorNote({ error }: { error: string | null }) {
  if (!error) return null;
  return <p className="mono" role="alert" style={{ color: 'var(--danger)', marginTop: 16 }}>{error}</p>;
}
