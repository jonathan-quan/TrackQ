import { useEffect, useState } from 'react'
import Modal from './Modal'
import * as searchApi from '../api/search'
import * as legsApi from '../api/legs'
import { apiErrorMessage } from '../api/errors'

const STAT_OPTIONS = [
  { value: 'points', label: 'Points' },
  { value: 'rebounds', label: 'Rebounds' },
  { value: 'assists', label: 'Assists' },
  { value: 'steals', label: 'Steals' },
  { value: 'blocks', label: 'Blocks' },
  { value: 'threes_made', label: 'Threes Made' },
]

export default function AddLegModal({ open, parlayId, onClose, onAdded }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [selected, setSelected] = useState(null)
  const [statType, setStatType] = useState('points')
  const [line, setLine] = useState('')
  const [overUnder, setOverUnder] = useState('over')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!open) {
      setQuery('')
      setResults([])
      setSelected(null)
      setStatType('points')
      setLine('')
      setOverUnder('over')
      setError('')
    }
  }, [open])

  useEffect(() => {
    if (!query.trim() || selected) {
      setResults([])
      return
    }
    let cancelled = false
    const handle = setTimeout(async () => {
      setSearching(true)
      try {
        const res = await searchApi.searchPlayers(query)
        if (!cancelled) setResults(res.data)
      } catch {
        if (!cancelled) setResults([])
      } finally {
        if (!cancelled) setSearching(false)
      }
    }, 300)
    return () => {
      cancelled = true
      clearTimeout(handle)
    }
  }, [query, selected])

  async function handleSubmit(e) {
    e.preventDefault()
    if (!selected) {
      setError('Pick a player')
      return
    }
    setError('')
    setSubmitting(true)
    try {
      const res = await legsApi.addLeg(parlayId, {
        player_name: selected.full_name,
        player_id: selected.player_id,
        stat_type: statType,
        line: parseFloat(line),
        over_under: overUnder,
      })
      onAdded(res.data)
      onClose()
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to add leg'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Add leg">
      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="label-mono block mb-2">Player</label>
          {selected ? (
            <div className="flex items-center justify-between px-4 py-3 surface">
              <span
                className="fw-mid-2"
                style={{ fontVariationSettings: '"wght" 480' }}
              >
                {selected.full_name}
              </span>
              <button
                type="button"
                onClick={() => setSelected(null)}
                className="btn btn-ghost"
                style={{ padding: '0.3rem 0.7rem', fontSize: '0.8rem' }}
              >
                Change
              </button>
            </div>
          ) : (
            <>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search NBA player…"
                className="input"
                autoFocus
              />
              {searching && (
                <p
                  className="label-mono mt-2"
                  style={{ color: 'var(--color-muted)' }}
                >
                  Searching…
                </p>
              )}
              {results.length > 0 && (
                <ul
                  className="surface scroll-area mt-2 max-h-44 overflow-y-auto p-1"
                >
                  {results.map((p) => (
                    <li key={p.player_id}>
                      <button
                        type="button"
                        onClick={() => setSelected(p)}
                        className="w-full text-left px-3 py-2 rounded fw-mid hover:bg-black/[0.04] transition"
                        style={{ fontVariationSettings: '"wght" 450' }}
                      >
                        {p.full_name}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </div>

        <div>
          <label className="label-mono block mb-2">Stat</label>
          <select
            value={statType}
            onChange={(e) => setStatType(e.target.value)}
            className="input"
          >
            {STAT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>

        <div className="flex gap-3">
          <div className="flex-1">
            <label className="label-mono block mb-2">Line</label>
            <input
              type="number"
              step="0.5"
              min="0"
              value={line}
              onChange={(e) => setLine(e.target.value)}
              required
              className="input"
              placeholder="20.5"
            />
          </div>
          <div className="flex-1">
            <label className="label-mono block mb-2">Over / Under</label>
            <select
              value={overUnder}
              onChange={(e) => setOverUnder(e.target.value)}
              className="input"
            >
              <option value="over">Over</option>
              <option value="under">Under</option>
            </select>
          </div>
        </div>

        {error && (
          <p className="text-sm fw-mid" style={{ color: 'var(--color-miss)' }}>
            {error}
          </p>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="btn btn-ghost">
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="btn btn-black"
          >
            {submitting ? 'Adding…' : 'Add leg'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
