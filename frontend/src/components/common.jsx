import { STATE_META } from '../utils.js';

export function StatusBadge({ state }) {
  const meta = STATE_META[state] || STATE_META.Inactive;
  return (
    <span className={`status-badge ${meta.cls}`}>
      <i className={`bi ${meta.icon}`} aria-hidden="true" /> {meta.label}
    </span>
  );
}

export function StatCard({ icon, label, value, tone = 'primary', hint }) {
  return (
    <div className="card stat-card h-100">
      <div className="card-body d-flex align-items-center gap-3">
        <div className={`stat-icon tone-${tone}`}><i className={`bi ${icon}`} aria-hidden="true" /></div>
        <div>
          <div className="stat-label">{label}</div>
          <div className="stat-value">{value}</div>
          {hint && <div className="stat-hint">{hint}</div>}
        </div>
      </div>
    </div>
  );
}

export function Alert({ kind = 'danger', children, onClose }) {
  if (!children) return null;
  return (
    <div className={`alert alert-${kind} alert-dismissible fade show d-flex align-items-center gap-2`} role="alert">
      <i className={`bi ${kind === 'success' ? 'bi-check-circle' : 'bi-exclamation-triangle'}`} aria-hidden="true" />
      <div className="flex-grow-1">{children}</div>
      {onClose && <button type="button" className="btn-close" aria-label="Close" onClick={onClose} />}
    </div>
  );
}

export function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="page-header d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
      <div>
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle mb-0">{subtitle}</p>}
      </div>
      {actions && <div className="d-flex gap-2 flex-wrap">{actions}</div>}
    </div>
  );
}

export function Spinner() {
  return (
    <div className="text-center py-5">
      <div className="spinner-border text-primary" role="status"><span className="visually-hidden">Loading</span></div>
    </div>
  );
}

export function EmptyState({ icon = 'bi-inbox', text }) {
  return (
    <div className="empty-state text-center py-5">
      <i className={`bi ${icon}`} aria-hidden="true" />
      <p className="mb-0">{text}</p>
    </div>
  );
}
