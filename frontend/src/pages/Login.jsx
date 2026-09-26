import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Mail, Lock } from 'lucide-react'
import toast from 'react-hot-toast'
import { errorMessage } from '../api/client'
import AuthLayout from '../components/AuthLayout'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ email: '', password: '' })
  const [show, setShow] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const user = await login(form.email, form.password)
      toast.success(`Welcome back, ${user.name.split(' ')[0]}!`)
      navigate(location.state?.from || '/dashboard', { replace: true })
    } catch (err) {
      setError(errorMessage(err, 'Could not log in'))
    } finally {
      setBusy(false)
    }
  }

  const fillDemo = () => setForm({ email: 'demo@linksense.dev', password: 'Demo@1234' })

  return (
    <AuthLayout title="Welcome back" subtitle="Log in to manage your links and analytics.">
      <form className="stack" onSubmit={submit}>
        {error && <div className="alert bad">{error}</div>}
        <label className="field">
          <span>Email</span>
          <div className="input-icon">
            <Mail size={16} />
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="you@example.com"
              autoComplete="email"
              required
            />
          </div>
        </label>
        <label className="field">
          <span>Password</span>
          <div className="input-icon">
            <Lock size={16} />
            <input
              type={show ? 'text' : 'password'}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              placeholder="Your password"
              autoComplete="current-password"
              required
            />
            <button type="button" className="icon-btn inset" onClick={() => setShow((s) => !s)} aria-label="Show password">
              {show ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </label>
        <button className="btn primary block" disabled={busy}>
          {busy ? 'Logging in…' : 'Log in'}
        </button>
        <button type="button" className="btn ghost block" onClick={fillDemo}>
          Use demo account
        </button>
      </form>
      <p className="auth-switch">
        New here? <Link to="/signup">Create an account</Link>
      </p>
    </AuthLayout>
  )
}
