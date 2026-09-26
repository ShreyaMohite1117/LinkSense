import { ShieldAlert, ShieldCheck, ShieldX } from 'lucide-react'

const MAP = {
  safe: { cls: 'ok', icon: ShieldCheck, label: 'Safe' },
  suspicious: { cls: 'warn', icon: ShieldAlert, label: 'Suspicious' },
  malicious: { cls: 'bad', icon: ShieldX, label: 'Malicious' },
}

export default function RiskBadge({ risk, showScore = false }) {
  if (!risk) return null
  const { cls, icon: Icon, label } = MAP[risk.verdict] || MAP.safe
  return (
    <span className={`badge ${cls}`} title={`Phishing score ${(risk.score * 100).toFixed(1)}%`}>
      <Icon size={13} />
      {label}
      {showScore && <em>{(risk.score * 100).toFixed(0)}%</em>}
    </span>
  )
}
