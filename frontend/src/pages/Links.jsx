import { useCallback, useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight, Download, Layers, Link2, Plus, Search } from 'lucide-react'
import toast from 'react-hot-toast'
import api, { downloadFile, errorMessage } from '../api/client'
import BulkModal from '../components/BulkModal'
import CreateLinkForm from '../components/CreateLinkForm'
import EmptyState from '../components/EmptyState'
import LinkRow from '../components/LinkRow'
import Modal from '../components/Modal'
import Spinner from '../components/Spinner'

const STATUSES = [
  ['all', 'All'],
  ['active', 'Active'],
  ['expired', 'Expired'],
  ['disabled', 'Paused'],
  ['limit_reached', 'Limit reached'],
]

export default function Links() {
  const [data, setData] = useState(null)
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('all')
  const [sort, setSort] = useState('newest')
  const [page, setPage] = useState(1)
  const [bulk, setBulk] = useState(false)
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => {
      setQuery(search)
      setPage(1)
    }, 300)
    return () => clearTimeout(t)
  }, [search])

  const load = useCallback(async () => {
    try {
      const res = await api.get('/links', { params: { search: query, status, sort, page, limit: 10 } })
      setData(res.data)
    } catch (err) {
      toast.error(errorMessage(err))
    }
  }, [query, status, sort, page])

  useEffect(() => {
    load()
  }, [load])

  const updateRow = (updated) => setData((d) => ({ ...d, links: d.links.map((l) => (l.id === updated.id ? updated : l)) }))

  const exportCsv = () => downloadFile('/links/export', 'linksense-links.csv').catch((err) => toast.error(errorMessage(err)))

  return (
    <div className="container">
      <div className="page-head">
        <div>
          <h1>My links</h1>
          <p className="muted">{data ? `${data.total} link${data.total === 1 ? '' : 's'}` : 'Loading…'}</p>
        </div>
        <div className="head-actions">
          <button className="btn ghost" onClick={exportCsv}>
            <Download size={16} /> Export CSV
          </button>
          <button className="btn soft" onClick={() => setBulk(true)}>
            <Layers size={16} /> Bulk shorten
          </button>
          <button className="btn primary" onClick={() => setCreating(true)}>
            <Plus size={16} /> New link
          </button>
        </div>
      </div>

      <div className="card toolbar">
        <div className="input-icon grow">
          <Search size={16} />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by URL, alias, title or tag" />
        </div>
        <div className="segmented">
          {STATUSES.map(([value, label]) => (
            <button
              key={value}
              className={status === value ? 'on' : ''}
              onClick={() => {
                setStatus(value)
                setPage(1)
              }}
            >
              {label}
            </button>
          ))}
        </div>
        <select value={sort} onChange={(e) => setSort(e.target.value)} className="sort-select">
          <option value="newest">Newest first</option>
          <option value="oldest">Oldest first</option>
          <option value="clicks">Most clicks</option>
        </select>
      </div>

      <div className="card">
        {!data ? (
          <Spinner full />
        ) : data.links.length === 0 ? (
          <EmptyState
            icon={Link2}
            title={query || status !== 'all' ? 'Nothing matches' : 'No links yet'}
            text={query || status !== 'all' ? 'Try a different search or filter.' : 'Create your first short link to see it here.'}
          />
        ) : (
          <div className="link-list">
            {data.links.map((l) => (
              <LinkRow key={l.id} link={l} onChange={updateRow} onDelete={load} />
            ))}
          </div>
        )}
        {data && data.pages > 1 && (
          <div className="pager">
            <button className="icon-btn" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              <ChevronLeft size={16} />
            </button>
            <span>
              Page {data.page} of {data.pages}
            </span>
            <button className="icon-btn" disabled={page >= data.pages} onClick={() => setPage((p) => p + 1)}>
              <ChevronRight size={16} />
            </button>
          </div>
        )}
      </div>

      {bulk && <BulkModal onClose={() => setBulk(false)} onDone={load} />}
      {creating && (
        <Modal title="New short link" onClose={() => setCreating(false)} width={720}>
          <CreateLinkForm onCreated={load} />
        </Modal>
      )}
    </div>
  )
}
