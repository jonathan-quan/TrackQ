import { useEffect, useState } from 'react'
import * as parlaysApi from '../api/parlays'
import ParlayCard from '../components/ParlayCard'
import NewParlayModal from '../components/NewParlayModal'
import { apiErrorMessage } from '../api/errors'

export default function Dashboard() {
  const [parlays, setParlays] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [newOpen, setNewOpen] = useState(false)

  useEffect(() => {
    let cancelled = false
    parlaysApi
      .listParlays()
      .then((res) => {
        if (!cancelled) setParlays(res.data)
      })
      .catch((err) => {
        if (!cancelled) {
          setError(apiErrorMessage(err, 'Failed to load parlays'))
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  function handleCreated(parlay) {
    setParlays((prev) => [parlay, ...prev])
  }

  return (
    <div className="max-w-5xl mx-auto mt-16 px-8">
      <div className="flex items-end justify-between mb-12 gap-6 flex-wrap">
        <div>
          <span className="label-mono">Dashboard</span>
          <h1
            className="fw-bold tracking-hero text-6xl mt-3 leading-[1.0]"
            style={{ fontVariationSettings: '"wght" 700' }}
          >
            Your parlays
          </h1>
        </div>
        <button onClick={() => setNewOpen(true)} className="btn btn-black">
          + New parlay
        </button>
      </div>

      {loading && (
        <p className="label-mono" style={{ color: 'var(--color-muted)' }}>
          Loading…
        </p>
      )}
      {error && (
        <p className="text-sm fw-mid" style={{ color: 'var(--color-miss)' }}>
          {error}
        </p>
      )}

      {!loading && !error && parlays.length === 0 && (
        <div
          className="surface px-8 py-16 text-center"
          style={{ borderStyle: 'dashed' }}
        >
          <p className="fw-light-2 text-lg" style={{ color: 'var(--color-muted)' }}>
            No parlays yet.
          </p>
          <button
            onClick={() => setNewOpen(true)}
            className="btn btn-white mt-6"
          >
            Create your first parlay
          </button>
        </div>
      )}

      {!loading && parlays.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {parlays.map((p) => (
            <ParlayCard key={p.id} parlay={p} />
          ))}
        </div>
      )}

      <NewParlayModal
        open={newOpen}
        onClose={() => setNewOpen(false)}
        onCreated={handleCreated}
      />
    </div>
  )
}
