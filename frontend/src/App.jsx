import { Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import Spinner from './components/Spinner'
import { useAuth } from './context/AuthContext'
import Dashboard from './pages/Dashboard'
import Landing from './pages/Landing'
import LinkAnalytics from './pages/LinkAnalytics'
import Links from './pages/Links'
import Login from './pages/Login'
import PasswordGate from './pages/PasswordGate'
import Scanner from './pages/Scanner'
import Settings from './pages/Settings'
import Signup from './pages/Signup'
import StatusPage from './pages/StatusPage'

function GuestOnly({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <Spinner full />
  return user ? <Navigate to="/dashboard" replace /> : children
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<GuestOnly><Login /></GuestOnly>} />
      <Route path="/signup" element={<GuestOnly><Signup /></GuestOnly>} />
      <Route path="/p/:code" element={<PasswordGate />} />
      <Route path="/expired" element={<StatusPage />} />
      <Route path="/not-found" element={<StatusPage kind="missing" />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/links" element={<Links />} />
        <Route path="/links/:id" element={<LinkAnalytics />} />
        <Route path="/scanner" element={<Scanner />} />
        <Route path="/settings" element={<Settings />} />
      </Route>

      <Route path="*" element={<StatusPage kind="missing" />} />
    </Routes>
  )
}
