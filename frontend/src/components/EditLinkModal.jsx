import { useState } from 'react'
import toast from 'react-hot-toast'
import api, { errorMessage } from '../api/client'
import Modal from './Modal'

function toLocalInput(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export default function EditLinkModal({ link, onClose, onSaved }) {
  const [form, setForm] = useState({
    url: link.original_url,
    title: link.title || '',
    tags: (link.tags || []).join(', '),
    expires_at: toLocalInput(link.expires_at),
    max_clicks: link.max_clicks || '',
    password: '',
    removePassword: false,
  })
  const [saving, setSaving] = useState(false)
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }))

  const save = async (e) => {
    e.preventDefault()
    setSaving(true)
    const body = {
      title: form.title,
      tags: form.tags,
      max_clicks: form.max_clicks || null,
      expires_at: form.expires_at ? new Date(form.expires_at).toISOString() : null,
    }
    if (form.url !== link.original_url) body.url = form.url
    if (form.removePassword) body.password = ''
    else if (form.password) body.password = form.password
    try {
      const { data } = await api.patch(`/links/${link.id}`, body)
      toast.success('Link updated')
      onSaved(data.link)
      onClose()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal title={`Edit /${link.short_code}`} onClose={onClose} width={520}>
      <form onSubmit={save} className="stack">
        <label className="field">
          <span>Destination URL</span>
          <input value={form.url} onChange={set('url')} required />
          <small className="muted">Changing this keeps the same short link - handy after it's already been shared.</small>
        </label>
        <label className="field">
          <span>Title</span>
          <input value={form.title} onChange={set('title')} />
        </label>
        <div className="grid-2">
          <label className="field">
            <span>Expires at</span>
            <input type="datetime-local" value={form.expires_at} onChange={set('expires_at')} />
          </label>
          <label className="field">
            <span>Click limit</span>
            <input type="number" min="1" value={form.max_clicks} onChange={set('max_clicks')} placeholder="Unlimited" />
          </label>
        </div>
        <label className="field">
          <span>Tags</span>
          <input value={form.tags} onChange={set('tags')} placeholder="comma, separated" />
        </label>
        <label className="field">
          <span>{link.has_password ? 'New password' : 'Password'}</span>
          <input
            type="password"
            value={form.password}
            onChange={set('password')}
            disabled={form.removePassword}
            placeholder={link.has_password ? 'Leave empty to keep current' : 'Optional'}
            autoComplete="new-password"
          />
        </label>
        {link.has_password && (
          <label className="check">
            <input type="checkbox" checked={form.removePassword} onChange={set('removePassword')} /> Remove password protection
          </label>
        )}
        <div className="modal-actions">
          <button type="button" className="btn ghost" onClick={onClose}>
            Cancel
          </button>
          <button className="btn primary" disabled={saving}>
            {saving ? 'Saving…' : 'Save changes'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
