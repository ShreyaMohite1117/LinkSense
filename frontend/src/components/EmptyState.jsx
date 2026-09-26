export default function EmptyState({ icon: Icon, title, text, action }) {
  return (
    <div className="empty">
      {Icon && (
        <div className="empty-icon">
          <Icon size={22} />
        </div>
      )}
      <h4>{title}</h4>
      {text && <p>{text}</p>}
      {action}
    </div>
  )
}
