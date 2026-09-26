import { useEffect, useState } from 'react'
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { BrainCircuit, CheckCircle2, Cpu, Radar, ScanSearch, ShieldAlert } from 'lucide-react'
import api, { errorMessage } from '../api/client'
import ChartTooltip from '../components/ChartTooltip'
import RiskBadge from '../components/RiskBadge'

const SAMPLES = [
  'https://github.com/facebook/react',
  'http://192.168.10.4/sbi/kyc-update.html',
  'https://hdfc-netbanking-secure.xyz/login/verify',
  'https://www.linkedin.com/in/some-profile',
  'http://amaz0n-refund.top/claim?id=88231',
]

const pretty = (s) => s.replace(/_/g, ' ')

export default function Scanner() {
  const [url, setUrl] = useState('')
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [models, setModels] = useState(null)

  useEffect(() => {
    api.get('/ml/models').then((r) => setModels(r.data)).catch(() => {})
  }, [])

  const scan = async (value = url) => {
    if (!value) return
    setBusy(true)
    setError('')
    try {
      const { data } = await api.post('/scan', { url: value })
      setResult(data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const importance = models?.phishing?.feature_importance
    ? Object.entries(models.phishing.feature_importance)
        .slice(0, 8)
        .map(([name, value]) => ({ name: pretty(name), value: Math.round(value * 1000) / 10 }))
    : []

  const f = result?.features

  return (
    <div className="container">
      <div className="page-head">
        <div>
          <h1>URL scanner</h1>
          <p className="muted">Check any link with the same phishing model that guards every short link.</p>
        </div>
      </div>

      <div className="card">
        <form
          className="create-main"
          onSubmit={(e) => {
            e.preventDefault()
            scan()
          }}
        >
          <div className="input-icon grow">
            <ScanSearch size={18} />
            <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com/some/page" required />
          </div>
          <button className="btn primary" disabled={busy}>
            {busy ? 'Scanning…' : 'Scan URL'}
          </button>
        </form>
        <div className="examples">
          <span className="muted small">Try:</span>
          {SAMPLES.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => {
                setUrl(s)
                scan(s)
              }}
            >
              {s.replace(/^https?:\/\//, '').slice(0, 34)}
            </button>
          ))}
        </div>
        {error && <div className="alert bad">{error}</div>}
      </div>

      {result && (
        <div className="grid-2 wide">
          <div className={`card verdict-card ${result.verdict}`}>
            <div className="verdict-top">
              {result.verdict === 'safe' ? <CheckCircle2 size={34} /> : <ShieldAlert size={34} />}
              <div>
                <h2>{result.verdict === 'safe' ? 'Looks safe' : result.verdict === 'suspicious' ? 'Be careful' : 'Likely phishing'}</h2>
                <p className="muted small mono">{result.domain || result.url}</p>
              </div>
              <RiskBadge risk={result} showScore />
            </div>
            <div className="meter big">
              <span className={result.verdict} style={{ width: `${Math.max(result.score * 100, 2)}%` }} />
            </div>
            <div className="meter-scale">
              <span>0%</span>
              <span>warn {Math.round((models?.thresholds?.warn ?? 0.5) * 100)}%</span>
              <span>block {Math.round((models?.thresholds?.block ?? 0.8) * 100)}%</span>
              <span>100%</span>
            </div>
            {result.trusted_domain && <p className="small ok-text">Known, trusted domain.</p>}
            {result.reasons.length > 0 ? (
              <>
                <h4>Why</h4>
                <ul className="reason-list">
                  {result.reasons.map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
              </>
            ) : (
              <p className="small muted">No obvious red flags in the URL structure.</p>
            )}
          </div>
          <div className="card">
            <div className="card-head">
              <h3>Extracted features</h3>
            </div>
            <div className="feature-table">
              {Object.entries(f).map(([k, v]) => (
                <div key={k}>
                  <span>{pretty(k)}</span>
                  <b className={typeof v === 'number' && v > 0 && ['has_ip_host', 'has_at', 'brand_mismatch', 'suspicious_tld', 'punycode', 'risky_extension', 'is_shortener'].includes(k) ? 'bad-text' : ''}>
                    {typeof v === 'number' && !Number.isInteger(v) ? v.toFixed(3) : v}
                  </b>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {models && (
        <>
          <h2 className="section-heading">
            <Cpu size={20} /> Under the hood
          </h2>
          <div className="grid-3">
            <div className="card model-card">
              <div className="stat-icon accent">
                <ScanSearch size={18} />
              </div>
              <h3>Phishing classifier</h3>
              <p className="muted small">
                {pretty(models.phishing.chosen_model || '')} picked from 3 candidates · {models.phishing.samples?.toLocaleString()} URLs
              </p>
              <div className="metric-row">
                {Object.entries(models.phishing.test_metrics || {}).map(([k, v]) => (
                  <div key={k}>
                    <b>{k === 'roc_auc' ? v.toFixed(3) : `${(v * 100).toFixed(1)}%`}</b>
                    <span>{k === 'roc_auc' ? 'ROC AUC' : k}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="card model-card">
              <div className="stat-icon violet">
                <BrainCircuit size={18} />
              </div>
              <h3>Click forecaster</h3>
              <p className="muted small">RandomForestRegressor on lag + seasonality features, rolled forward 24h</p>
              <div className="metric-row">
                <div>
                  <b>{models.forecaster.mae_clicks_per_hour}</b>
                  <span>MAE / hour</span>
                </div>
                <div>
                  <b>{models.forecaster.naive_mae_clicks_per_hour}</b>
                  <span>naive MAE</span>
                </div>
                <div>
                  <b>{models.forecaster.improvement_over_naive_pct}%</b>
                  <span>better</span>
                </div>
              </div>
            </div>
            <div className="card model-card">
              <div className="stat-icon rose">
                <Radar size={18} />
              </div>
              <h3>Anomaly detector</h3>
              <p className="muted small">Isolation Forest fitted {models.anomaly.fit}</p>
              <div className="metric-row">
                <div>
                  <b>{models.anomaly.contamination * 100}%</b>
                  <span>contamination</span>
                </div>
                <div>
                  <b>8</b>
                  <span>features</span>
                </div>
                <div>
                  <b>150</b>
                  <span>trees</span>
                </div>
              </div>
            </div>
          </div>

          {importance.length > 0 && (
            <div className="card">
              <div className="card-head">
                <h3>What the phishing model pays attention to</h3>
                <span className="muted small">feature importance, %</span>
              </div>
              <div className="chart-box">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={importance} layout="vertical" margin={{ top: 0, right: 16, left: 40, bottom: 0 }}>
                    <XAxis type="number" hide />
                    <YAxis type="category" dataKey="name" width={130} tick={{ fill: 'var(--text-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
                    <Tooltip content={<ChartTooltip />} cursor={{ fill: 'var(--surface-2)' }} />
                    <Bar dataKey="value" name="Importance %" fill="var(--accent)" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
