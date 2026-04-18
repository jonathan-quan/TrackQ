import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import * as parlaysApi from '../api/parlays'
import * as legsApi from '../api/legs'
import LegCard from '../components/LegCard'
import StatusBadge from '../components/StatusBadge'
import AddLegModal from '../components/AddLegModal'
import { apiErrorMessage } from '../api/errors'

const REFRESH_INTERVAL_MS = 60_000

export default function ParlayDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [parlay, setParlay] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [addOpen, setAddOpen] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const loadParlay = useCallback(async () => {
    const res = await parlaysApi.getParlay(id)
    setParlay(res.data)
    setError('')
    return res.data
  }, [id])

  function handleLegAdded() {
    loadParlay().catch((err) => {
      setError(apiErrorMessage(err, 'Failed to reload parlay'))
    })
  }

  async function handleDeleteLeg(legId) {
    if (!window.confirm('Remove this leg?')) return
    try {
      await legsApi.deleteLeg(legId)
      await loadParlay()
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to remove leg'))
    }
  }

  async function handleDeleteParlay() {
    if (!window.confirm('Delete this parlay? This cannot be undone.')) return
    setDeleting(true)
    try {
      await parlaysApi.deleteParlay(id)
      navigate('/', { replace: true })
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to delete parlay'))
      setDeleting(false)
    }
  }

  const refresh = useCallback(async () => {
    setRefreshing(true)
    try {
      const res = await parlaysApi.refreshParlay(id)
      // The refresh response is already the latest parlay (with matchups
      // attached on the backend); a follow-up GET would just drop those.
      setParlay(res.data)
      setError('')
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to refresh'))
    } finally {
      setRefreshing(false)
    }
  }, [id])

  // On mount: show cached DB data immediately, then fire a background refresh
  // so we don't block the page on the (slow) nba.com fan-out.
  useEffect(() => {
    let cancelled = false
    setLoading(true)
    loadParlay()
      .catch((err) => {
        if (!cancelled) setError(apiErrorMessage(err, 'Failed to load parlay'))
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
          void refresh()
        }
      })
    const handle = setInterval(() => {
      void refresh()
    }, REFRESH_INTERVAL_MS)
    return () => {
      cancelled = true
      clearInterval(handle)
    }
  }, [loadParlay, refresh])

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto mt-16 px-8">
        <span className="label-mono" style={{ color: 'var(--color-muted)' }}>
          Loading…
        </span>
      </div>
    )
  }

  if (error && !parlay) {
    return (
      <div className="max-w-5xl mx-auto mt-16 px-8">
        <Link to="/" className="label-mono inline-block mb-6 underline underline-offset-4">
          ← Back to dashboard
        </Link>
        <p className="text-sm fw-mid" style={{ color: 'var(--color-miss)' }}>
          {error}
        </p>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto mt-12 px-8 pb-20">
      <Link
        to="/"
        className="label-mono inline-block mb-8 underline underline-offset-4"
        style={{ color: 'var(--color-muted)' }}
      >
        ← Back to dashboard
      </Link>

      <div className="flex items-start justify-between mb-12 gap-6 flex-wrap">
        <div className="min-w-0">
          <span className="label-mono" style={{ color: 'var(--color-muted)' }}>
            {parlay.game_date}
          </span>
          <div className="flex items-center gap-4 mt-3 flex-wrap">
            <h1
              className="fw-bold tracking-hero text-5xl leading-[1.0]"
              style={{ fontVariationSettings: '"wght" 700' }}
            >
              {parlay.name}
            </h1>
            <StatusBadge status={parlay.status} />
          </div>
        </div>
        <div className="flex gap-2 flex-wrap justify-end items-center">
          <button onClick={() => setAddOpen(true)} className="btn btn-glass">
            + Add leg
          </button>
          <button
            onClick={refresh}
            disabled={refreshing}
            className="btn btn-black"
          >
            {refreshing ? 'Refreshing…' : 'Refresh'}
          </button>
          <button
            onClick={handleDeleteParlay}
            disabled={deleting}
            className="btn btn-white"
          >
            {deleting ? 'Deleting…' : 'Delete'}
          </button>
        </div>
      </div>

      {error && (
        <p className="text-sm fw-mid mb-4" style={{ color: 'var(--color-miss)' }}>
          {error}
        </p>
      )}

      {parlay.legs.length === 0 ? (
        <div
          className="surface px-8 py-16 text-center"
          style={{ borderStyle: 'dashed' }}
        >
          <p className="fw-light-2 text-lg" style={{ color: 'var(--color-muted)' }}>
            No legs yet.
          </p>
          <button
            onClick={() => setAddOpen(true)}
            className="btn btn-white mt-6"
          >
            Add your first leg
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {parlay.legs.map((leg) => (
            <LegCard key={leg.id} leg={leg} onDelete={() => handleDeleteLeg(leg.id)} />
          ))}
        </div>
      )}

      <AddLegModal
        open={addOpen}
        parlayId={id}
        onClose={() => setAddOpen(false)}
        onAdded={handleLegAdded}
      />
    </div>
  )
}
