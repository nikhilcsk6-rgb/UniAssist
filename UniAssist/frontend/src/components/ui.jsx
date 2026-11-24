import ReactMarkdown from 'react-markdown'

export const LANGS = [{ v: 'en', l: 'English' }, { v: 'kn', l: 'ಕನ್ನಡ (Kannada)' }, { v: 'hi', l: 'हिन्दी (Hindi)' }]

export function Spinner({ label = 'Loading...' }) {
  return (
    <span role="status" className="inline-flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" aria-hidden="true" />
      {label}
    </span>
  )
}

export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3 animate-fadeUp">
      <div>
        <h1 className="text-2xl font-bold text-navy-900 dark:text-white">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>}
      </div>
      <div className="flex flex-wrap gap-2">{children}</div>
    </div>
  )
}

export function Card({ title, children, className = '' }) {
  return (
    <section className={`card animate-fadeUp ${className}`}>
      {title && <h2 className="mb-3 text-base font-semibold text-navy-900 dark:text-white">{title}</h2>}
      {children}
    </section>
  )
}

export function StatCard({ label, value, icon }) {
  return (
    <div className="card animate-fadeUp flex items-center gap-4">
      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-100 text-xl dark:bg-brand-900" aria-hidden="true">{icon}</div>
      <div>
        <div className="text-2xl font-bold text-navy-900 dark:text-white">{value ?? '-'}</div>
        <div className="text-xs text-slate-500 dark:text-slate-400">{label}</div>
      </div>
    </div>
  )
}

export function Field({ label, id, children }) {
  return (
    <div>
      <label htmlFor={id} className="label">{label}</label>
      {children}
    </div>
  )
}

export function Empty({ children }) {
  return <p className="rounded-xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500 dark:border-navy-600 dark:text-slate-400">{children}</p>
}

export function Badge({ children, color = 'purple' }) {
  const map = {
    purple: 'bg-brand-100 text-brand-800 dark:bg-brand-900 dark:text-brand-200',
    green: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200',
    amber: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
    red: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    navy: 'bg-navy-100 text-navy-800 dark:bg-navy-700 dark:text-navy-100',
  }
  return <span className={`badge ${map[color]}`}>{children}</span>
}

// react-markdown does not render raw HTML, so model/document output cannot inject markup (XSS-safe).
export function Md({ children }) {
  return <div className="md"><ReactMarkdown>{children || ''}</ReactMarkdown></div>
}

export function LangSelect({ value, onChange, id = 'lang' }) {
  return (
    <select id={id} aria-label="Language" className="input w-auto" value={value} onChange={(e) => onChange(e.target.value)}>
      {LANGS.map((l) => <option key={l.v} value={l.v}>{l.l}</option>)}
    </select>
  )
}

export function Tabs({ tabs, active, onChange }) {
  return (
    <div role="tablist" className="mb-4 flex flex-wrap gap-1 border-b border-slate-200 dark:border-navy-700">
      {tabs.map(([k, label]) => (
        <button key={k} role="tab" aria-selected={active === k} onClick={() => onChange(k)}
          className={`px-4 py-2 text-sm font-semibold transition ${active === k ? 'border-b-2 border-brand-600 text-brand-700 dark:text-brand-300' : 'text-slate-500 hover:text-navy-900 dark:text-slate-400 dark:hover:text-white'}`}>
          {label}
        </button>
      ))}
    </div>
  )
}
