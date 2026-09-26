import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Bot, Link2, MousePointerClick, ShieldX, TrendingUp, Users } from 'lucide-react'
import api from '../api/client'
import BreakdownList from '../components/BreakdownList'
import ChartTooltip from '../components/ChartTooltip'
import CreateLinkForm from '../components/CreateLinkForm'
import EmptyState from '../components/EmptyState'
import LinkRow from '../components/LinkRow'
import Spinner from '../components/Spinner'
import StatCard from '../components/StatCard'
import { useAuth } from '../context/AuthContext'
import { compact, countryName, flag } from '../utils/format'

function greeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

export default function Dashboard() {
  const { user } = useAuth()
  const [overview, setOverview] = useState(null)
  const [recent, setRecent] = useState([])

  const load = useCallback(async () => {
    const [o, l] = await Promise.all([api.get('/analytics/overview'), api.get('/links', { params: { limit: 5 } })])
    setOverview(o.data)
    setRecent(l.data.links)
  }, [])

  useEffect(() => {
    load().catch(() => {})
  }, [load])

  const updateRow = (updated) => setRecent((rows) => rows.map((r) => (r.id === updated.id ? updated : r)))
  const removeRow = (id) => {
    setRecent((rows) => rows.filter((r) => r.id !== id))
    load().catch(() => {})
  }

  return (
    <div className="container">
      <div className="page-head">
        <div>
          <h1>
            {greeting()}, {user?.name?.split(' ')[0]} 👋
          </h1>
          <p className="muted">Here's how your links are doing.</p>
        </div>
      </div>

      <CreateLinkForm onCreated={() => load()} />

      {!overview ? (
        <Spinner full />
      ) : (
        <>
          <div className="stats-grid">
            <StatCard icon={Link2} label="Total links" value={compact(overview.total_links)} />
            <StatCard icon={MousePointerClick} label="Total clicks" value={compact(overview.total_clicks)} hint={`${compact(overview.clicks_last_7d)} in the last 7 days`} tone="blue" />
            <StatCard icon={Users} label="Unique visitors" value={compact(overview.unique_clicks)} tone="violet" />
            <StatCard
              icon={Bot}
              label="Bot clicks filtered"
              value={compact(overview.bot_clicks)}
              hint={overview.blocked_links ? `${overview.blocked_links} phishing URLs blocked` : 'No phishing attempts'}
              tone="amber"
            />
          </div>

          <div className="grid-main">
            <div className="card">
              <div className="card-head">
                <h3>
                  <TrendingUp size={17} /> Clicks, last 14 days
                </h3>
              </div>
              <div className="chart-box stretch">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={overview.daily} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
                    <defs>
                      <linearGradient id="clickFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.35} />
                        <stop offset="100%" stopColor="var(--accent)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="date" tickFormatter={(d) => d.slice(5)} tick={{ fill: 'var(--text-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
                    <YAxis allowDecimals={false} tick={{ fill: 'var(--text-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
                    <Tooltip content={<ChartTooltip />} />
                    <Area type="monotone" dataKey="clicks" name="Clicks" stroke="var(--accent)" strokeWidth={2.2} fill="url(#clickFill)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="card">
              <div className="card-head">
                <h3>Top countries</h3>
              </div>
              <BreakdownList items={overview.countries} render={(i) => `${flag(i.name)} ${countryName(i.name)}`} />
              <div className="card-head spaced">
                <h3>Devices</h3>
              </div>
              <BreakdownList items={overview.devices} />
            </div>
          </div>

          <div className="card">
            <div className="card-head">
              <h3>Recent links</h3>
              <Link to="/links" className="btn ghost sm">
                View all
              </Link>
            </div>
            {recent.length === 0 ? (
              <EmptyState icon={Link2} title="No links yet" text="Paste a URL above to create your first short link." />
            ) : (
              <div className="link-list">
                {recent.map((l) => (
                  <LinkRow key={l.id} link={l} onChange={updateRow} onDelete={removeRow} />
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
