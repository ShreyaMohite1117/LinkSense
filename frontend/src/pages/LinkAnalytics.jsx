import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  AlertTriangle,
  ArrowLeft,
  Bot,
  BrainCircuit,
  Clock,
  Download,
  ExternalLink,
  MousePointerClick,
  QrCode,
  Radar,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Users,
} from 'lucide-react'
import toast from 'react-hot-toast'
import api, { downloadFile, errorMessage } from '../api/client'
import BreakdownList from '../components/BreakdownList'
import ChartTooltip from '../components/ChartTooltip'
import CopyButton from '../components/CopyButton'
import EmptyState from '../components/EmptyState'
import QrModal from '../components/QrModal'
import RiskBadge from '../components/RiskBadge'
import Spinner from '../components/Spinner'
import StatCard from '../components/StatCard'
import StatusBadge from '../components/StatusBadge'
import { compact, countryName, dateTime, flag, shortDate } from '../utils/format'

const hourLabel = (iso) => new Date(iso).toLocaleString('en-IN', { weekday: 'short', hour: '2-digit' })

function TrendIcon({ trend }) {
  if (trend === 'rising') return <TrendingUp size={16} className="ok-text" />
  if (trend === 'falling') return <TrendingDown size={16} className="bad-text" />
  return <Clock size={16} className="muted" />
}

