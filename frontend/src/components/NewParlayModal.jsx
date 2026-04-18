import { useState } from 'react'
import Modal from './Modal'
import * as parlaysApi from '../api/parlays'
import { apiErrorMessage } from '../api/errors'

function today() {
  return new Date().toISOString().slice(0, 10)
}

export default function NewParlayModal({ open, onClose, onCreated }) {
  const [name, setName] = useState('')
  const [gameDate, setGameDate] = useState(today())
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const res = await parlaysApi.createParlay({ name, game_date: gameDate })
      onCreated(res.data)
      setName('')
      setGameDate(today())
      onClose()
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to create parlay'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="New parlay">
      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="label-mono block mb-2">Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            maxLength={100}
            className="input"
            placeholder="e.g. nba playoff"
          />
        </div>
        <div>
          <label className="label-mono block mb-2">Game date</label>
          <input
            type="date"
            value={gameDate}
            onChange={(e) => setGameDate(e.target.value)}
            required
            className="input"
          />
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
            {submitting ? 'Creating…' : 'Create parlay'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
