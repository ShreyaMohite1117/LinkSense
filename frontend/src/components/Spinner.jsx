export default function Spinner({ full = false, size = 22 }) {
  const el = <span className="spinner" style={{ width: size, height: size }} aria-label="Loading" />
  if (!full) return el
  return <div className="spinner-full">{el}</div>
}
