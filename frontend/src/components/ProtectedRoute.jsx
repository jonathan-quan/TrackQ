import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children }) {
  const { token, loading } = useAuth()

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto mt-16 p-8 text-gray-500">Loading…</div>
    )
  }

  if (!token) {
    return <Navigate to="/login" replace />
  }

  return children
}