export default function LinkAnalytics() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [qr, setQr] = useState(false)
  const [tab, setTab] = useState('countries')

  useEffect(() => {
    api
      .get(`/analytics/links/${id}`)
      .then((res) => setData(res.data))
      .catch((err) => setError(errorMessage(err)))
  }, [id])

  // stitch the last 48h of real clicks and the 24h forecast into one series
  const forecastSeries = useMemo(() => {
    if (!data) return []
    const hist = data.forecast.history.map((h) => ({ hour: h.hour, actual: h.clicks, predicted: null }))
    if (hist.length) hist[hist.length - 1].predicted = hist[hist.length - 1].actual
    return [...hist, ...data.forecast.forecast.map((f) => ({ hour: f.hour, actual: null, predicted: f.predicted }))]
  }, [data])

  const hourBuckets = useMemo(() => {
    const b = data?.stats.hour_buckets
    if (!b) return []
    // server buckets are UTC - shift to the viewer's local time
    const offset = -new Date().getTimezoneOffset() / 60
    return Array.from({ length: 24 }, (_, local) => {
      const utc = (((local - offset) % 24) + 24) % 24
      const lo = Math.floor(utc)
      const frac = utc - lo
      const v = b[lo] * (1 - frac) + b[(lo + 1) % 24] * frac
      return { hour: `${String(local).padStart(2, '0')}`, clicks: Math.round(v) }
    })
  }, [data])

  if (error)
    return (
      <div className="container">
        <EmptyState icon={AlertTriangle} title="Couldn't load analytics" text={error} action={<Link to="/links" className="btn primary">Back to links</Link>} />
      </div>
    )
  if (!data) return <Spinner full />

  const { link, stats, forecast, anomalies, insights } = data
  const peak = Math.max(...hourBuckets.map((h) => h.clicks), 0)
  const breakdowns = {
    countries: { items: stats.countries, render: (i) => `${flag(i.name)} ${countryName(i.name)}` },
    referrers: { items: stats.referrers, render: (i) => (i.name === 'direct' ? 'Direct / none' : i.name) },
    browsers: { items: stats.browsers },
    os: { items: stats.os },
  }

  return (
    <div className="container">
      <Link to="/links" className="back-link">
        <ArrowLeft size={16} /> All links
      </Link>

      <div className="card link-hero">
        <div className="link-hero-main">
          <div className="link-meta">
            <StatusBadge status={link.status} />
            <RiskBadge risk={link.risk} showScore />
            <span className="muted small">Created {shortDate(link.created_at)}</span>
          </div>
          <h1>{link.title || `/${link.short_code}`}</h1>
          <div className="link-short big">
            <a href={link.short_url} target="_blank" rel="noreferrer">
              {link.short_url.replace(/^https?:\/\//, '')}
            </a>
            <CopyButton text={link.short_url} />
          </div>
          <a className="link-orig" href={link.original_url} target="_blank" rel="noreferrer">
            {link.original_url} <ExternalLink size={12} />
          </a>
        </div>
        <div className="head-actions">
          <button className="btn ghost" onClick={() => setQr(true)}>
            <QrCode size={16} /> QR
          </button>
          <button
            className="btn soft"
            onClick={() => downloadFile(`/analytics/links/${link.id}/export`, `clicks-${link.short_code}.csv`).catch((e) => toast.error(errorMessage(e)))}
          >
            <Download size={16} /> Export clicks
          </button>
        </div>
      </div>

      <div className="card insights">
        <div className="card-head">
          <h3>
            <Sparkles size={17} /> AI insights
          </h3>
        </div>
        <ul>
          {insights.map((t) => (
            <li key={t}>{t.replace(/from ([A-Z]{2})\./, (_, c) => `from ${countryName(c)}.`)}</li>
          ))}
        </ul>
      </div>

      <div className="stats-grid">
        <StatCard icon={MousePointerClick} label="Total clicks" value={compact(link.clicks)} hint={link.max_clicks ? `Limit ${link.max_clicks}` : null} />
        <StatCard icon={Users} label="Unique visitors" value={compact(link.unique_clicks)} tone="violet" />
        <StatCard icon={Bot} label="Bot clicks" value={compact(stats.bot_clicks)} hint={`${Math.round(anomalies.bot_rate * 100)}% of traffic`} tone="amber" />
        <StatCard
          icon={Radar}
          label="Anomalies flagged"
          value={anomalies.flagged || 0}
          hint={anomalies.method === 'isolation_forest' ? 'Isolation Forest' : anomalies.method === 'rules' ? 'Rule based (needs 25+ clicks for ML)' : '-'}
          tone="rose"
        />
      </div>

      <div className="grid-2 wide">
        <div className="card">
          <div className="card-head">
            <h3>
              <BrainCircuit size={17} /> 24h click forecast
            </h3>
            <span className="forecast-pill">
              <TrendIcon trend={forecast.summary.trend} />
              {forecast.summary.trend === 'quiet'
                ? 'Quiet'
                : forecast.summary.trend === 'warming_up'
                ? 'Learning'
                : `${forecast.summary.change_pct > 0 ? '+' : ''}${forecast.summary.change_pct}%`}
            </span>
          </div>
          <p className="muted small">
            Random Forest prediction: <b>{forecast.summary.predicted_next_24h}</b> clicks in the next 24 hours (vs {forecast.summary.last_24h} in the last 24).
          </p>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={250}>
              <ComposedChart data={forecastSeries} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="hour" tickFormatter={hourLabel} interval={11} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis allowDecimals={false} tick={{ fill: 'var(--text-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTooltip labelFormat={hourLabel} />} />
                {forecast.history.length > 0 && <ReferenceLine x={forecast.history[forecast.history.length - 1].hour} stroke="var(--text-muted)" strokeDasharray="4 4" />}
                <Bar dataKey="actual" name="Actual" fill="var(--accent)" radius={[3, 3, 0, 0]} />
                <Line dataKey="predicted" name="Forecast" stroke="var(--violet)" strokeWidth={2.4} strokeDasharray="6 4" dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-head">
            <h3>
              <Clock size={17} /> When people click (your time)
            </h3>
          </div>
          {peak === 0 ? (
            <EmptyState icon={Clock} title="No clicks yet" text="Peak hours show up once people start clicking." />
          ) : (
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={270}>
              <BarChart data={hourBuckets} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="hour" interval={2} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis allowDecimals={false} tick={{ fill: 'var(--text-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTooltip labelFormat={(h) => `${h}:00`} />} cursor={{ fill: 'var(--surface-2)' }} />
                <Bar dataKey="clicks" name="Clicks" radius={[3, 3, 0, 0]}>
                  {hourBuckets.map((h) => (
                    <Cell key={h.hour} fill={h.clicks === peak && peak > 0 ? 'var(--accent)' : 'var(--accent-soft-strong)'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <h3>Clicks, last 30 days</h3>
        </div>
        <div className="chart-box">
          <ResponsiveContainer width="100%" height={230}>
            <AreaChart data={stats.daily} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
              <defs>
                <linearGradient id="dailyFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--blue)" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="var(--blue)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="date" tickFormatter={(d) => d.slice(5)} tick={{ fill: 'var(--text-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis allowDecimals={false} tick={{ fill: 'var(--text-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip content={<ChartTooltip />} />
              <Area type="monotone" dataKey="clicks" name="Clicks" stroke="var(--blue)" strokeWidth={2} fill="url(#dailyFill)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid-2 wide">
        <div className="card">
          <div className="card-head">
            <div className="segmented">
              {Object.keys(breakdowns).map((k) => (
                <button key={k} className={tab === k ? 'on' : ''} onClick={() => setTab(k)}>
                  {k === 'os' ? 'OS' : k[0].toUpperCase() + k.slice(1)}
                </button>
              ))}
            </div>
          </div>
          <BreakdownList {...breakdowns[tab]} />
        </div>
        <div className="card">
          <div className="card-head">
            <h3>Devices</h3>
          </div>
          <BreakdownList items={stats.devices} />
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <h3>
            <Radar size={17} /> Suspicious clicks
          </h3>
          <span className="muted small">
            {anomalies.method === 'isolation_forest'
              ? `Isolation Forest over ${anomalies.total} clicks · ${(anomalies.anomaly_rate * 100).toFixed(1)}% flagged`
              : anomalies.method === 'rules'
              ? 'Rule-based until the link has 25+ clicks'
              : ''}
          </span>
        </div>
        {!anomalies.anomalies?.length ? (
          <EmptyState icon={Radar} title="Nothing suspicious" text="Traffic on this link looks normal." />
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Source</th>
                  <th>Client</th>
                  <th>Why it was flagged</th>
                  <th>Score</th>
                </tr>
              </thead>
              <tbody>
                {anomalies.anomalies.slice(0, 15).map((a, i) => (
                  <tr key={i}>
                    <td className="nowrap">{dateTime(a.ts)}</td>
                    <td className="nowrap">
                      {flag(a.country)} <span className="mono">{a.ip}</span>
                    </td>
                    <td className="nowrap">
                      {a.browser} · {a.device}
                    </td>
                    <td>{a.reasons.join(' · ')}</td>
                    <td>
                      <div className="meter tiny">
                        <span className="malicious" style={{ width: `${Math.max(a.score * 100, 5)}%` }} />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {qr && <QrModal link={link} onClose={() => setQr(false)} />}
    </div>
  )
}
