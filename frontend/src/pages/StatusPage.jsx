import { Link, useSearchParams } from 'react-router-dom'
import { Clock, Link2Off, PauseCircle, MousePointerClick } from 'lucide-react'
import Logo from '../components/Logo'
import ThemeToggle from '../components/ThemeToggle'

const COPY = {
  expired: [Clock, 'This link has expired', 'The owner set an expiry date and it has passed.'],
  disabled: [PauseCircle, 'This link is paused', 'The owner has temporarily switched it off.'],
  limit_reached: [MousePointerClick, 'Click limit reached', 'This link was only allowed a set number of visits.'],
  missing: [Link2Off, "We couldn't find that link", 'Double-check the address, or it may have been deleted.'],
}

export default function StatusPage({ kind }) {
  const [params] = useSearchParams()
  const key = kind || params.get('reason') || 'expired'
  const [Icon, title, text] = COPY[key] || COPY.missing
  const code = params.get('code')

  return (
    <div className="center-page">
      <ThemeToggle floating />
      <div className="card gate">
        <Logo />
        <div className="gate-icon muted-icon">
          <Icon size={24} />
        </div>
        <h2>{title}</h2>
        <p className="muted">
          {text}
          {code && (
            <>
              {' '}
              (<span className="mono">/{code}</span>)
            </>
          )}
        </p>
        <Link to="/" className="btn primary">
          Go to LinkSense
        </Link>
      </div>
    </div>
  )
}
