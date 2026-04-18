import StatusBadge from './StatusBadge'

const STAT_LABELS = {
  points: 'PTS',
  rebounds: 'REB',
  assists: 'AST',
  steals: 'STL',
  blocks: 'BLK',
  threes_made: '3PM',
}

const BAR_COLORS = {
  hit: 'var(--color-hit)',
  miss: 'var(--color-miss)',
  live: 'var(--color-live)',
  'live-winning': 'var(--color-hit)',
  pending: 'rgba(0, 0, 0, 0.15)',
}

export default function LegCard({ leg, onDelete }) {
  const label = STAT_LABELS[leg.stat_type] || leg.stat_type
  const actual = leg.actual_value != null ? leg.actual_value : '—'

  // Surface a "live" / "live-winning" display state while the underlying DB
  // status is still "pending" but a live actual_value has come in.
  let displayStatus = leg.status
  if (leg.status === 'pending' && leg.actual_value != null) {
    const winning =
      leg.over_under === 'over'
        ? leg.actual_value > leg.line
        : leg.actual_value < leg.line
    displayStatus = winning ? 'live-winning' : 'live'
  }

  const hasProgress = leg.actual_value != null && leg.line > 0
  const pct = hasProgress
    ? Math.min(100, Math.max(0, (leg.actual_value / leg.line) * 100))
    : 0
  const barColor = BAR_COLORS[displayStatus] || BAR_COLORS.pending

  return (
    <div className="surface p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-baseline gap-3 flex-wrap">
            <h3
              className="fw-semi text-xl tracking-display"
              style={{ fontVariationSettings: '"wght" 540' }}
            >
              {leg.player_name}
            </h3>
            {leg.matchup && (
              <span className="label-mono" style={{ color: 'var(--color-muted)' }}>
                {leg.matchup}
              </span>
            )}
          </div>
          <p
            className="label-mono mt-2"
            style={{ color: 'var(--color-muted)' }}
          >
            {leg.over_under} · {leg.line} {label}
          </p>
        </div>

        <div className="flex items-start gap-3 shrink-0">
          <div className="text-right">
            <div className="label-mono" style={{ color: 'var(--color-muted)' }}>
              Actual
            </div>
            <div
              className="fw-bold text-2xl tracking-display leading-none mt-1"
              style={{ fontVariationSettings: '"wght" 700' }}
            >
              {actual}
            </div>
            <div className="mt-2">
              <StatusBadge status={displayStatus} />
            </div>
          </div>
          {onDelete && (
            <button
              onClick={onDelete}
              className="btn-icon"
              aria-label="Remove leg"
              title="Remove leg"
            >
              ×
            </button>
          )}
        </div>
      </div>

      {hasProgress && (
        <div className="mt-5">
          <div
            className="w-full h-1 bg-black/[0.08] rounded-full overflow-hidden"
            role="progressbar"
            aria-valuenow={leg.actual_value}
            aria-valuemin={0}
            aria-valuemax={leg.line}
            aria-label={`${leg.actual_value} of ${leg.line} ${label}`}
          >
            <div
              className="h-full rounded-full transition-all duration-500 ease-out"
              style={{ width: `${pct}%`, background: barColor }}
            />
          </div>
          <p
            className="label-mono mt-2 text-right"
            style={{ color: 'var(--color-muted)' }}
          >
            {leg.actual_value} / {leg.line} {label}
          </p>
        </div>
      )}
    </div>
  )
}
