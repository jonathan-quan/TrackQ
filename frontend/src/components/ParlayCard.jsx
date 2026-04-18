import { Link } from 'react-router-dom'
import StatusBadge from './StatusBadge'

export default function ParlayCard({ parlay }) {
  return (
    <Link
      to={`/parlays/${parlay.id}`}
      className="surface block p-6 hover:bg-black/[0.02] transition group"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <span className="label-mono" style={{ color: 'var(--color-muted)' }}>
            {parlay.game_date}
          </span>
          <h2
            className="fw-semi text-2xl tracking-display mt-2 truncate"
            style={{ fontVariationSettings: '"wght" 540' }}
          >
            {parlay.name}
          </h2>
        </div>
        <StatusBadge status={parlay.status} />
      </div>

      <div className="mt-6 flex items-center justify-between">
        <span className="label-mono" style={{ color: 'var(--color-muted)' }}>
          View parlay
        </span>
        <span
          className="fw-mid text-lg group-hover:translate-x-0.5 transition-transform"
          aria-hidden="true"
        >
          →
        </span>
      </div>
    </Link>
  )
}
