import { BrowserRouter, Routes, Route, Navigate, Link, useNavigate } from 'react-router-dom'

import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import ParlayDetail from './pages/ParlayDetail'
import ProtectedRoute from './components/ProtectedRoute'
import { AuthProvider, useAuth } from './context/AuthContext'

function Nav() {
  const { token, user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <nav className="border-b border-black/10 bg-white">
      <div className="max-w-5xl mx-auto px-8 py-5 flex items-center justify-between">
        <Link
          to="/"
          className="fw-bold tracking-display text-xl text-black"
          style={{ fontVariationSettings: '"wght" 700' }}
        >
          TrackQ
        </Link>
        <div className="flex gap-2 items-center">
          {token ? (
            <>
              {user && (
                <span className="label-mono mr-3">{user.username}</span>
              )}
              <button onClick={handleLogout} className="btn btn-ghost">
                Log out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn-ghost">Login</Link>
              <Link to="/register" className="btn btn-black">Register</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="min-h-full bg-white">
          <Nav />
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/parlays/:id"
              element={
                <ProtectedRoute>
                  <ParlayDetail />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </AuthProvider>
    </BrowserRouter>
  )
}
