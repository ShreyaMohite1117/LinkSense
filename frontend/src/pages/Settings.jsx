import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertTriangle, KeyRound, Terminal, UserRound } from 'lucide-react'
import toast from 'react-hot-toast'
import api, { errorMessage } from '../api/client'
import CopyButton from '../components/CopyButton'
import { useAuth } from '../context/AuthContext'
import { shortDate } from '../utils/format'

const API_BASE = `${import.meta.env.VITE_API_URL || window.location.origin}/api`

export default function Settings() {
  const { user, setUser, logout } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState(user.name)
  const [pw, setPw] = useState({ current_password: '', new_password: '' })
  const [apiKey, setApiKey] = useState(null)
  const [busy, setBusy] = useState('')

  const saveProfile = async (e) => {
    e.preventDefault()
    setBusy('profile')
    try {
      const { data } = await api.patch('/auth/me', { name })
      setUser(data.user)
      toast.success('Profile saved')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy('')
    }
  }

  const changePassword = async (e) => {
    e.preventDefault()
    setBusy('password')
    try {
      await api.post('/auth/change-password', pw)
      setPw({ current_password: '', new_password: '' })
      toast.success('Password changed')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy('')
    }
  }

  const generateKey = async () => {
    if (user.has_api_key && !window.confirm('This replaces your current key. Apps using it will stop working.')) return
    const { data } = await api.post('/auth/api-key')
    setApiKey(data.api_key)
    setUser({ ...user, has_api_key: true })
  }

  const revokeKey = async () => {
    await api.delete('/auth/api-key')
    setApiKey(null)
    setUser({ ...user, has_api_key: false })
    toast.success('API key revoked')
  }

  const deleteAccount = async () => {
    if (window.prompt('Type DELETE to permanently remove your account and all links') !== 'DELETE') return
    await api.delete('/auth/me')
    logout()
    navigate('/')
    toast.success('Account deleted')
  }

  const curl = `curl -X POST ${API_BASE}/links \\
  -H "X-API-Key: ${apiKey || 'lsk_your_key'}" \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://example.com/very/long/url", "alias": "my-link"}'`

  return (
    <div className="container narrow">
      <div className="page-head">
        <div>
          <h1>Settings</h1>
          <p className="muted">Member since {shortDate(user.created_at)}</p>
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <h3>
            <UserRound size={17} /> Profile
          </h3>
        </div>
        <form className="stack" onSubmit={saveProfile}>
          <div className="grid-2">
            <label className="field">
              <span>Name</span>
              <input value={name} onChange={(e) => setName(e.target.value)} />
            </label>
            <label className="field">
              <span>Email</span>
              <input value={user.email} disabled />
            </label>
          </div>
          <div>
            <button className="btn primary" disabled={busy === 'profile'}>
              Save
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <div className="card-head">
          <h3>
            <KeyRound size={17} /> Change password
          </h3>
        </div>
        <form className="stack" onSubmit={changePassword}>
          <div className="grid-2">
            <label className="field">
              <span>Current password</span>
              <input type="password" value={pw.current_password} onChange={(e) => setPw({ ...pw, current_password: e.target.value })} required autoComplete="current-password" />
            </label>
            <label className="field">
              <span>New password</span>
              <input type="password" value={pw.new_password} onChange={(e) => setPw({ ...pw, new_password: e.target.value })} required autoComplete="new-password" />
            </label>
          </div>
          <div>
            <button className="btn primary" disabled={busy === 'password'}>
              Update password
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <div className="card-head">
          <h3>
            <Terminal size={17} /> Developer API
          </h3>
        </div>
        <p className="muted small">Create links from scripts or other apps with an API key. The key is shown once - store it somewhere safe.</p>
        {apiKey && (
          <div className="key-box">
            <code>{apiKey}</code>
            <CopyButton text={apiKey} />
          </div>
        )}
        <div className="row-gap">
          <button className="btn soft" onClick={generateKey}>
            {user.has_api_key ? 'Regenerate key' : 'Generate API key'}
          </button>
          {user.has_api_key && (
            <button className="btn ghost danger-text" onClick={revokeKey}>
              Revoke
            </button>
          )}
        </div>
        <pre className="code">{curl}</pre>
      </div>

      <div className="card danger-card">
        <div className="card-head">
          <h3>
            <AlertTriangle size={17} /> Danger zone
          </h3>
        </div>
        <p className="muted small">Deletes your account, every link and all click data. This can't be undone.</p>
        <button className="btn danger" onClick={deleteAccount}>
          Delete account
        </button>
      </div>
    </div>
  )
}
