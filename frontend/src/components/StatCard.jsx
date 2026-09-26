export default function StatCard({ icon: Icon, label, value, hint, tone = 'accent' }) {
  return (
    <div className="card stat-card">
      <div className={`stat-icon ${tone}`}>
        <Icon size={18} />
      </div>
      <div>
        <p className="stat-label">{label}</p>
        <p className="stat-value">{value}</p>
        {hint && <p className="stat-hint">{hint}</p>}
      </div>
    </div>
  )
}
