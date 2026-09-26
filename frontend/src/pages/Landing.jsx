import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  BarChart3,
  BrainCircuit,
  CalendarClock,
  Gauge,
  KeyRound,
  QrCode,
  Radar,
  ScanSearch,
  ShieldCheck,
  Zap,
} from 'lucide-react'
import api, { errorMessage } from '../api/client'
import Logo from '../components/Logo'
import RiskBadge from '../components/RiskBadge'
import ThemeToggle from '../components/ThemeToggle'
import { useAuth } from '../context/AuthContext'

const FEATURES = [
  { icon: ShieldCheck, title: 'Phishing detection', text: 'A gradient boosted classifier scores every destination on 25 URL features and blocks the bad ones.' },
  { icon: BrainCircuit, title: 'Click forecasting', text: 'A Random Forest trained on hourly traffic patterns predicts the next 24 hours for each link.' },
  { icon: Radar, title: 'Anomaly detection', text: 'Isolation Forest flags click bursts, scrapers and bots so your numbers stay honest.' },
  { icon: BarChart3, title: 'Rich analytics', text: 'Countries, devices, browsers, referrers and peak hours with plain-English insights.' },
  { icon: Zap, title: 'Fast redirects', text: 'Hot links are served from Redis with cache-aside lookups and per-user rate limiting.' },
  { icon: KeyRound, title: 'Password protection', text: 'Lock a link behind a password - handy for resumes and private docs.' },
  { icon: CalendarClock, title: 'Expiry & click limits', text: 'Links that switch themselves off after a date or a number of clicks.' },
  { icon: QrCode, title: 'QR codes', text: 'Every link gets a colour-customisable QR code, ready to download.' },
]

const STACK = ['React', 'Vite', 'Flask', 'MongoDB', 'Redis', 'scikit-learn', 'JWT', 'Docker']

function HeroScanner() {
  const [url, setUrl] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const scan = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const { data } = await api.post('/scan', { url })
      setResult(data)
    } catch (err) {
      setError(errorMessage(err))
      setResult(null)
    } finally {
      setBusy(false)
    }
  }

  const examples = ['https://github.com/pallets/flask', 'http://paypal.com.secure-login.verify-acc.tk/webscr']

  return (
    <div className="hero-scanner card">
      <p className="eyebrow">
        <ScanSearch size={14} /> Try the phishing model - no account needed
      </p>
      <form onSubmit={scan} className="create-main">
        <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="Paste any URL" required />
        <button className="btn primary" disabled={busy}>
          {busy ? 'Scanning…' : 'Scan'}
        </button>
      </form>
      <div className="examples">
        {examples.map((ex) => (
          <button key={ex} type="button" onClick={() => setUrl(ex)}>
            {ex.length > 44 ? ex.slice(0, 44) + '…' : ex}
          </button>
        ))}
      </div>
      {error && <p className="bad-text small">{error}</p>}
      {result && (
        <div className="scan-mini">
          <div className="scan-mini-head">
            <RiskBadge risk={result} showScore />
            <span className="muted small">{result.domain}</span>
          </div>
          <div className="meter">
            <span className={result.verdict} style={{ width: `${Math.max(result.score * 100, 3)}%` }} />
          </div>
          {result.reasons.length > 0 ? (
            <ul>
              {result.reasons.slice(0, 3).map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          ) : (
            <p className="small muted">No red flags found.</p>
          )}
        </div>
      )}
    </div>
  )
}

export default function Landing() {
  const { user } = useAuth()
  return (
    <div className="landing">
      <header className="landing-nav">
        <Logo />
        <div className="nav-right">
          <ThemeToggle />
          {user ? (
            <Link to="/dashboard" className="btn primary sm">
              Dashboard
            </Link>
          ) : (
            <>
              <Link to="/login" className="btn ghost sm">
                Log in
              </Link>
              <Link to="/signup" className="btn primary sm">
                Sign up
              </Link>
            </>
          )}
        </div>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <span className="pill">
            <Gauge size={14} /> ML-powered URL shortener
          </span>
          <h1>
            Short links that <span className="accent-text">think</span> before they redirect.
          </h1>
          <p>
            LinkSense shortens your URLs, checks them for phishing, predicts how they'll perform and flags suspicious
            traffic - all from one clean dashboard.
          </p>
          <div className="hero-cta">
            <Link to={user ? '/dashboard' : '/signup'} className="btn primary lg">
              Get started free <ArrowRight size={18} />
            </Link>
            <Link to="/login" state={{ from: '/dashboard' }} className="btn ghost lg">
              View live demo
            </Link>
          </div>
          <p className="muted small">Demo login: demo@linksense.dev / Demo@1234</p>
        </div>
        <HeroScanner />
      </section>

      <section className="section">
        <h2 className="section-title">Everything a link needs</h2>
        <p className="section-sub">The basics you expect from a shortener, plus three models working in the background.</p>
        <div className="feature-grid">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <div key={title} className="card feature">
              <div className="stat-icon accent">
                <Icon size={18} />
              </div>
              <h3>{title}</h3>
              <p>{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="section how">
        <h2 className="section-title">What happens when you shorten a link</h2>
        <ol className="steps">
          <li>
            <b>1</b>
            <div>
              <h4>Scan</h4>
              <p>URL features go through the phishing classifier. High-risk links are refused.</p>
            </div>
          </li>
          <li>
            <b>2</b>
            <div>
              <h4>Store & cache</h4>
              <p>The link is saved in MongoDB and cached in Redis on first hit, so redirects stay fast.</p>
            </div>
          </li>
          <li>
            <b>3</b>
            <div>
              <h4>Track</h4>
              <p>Each click logs device, browser, country and referrer - no raw IPs are stored.</p>
            </div>
          </li>
          <li>
            <b>4</b>
            <div>
              <h4>Learn</h4>
              <p>Forecasts and anomaly checks run on your real click history every time you open analytics.</p>
            </div>
          </li>
        </ol>
      </section>

      <section className="section stack-section">
        <p className="muted small">BUILT WITH</p>
        <div className="stack-list">
          {STACK.map((s) => (
            <span key={s}>{s}</span>
          ))}
        </div>
      </section>

      <footer className="landing-foot">
        <Logo />
        <p className="muted small">© {new Date().getFullYear()} LinkSense. Made as a full-stack + ML project.</p>
      </footer>
    </div>
  )
}
