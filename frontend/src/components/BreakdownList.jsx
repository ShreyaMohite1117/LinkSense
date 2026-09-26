export default function BreakdownList({ items = [], total, render = (i) => i.name, empty = 'No data yet' }) {
  if (!items.length) return <p className="muted small">{empty}</p>
  const sum = total || items.reduce((s, i) => s + i.count, 0) || 1
  return (
    <ul className="breakdown">
      {items.map((item) => {
        const pct = Math.round((item.count / sum) * 100)
        return (
          <li key={item.name}>
            <div className="breakdown-row">
              <span className="breakdown-name">{render(item)}</span>
              <span className="breakdown-val">
                {item.count.toLocaleString()} <small>{pct}%</small>
              </span>
            </div>
            <div className="bar">
              <span style={{ width: `${Math.max(pct, 2)}%` }} />
            </div>
          </li>
        )
      })}
    </ul>
  )
}
