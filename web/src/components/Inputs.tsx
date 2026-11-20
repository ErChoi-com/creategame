import type { ButtonHTMLAttributes, ReactNode } from 'react';

type Variant = 'primary' | 'outline' | 'ghost';

export function Button({ variant = 'outline', children, ...rest }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  const cls = variant === 'primary' ? 'btn btn-primary' : variant === 'ghost' ? 'btn btn-ghost' : 'btn';
  return <button className={cls} {...rest}>{children}</button>;
}

export interface ChoiceItem<V extends string = string> {
  value: V;
  label: ReactNode;
  sub?: ReactNode;
  aside?: ReactNode;
  disabled?: boolean;
}

/** One-of-N choice rendered as large tappable rows/tiles. Every decision screen uses this. */
export function ChoiceGroup<V extends string>({ items, value, onChange, columns = 1, label, dense }: {
  items: ChoiceItem<V>[];
  value: V | null;
  onChange: (v: V) => void;
  columns?: number | 'auto';
  label?: string;
  /** Smaller tiles for long lists (genres, categories). */
  dense?: boolean;
}) {
  const cols = columns === 'auto' ? `repeat(auto-fit, minmax(min(${dense ? 150 : 240}px, 100%), 1fr))` : `repeat(${columns}, minmax(0, 1fr))`;
  return (
    <div className={dense ? 'choices dense' : 'choices'} role="radiogroup" aria-label={label} style={{ gridTemplateColumns: cols }}>
      {items.map((it) => (
        <button
          key={it.value}
          className="choice"
          role="radio"
          aria-checked={value === it.value}
          aria-pressed={value === it.value}
          disabled={it.disabled}
          onClick={() => onChange(it.value)}
        >
          <span className="spread" style={{ alignItems: 'center' }}>
            <span className="label">{it.label}</span>
            {it.aside}
          </span>
          {it.sub && <span className="sub">{it.sub}</span>}
        </button>
      ))}
    </div>
  );
}

/** Compact segmented control for small option sets; wraps into a grid on narrow screens. */
export function Segmented<V extends string>({ items, value, onChange, label }: {
  items: ChoiceItem<V>[];
  value: V | null;
  onChange: (v: V) => void;
  label?: string;
}) {
  return (
    <div role="radiogroup" aria-label={label} className="segmented mono">
      {items.map((it) => (
        <button key={it.value} role="radio" aria-checked={value === it.value} disabled={it.disabled} onClick={() => onChange(it.value)}>
          {it.label}
        </button>
      ))}
    </div>
  );
}

/** A yes/no toggle that reads as a sentence. */
export function Toggle({ checked, onChange, children }: { checked: boolean; onChange: (v: boolean) => void; children: ReactNode }) {
  return (
    <label className="row" style={{ cursor: 'pointer', gap: 12 }}>
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} style={{ accentColor: 'var(--accent)', width: 16, height: 16 }} />
      <span>{children}</span>
    </label>
  );
}

/** Generic tab bar; tabs are data ({id, label}), content is rendered by the caller. */
export function Tabs<T extends string>({ tabs, active, onChange }: { tabs: { id: T; label: string }[]; active: T; onChange: (t: T) => void }) {
  return (
    <nav className="row" role="tablist" style={{ gap: 28, borderBottom: '1px solid var(--line)' }}>
      {tabs.map((t) => (
        <button
          key={t.id}
          role="tab"
          aria-selected={active === t.id}
          onClick={() => onChange(t.id)}
          className="eyebrow"
          style={{
            padding: '14px 0', marginBottom: -1,
            color: active === t.id ? 'var(--ink)' : 'var(--ink-faint)',
            borderBottom: `1px solid ${active === t.id ? 'var(--accent)' : 'transparent'}`,
          }}
        >
          {t.label}
        </button>
      ))}
    </nav>
  );
}

export function TextField({ label, value, onChange, placeholder, numeric }: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string; numeric?: boolean;
}) {
  return (
    <label className="row mono faint">
      {label}
      <input
        value={value}
        placeholder={placeholder}
        inputMode={numeric ? 'numeric' : undefined}
        onChange={(e) => onChange(numeric ? e.target.value.replace(/\D/g, '').slice(0, 9) : e.target.value)}
        style={{ background: 'transparent', border: 0, borderBottom: '1px solid var(--line-strong)', color: 'var(--ink)', font: 'inherit', width: 110, padding: '6px 2px' }}
      />
    </label>
  );
}
