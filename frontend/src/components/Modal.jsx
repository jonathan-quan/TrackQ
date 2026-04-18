export default function Modal({ open, onClose, title, children }) {
  if (!open) return null
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="surface w-full max-w-md p-7"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-6 gap-4">
          <div className="min-w-0">
            <span className="label-mono" style={{ color: 'var(--color-muted)' }}>
              Action
            </span>
            <h2
              className="fw-bold tracking-display text-2xl mt-2 leading-[1.1]"
              style={{ fontVariationSettings: '"wght" 700' }}
            >
              {title}
            </h2>
          </div>
          <button onClick={onClose} className="btn-icon" aria-label="Close">
            ×
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}
