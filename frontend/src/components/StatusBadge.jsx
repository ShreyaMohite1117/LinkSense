const LABELS = {
  active: ['Active', 'ok'],
  expired: ['Expired', 'muted'],
  disabled: ['Paused', 'muted'],
  limit_reached: ['Limit reached', 'warn'],
}

export default function StatusBadge({ status }) {
  const [label, cls] = LABELS[status] || [status, 'muted']
  return <span className={`badge dot ${cls}`}>{label}</span>
}
