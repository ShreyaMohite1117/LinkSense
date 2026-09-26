import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Lock, Mail, User } from 'lucide-react'
import toast from 'react-hot-toast'
import { errorMessage } from '../api/client'
import AuthLayout from '../components/AuthLayout'
import { useAuth } from '../context/AuthContext'

function strength(pw) {
  let s = 0
  if (pw.length >= 8) s++
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) s++
  if (/\d/.test(pw)) s++
  if (/[^A-Za-z0-9]/.test(pw)) s++
  return s
}

const LABELS = ['Too weak', 'Weak', 'Okay', 'Good', 'Strong']

export default function Signup() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' })
  const [show, setShow] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })
  const score = strength(form.password)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirm) return setError("Passwords don't match")
    setBusy(true)
    try {
      await signup(form.name, form.email, form.password)
      toast.success('Account created 🎉')
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(errorMessage(err, 'Could not create account'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthLayout title="Create your account" subtitle="Free forever for personal use. Takes 20 seconds.">
      <form className="stack" onSubmit={submit}>
        {error && <div className="alert bad">{error}</div>}
        <label className="field">
          <span>Full name</span>
          <div className="input-icon">
            <User size={16} />
            <input value={form.name} onChange={set('name')} placeholder="Priya Sharma" autoComplete="name" required />
          </div>
        </label>
        <label className="field">
          <span>Email</span>
          <div className="input-icon">
            <Mail size={16} />
            <input type="email" value={form.email} onChange={set('email')} placeholder="you@example.com" autoComplete="email" required />
          </div>
        </label>
        <label className="field">
          <span>Password</span>
          <div className="input-icon">
            <Lock size={16} />
            <input
              type={show ? 'text' : 'password'}
              value={form.password}
              onChange={set('password')}
              placeholder="At least 8 characters, with a number"
              autoComplete="new-password"
              required
            />
            <button type="button" className="icon-btn inset" onClick={() => setShow((s) => !s)} aria-label="Show password">
              {show ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          {form.password && (
            <div className="strength">
              <div className="strength-bar">
                {[0, 1, 2, 3].map((i) => (
                  <span key={i} className={i < score ? `on s${score}` : ''} />
                ))}
              </div>
              <small>{LABELS[score]}</small>
            </div>
          )}
        </label>
        <label className="field">
          <span>Confirm password</span>
          <div className="input-icon">
            <Lock size={16} />
            <input type={show ? 'text' : 'password'} value={form.confirm} onChange={set('confirm')} autoComplete="new-password" required />
          </div>
        </label>
        <button className="btn primary block" disabled={busy}>
          {busy ? 'Creating account…' : 'Sign up'}
        </button>
      </form>
      <p className="auth-switch">
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </AuthLayout>
  )
}
