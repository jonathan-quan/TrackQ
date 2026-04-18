import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { apiErrorMessage } from '../api/errors'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await register(username, email, password)
      navigate('/', { replace: true })
    } catch (err) {
      setError(apiErrorMessage(err, 'Registration failed'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-md mx-auto mt-20 px-8">
      <span className="label-mono">Account</span>
      <h1
        className="fw-bold tracking-hero text-5xl mt-3 mb-10 leading-[1.0]"
        style={{ fontVariationSettings: '"wght" 700' }}
      >
        Create an account
      </h1>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="label-mono block mb-2">Username</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            className="input"
            placeholder="yourname"
          />
        </div>
        <div>
          <label className="label-mono block mb-2">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="input"
            placeholder="you@example.com"
          />
        </div>
        <div>
          <label className="label-mono block mb-2">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
            className="input"
            placeholder="6+ characters"
          />
        </div>

        {error && (
          <p className="text-sm fw-mid" style={{ color: 'var(--color-miss)' }}>
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="btn btn-black w-full mt-2"
          style={{ paddingTop: '0.85rem', paddingBottom: '0.9rem' }}
        >
          {submitting ? 'Creating…' : 'Register'}
        </button>
      </form>

      <p className="mt-8 text-sm fw-light-2" style={{ color: 'var(--color-muted)' }}>
        Already have an account?{' '}
        <Link to="/login" className="text-black underline underline-offset-4 fw-mid">
          Log in
        </Link>
      </p>
    </div>
  )
}
