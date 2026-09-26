import { useState } from 'react'
import { CheckCircle2, Upload, XCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import api, { errorMessage } from '../api/client'
import Modal from './Modal'

export default function BulkModal({ onClose, onDone }) {
  const [text, setText] = useState('')
  const [tags, setTags] = useState('')
  const [busy, setBusy] = useState(false)
  const [results, setResults] = useState(null)

  const urls = text
    .split(/[\n,]+/)
    .map((u) => u.trim())
    .filter(Boolean)

  const loadFile = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      // accept a plain list or a CSV where the url is the first column
      const lines = String(reader.result)
        .split(/\r?\n/)
        .map((l) => l.split(',')[0].replace(/"/g, '').trim())
        .filter((l) => l && l.toLowerCase() !== 'url')
      setText(lines.join('\n'))
    }
    reader.readAsText(file)
  }

  const submit = async () => {
    if (!urls.length) return
    setBusy(true)
    try {
      const { data } = await api.post('/links/bulk', { urls, tags })
      setResults(data.results)
      toast.success(`${data.created} links created${data.failed ? `, ${data.failed} skipped` : ''}`)
      onDone()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title="Bulk shorten" onClose={onClose} width={600}>
      {!results ? (
        <div className="stack">
          <p className="muted small">One URL per line (max 50). You can also upload a .csv or .txt file.</p>
          <textarea rows={8} value={text} onChange={(e) => setText(e.target.value)} placeholder={'https://example.com/page-one\nhttps://example.com/page-two'} />
          <div className="grid-2">
            <label className="field">
              <span>Tags for all</span>
              <input value={tags} onChange={(e) => setTags(e.target.value)} placeholder="campaign-q3" />
            </label>
            <label className="btn soft file-btn">
              <Upload size={16} /> Upload file
              <input type="file" accept=".csv,.txt" onChange={loadFile} hidden />
            </label>
          </div>
          <div className="modal-actions">
            <span className="muted small">{urls.length} URL(s)</span>
            <button className="btn primary" onClick={submit} disabled={busy || !urls.length || urls.length > 50}>
              {busy ? 'Shortening…' : 'Shorten all'}
            </button>
          </div>
        </div>
      ) : (
        <div className="bulk-results">
          {results.map((r, i) => (
            <div key={i} className="bulk-row">
              {r.ok ? <CheckCircle2 size={16} className="ok-text" /> : <XCircle size={16} className="bad-text" />}
              <span className="truncate">{r.url}</span>
              <span className={r.ok ? 'mono' : 'bad-text small'}>{r.ok ? r.link.short_url.replace(/^https?:\/\//, '') : r.error}</span>
            </div>
          ))}
          <div className="modal-actions">
            <button className="btn primary" onClick={onClose}>
              Done
            </button>
          </div>
        </div>
      )}
    </Modal>
  )
}
