import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Navbar from './Navbar'
import Spinner from './Spinner'

export default function ProtectedRoute() {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <Spinner full />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />

  return (
    <>
      <Navbar />
      <main className="page">
        <Outlet />
      </main>
    </>
  )
}
