import { useEffect, useState } from 'react'
import { CalendarClock, KeyRound, Link2, MousePointerClick, Sparkles, SlidersHorizontal, Tag, Wand2 } from 'lucide-react'
import toast from 'react-hot-toast'
import api, { errorMessage } from '../api/client'
import CopyButton from './CopyButton'
import RiskBadge from './RiskBadge'

const EMPTY = { url: '', alias: '', title: '', password: '', expires_in_days: '', max_clicks: '', tags: '' }

export default function CreateLinkForm({ onCreated }) {
  const [form, setForm] = useState(EMPTY)
  const [showMore, setShowMore] = useState(false)
  const [saving, setSaving] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const [aliasState, setAliasState] = useState(null)
  const [result, setResult] = useState(null)
  const [blocked, setBlocked] = useState(null)

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  // debounce alias availability checks while the user types
  useEffect(() => {
    if (!form.alias) {
      setAliasState(null)
      return
    }
    const t = setTimeout(async () => {
      try {
        const { data } = await api.get('/links/check-alias', { params: { alias: form.alias } })
        setAliasState(data)
      } catch {
        setAliasState(null)
      }
    }, 350)
    return () => clearTimeout(t)
  }, [form.alias])

  const suggest = async () => {
    if (!form.url) return toast('Paste a URL first')
    try {
      const { data } = await api.get('/links/suggest-alias', { params: { url: form.url } })
      setSuggestions(data.suggestions)
      setShowMore(true)
      if (!data.suggestions.length) toast('No good alias ideas for this one')
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  const submit = async (e) => {
    e.preventDefault()
    if (!form.url.trim()) return
    setSaving(true)
    setBlocked(null)
    try {
      const body = Object.fromEntries(Object.entries(form).filter(([, v]) => v !== ''))
      const { data } = await api.post('/links', body)
      setResult(data.link)
      if (data.link.warning) toast(data.link.warning, { icon: '⚠️' })
      else toast.success('Short link created')
      setForm(EMPTY)
      setSuggestions([])
      onCreated?.(data.link)
    } catch (err) {
      if (err.response?.status === 422) setBlocked(err.response.data)
      else toast.error(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="card create-card">
      <form onSubmit={submit}>
        <div className="create-main">
          <div className="input-icon grow">
            <Link2 size={18} />
            <input
              value={form.url}
              onChange={set('url')}
              placeholder="Paste a long URL, e.g. https://medium.com/@you/some-long-article"
              aria-label="Long URL"
              required
            />
          </div>
          <button className="btn primary" disabled={saving}>
            {saving ? 'Checking…' : 'Shorten'}
          </button>
        </div>

        <div className="create-actions">
          <button type="button" className="chip-btn" onClick={() => setShowMore((s) => !s)}>
            <SlidersHorizontal size={14} /> {showMore ? 'Hide options' : 'More options'}
          </button>
          <button type="button" className="chip-btn" onClick={suggest}>
            <Wand2 size={14} /> Suggest alias
          </button>
          <span className="muted small">
            <Sparkles size={13} /> Every URL is scanned for phishing before it's shortened
          </span>
        </div>

        {showMore && (
          <div className="create-grid">
            <label className="field">
              <span>Custom alias</span>
              <div className="alias-input">
                <em>/</em>
                <input value={form.alias} onChange={set('alias')} placeholder="my-portfolio" />
              </div>
              {aliasState && (
                <small className={aliasState.available ? 'ok-text' : 'bad-text'}>
                  {aliasState.available ? 'Available' : aliasState.reason}
                </small>
              )}
              {suggestions.length > 0 && (
                <div className="suggestions">
                  {suggestions.map((s) => (
                    <button type="button" key={s} onClick={() => setForm((f) => ({ ...f, alias: s }))}>
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </label>
            <label className="field">
              <span>Title</span>
              <input value={form.title} onChange={set('title')} placeholder="Something you'll recognise" />
            </label>
            <label className="field">
              <span>
                <KeyRound size={13} /> Password
              </span>
              <input type="password" value={form.password} onChange={set('password')} placeholder="Optional" autoComplete="new-password" />
            </label>
            <label className="field">
              <span>
                <CalendarClock size={13} /> Expires after
              </span>
              <select value={form.expires_in_days} onChange={set('expires_in_days')}>
                <option value="">Never</option>
                <option value="0.0417">1 hour</option>
                <option value="1">1 day</option>
                <option value="7">7 days</option>
                <option value="30">30 days</option>
                <option value="90">90 days</option>
              </select>
            </label>
            <label className="field">
              <span>
                <MousePointerClick size={13} /> Click limit
              </span>
              <input type="number" min="1" value={form.max_clicks} onChange={set('max_clicks')} placeholder="Unlimited" />
            </label>
            <label className="field">
              <span>
                <Tag size={13} /> Tags
              </span>
              <input value={form.tags} onChange={set('tags')} placeholder="resume, project" />
            </label>
          </div>
        )}
      </form>

      {blocked && (
        <div className="alert bad">
          <strong>{blocked.error}</strong>
          <RiskBadge risk={blocked.risk} showScore />
          <ul>
            {blocked.risk?.reasons?.slice(0, 4).map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      {result && (
        <div className="result">
          <div>
            <p className="muted small">Your short link</p>
            <a href={result.short_url} target="_blank" rel="noreferrer" className="result-link">
              {result.short_url}
            </a>
          </div>
          <div className="result-right">
            <RiskBadge risk={result.risk} />
            <CopyButton text={result.short_url} label="Copy" className="btn soft" />
          </div>
        </div>
      )}
    </div>
  )
}
