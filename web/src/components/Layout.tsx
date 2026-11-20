import { useEffect, type CSSProperties, type ReactNode } from 'react';

/** A full-screen push card over the hub (ux/02, "the push interrupt"). */
export function Screen({ eyebrow, title, lede, children, footer, onClose }: {
  eyebrow: string;
  title: ReactNode;
  lede?: ReactNode;
  children?: ReactNode;
  footer?: ReactNode;
  onClose?: () => void;
}) {
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);
  return (
    <div className="push" role="dialog" aria-modal="true" aria-label={typeof title === 'string' ? title : eyebrow}>
      <div className="push-inner">
        <header className="push-head rise">
          <div className="spread">
            <span className="eyebrow">{eyebrow}</span>
            {onClose && <button className="btn btn-ghost" onClick={onClose}>← Back to the hub</button>}
          </div>
          <h1 className="headline" style={{ marginTop: 14 }}>{title}</h1>
          {lede && <p className="lede" style={{ marginTop: 14 }}>{lede}</p>}
        </header>
        <div className="rise" style={{ animationDelay: '0.12s' }}>{children}</div>
        {footer && <footer className="push-foot">{footer}</footer>}
      </div>
    </div>
  );
}

/** A titled block with an optional index label ("01 / Background") and hint line. */
export function Section({ title, index, hint, children, style }: {
  title: ReactNode;
  index?: string;
  hint?: ReactNode;
  children: ReactNode;
  style?: CSSProperties;
}) {
  return (
    <section className="rise" style={{ marginTop: 48, ...style }}>
      <div className="spread" style={{ marginBottom: hint ? 6 : 18 }}>
        <h2 className="title">{title}</h2>
        {index && <span className="eyebrow">{index}</span>}
      </div>
      {hint && <p className="dim" style={{ marginBottom: 18 }}>{hint}</p>}
      {children}
    </section>
  );
}

/** A content card: eyebrow, title, tags, body, actions. Used for offers, projects, panels. */
export function Card({ eyebrow, title, tags, children, actions, muted, highlight }: {
  eyebrow?: ReactNode;
  title?: ReactNode;
  tags?: ReactNode;
  children?: ReactNode;
  actions?: ReactNode;
  muted?: boolean;
  highlight?: boolean;
}) {
  return (
    <article className="card" style={{
      opacity: muted ? 0.45 : 1,
      boxShadow: highlight ? 'inset 2px 0 0 var(--accent)' : undefined,
      display: 'flex', flexDirection: 'column', gap: 12,
    }}>
      {eyebrow && <div className="eyebrow">{eyebrow}</div>}
      {title && <h3 className="title">{title}</h3>}
      {tags && <div className="row" style={{ gap: 6 }}>{tags}</div>}
      {children && <div className="dim" style={{ flex: 1 }}>{children}</div>}
      {actions && <div className="row" style={{ marginTop: 6 }}>{actions}</div>}
    </article>
  );
}

/** A responsive grid of cards separated by hairlines. */
export function CardGrid({ children, min = 260 }: { children: ReactNode; min?: number }) {
  return <div className="grid-cards" style={{ gridTemplateColumns: `repeat(auto-fill, minmax(min(${min}px, 100%), 1fr))` }}>{children}</div>;
}
