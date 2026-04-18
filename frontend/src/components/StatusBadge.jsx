const STYLES = {
  hit: 'badge badge-hit',
  miss: 'badge badge-miss',
  pending: 'badge badge-pending',
  live: 'badge badge-live',
  'live-winning': 'badge badge-hit',
}

const LABELS = {
  'live-winning': 'live',
}

export default function StatusBadge({ status }) {
  const cls = STYLES[status] || STYLES.pending
  const label = LABELS[status] || status
  return <span className={cls}>{label}</span>
}
