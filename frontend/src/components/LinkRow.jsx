import { useState } from 'react'
import { Link } from 'react-router-dom'
import { BarChart2, CalendarClock, Lock, MoreHorizontal, Pause, Pencil, Play, QrCode, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import api, { errorMessage } from '../api/client'
import { compact, faviconFor, hostOf, shortDate, timeAgo } from '../utils/format'
import CopyButton from './CopyButton'
import EditLinkModal from './EditLinkModal'
import QrModal from './QrModal'
import RiskBadge from './RiskBadge'
import StatusBadge from './StatusBadge'

export default function LinkRow({ link, onChange, onDelete }) {
  const [qr, setQr] = useState(false)
  const [edit, setEdit] = useState(false)
  const [menu, setMenu] = useState(false)
  const [iconFailed, setIconFailed] = useState(false)

  const toggleActive = async () => {
    setMenu(false)
    try {
      const { data } = await api.patch(`/links/${link.id}`, { is_active: !link.is_active })
      onChange(data.link)
      toast.success(data.link.is_active ? 'Link resumed' : 'Link paused')
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  const remove = async () => {
    setMenu(false)
    if (!window.confirm(`Delete /${link.short_code}? Its analytics will be deleted too.`)) return
    try {
      await api.delete(`/links/${link.id}`)
      onDelete(link.id)
      toast.success('Link deleted')
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }

  return (
    <div className="link-row">
      {iconFailed ? (
        <span className="favicon letter">{hostOf(link.original_url).charAt(0).toUpperCase()}</span>
      ) : (
        <img className="favicon" src={faviconFor(link.original_url)} alt="" loading="lazy" onError={() => setIconFailed(true)} />
      )}
      <div className="link-main">
        <div className="link-title">
          <span>{link.title || hostOf(link.original_url)}</span>
          {link.has_password && <Lock size={13} className="muted" title="Password protected" />}
          {link.expires_at && <CalendarClock size={13} className="muted" title={`Expires ${shortDate(link.expires_at)}`} />}
        </div>
        <div className="link-short">
          <a href={link.short_url} target="_blank" rel="noreferrer">
            {link.short_url.replace(/^https?:\/\//, '')}
          </a>
          <CopyButton text={link.short_url} />
        </div>
        <p className="link-orig" title={link.original_url}>
          {link.original_url}
        </p>
        <div className="link-meta">
          <StatusBadge status={link.status} />
          <RiskBadge risk={link.risk} />
          {link.tags?.map((t) => (
            <span key={t} className="tag">
              #{t}
            </span>
          ))}
          <span className="muted small">Created {timeAgo(link.created_at)}</span>
        </div>
      </div>
      <div className="link-clicks">
        <strong>{compact(link.clicks)}</strong>
        <span>clicks</span>
      </div>
      <div className="link-actions">
        <Link to={`/links/${link.id}`} className="icon-btn" title="Analytics">
          <BarChart2 size={16} />
        </Link>
        <button className="icon-btn" onClick={() => setQr(true)} title="QR code">
          <QrCode size={16} />
        </button>
        <div className="menu-wrap">
          <button className="icon-btn" onClick={() => setMenu((m) => !m)} title="More">
            <MoreHorizontal size={16} />
          </button>
          {menu && (
            <>
              <div className="menu-overlay" onClick={() => setMenu(false)} />
              <div className="dropdown right">
                <button
                  onClick={() => {
                    setMenu(false)
                    setEdit(true)
                  }}
                >
                  <Pencil size={15} /> Edit
                </button>
                <button onClick={toggleActive}>
                  {link.is_active ? <Pause size={15} /> : <Play size={15} />} {link.is_active ? 'Pause' : 'Resume'}
                </button>
                <button className="danger" onClick={remove}>
                  <Trash2 size={15} /> Delete
                </button>
              </div>
            </>
          )}
        </div>
      </div>
      {qr && <QrModal link={link} onClose={() => setQr(false)} />}
      {edit && <EditLinkModal link={link} onClose={() => setEdit(false)} onSaved={onChange} />}
    </div>
  )
}
