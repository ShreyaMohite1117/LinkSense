import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Lock } from 'lucide-react'
import api, { errorMessage } from '../api/client'
import Logo from '../components/Logo'
import Spinner from '../components/Spinner'
import ThemeToggle from '../components/ThemeToggle'

export default function PasswordGate() {
  const { code } = useParams()
  const [info, setInfo] = useState(null)
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api
      .get(`/r/${code}`)
      .then((r) => setInfo(r.data))
      .catch(() => setInfo({ status: 'missing' }))
  }, [code])

  const unlock = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const { data } = await api.post(`/r/${code}/unlock`, { password })
      window.location.replace(data.url)
    } catch (err) {
      setError(errorMessage(err, 'Wrong password'))
      setBusy(false)
    }
  }

  return (
    <div className="center-page">
      <ThemeToggle floating />
      <div className="card gate">
        <Logo />
        {!info ? (
          <Spinner />
        ) : info.status === 'missing' ? (
          <>
            <h2>Link not found</h2>
            <p className="muted">This short link doesn't exist.</p>
          </>
        ) : info.status !== 'active' ? (
          <>
            <h2>Link unavailable</h2>
            <p className="muted">This link has expired or been switched off by its owner.</p>
          </>
        ) : (
          <form onSubmit={unlock} className="stack">
            <div className="gate-icon">
              <Lock size={22} />
            </div>
            <h2>This link is protected</h2>
            <p className="muted">{info.title ? `"${info.title}" - ` : ''}enter the password to continue.</p>
            {error && <div className="alert bad">{error}</div>}
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" autoFocus required />
            <button className="btn primary block" disabled={busy}>
              {busy ? 'Checking…' : 'Unlock link'}
            </button>
          </form>
        )}
        <p className="muted small">
          Powered by <Link to="/">LinkSense</Link>
        </p>
      </div>
    </div>
  )
}
