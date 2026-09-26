export default function ChartTooltip({ active, payload, label, labelFormat = (l) => l }) {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tip">
      <p>{labelFormat(label)}</p>
      {payload
        .filter((p) => p.value != null)
        .map((p) => (
          <p key={p.dataKey}>
            <i style={{ background: p.color }} /> {p.name}: <b>{Math.round(p.value * 10) / 10}</b>
          </p>
        ))}
    </div>
  )
}
