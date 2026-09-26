import { useEffect, useRef, useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { BarChart3, ChevronDown, Link2, LogOut, Settings, ShieldCheck } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import Logo from './Logo'
import ThemeToggle from './ThemeToggle'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: BarChart3 },
  { to: '/links', label: 'My Links', icon: Link2 },
  { to: '/scanner', label: 'URL Scanner', icon: ShieldCheck },
]

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const menuRef = useRef(null)

  useEffect(() => {
    const close = (e) => menuRef.current && !menuRef.current.contains(e.target) && setOpen(false)
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])

  const initials = (user?.name || '?')
    .split(' ')
    .map((p) => p[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <Logo to="/dashboard" />
        <nav className="nav-links">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <Icon size={16} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="nav-right">
          <ThemeToggle />
          <div className="user-menu" ref={menuRef}>
            <button className="user-btn" onClick={() => setOpen((o) => !o)}>
              <span className="avatar">{initials}</span>
              <span className="user-name">{user?.name?.split(' ')[0]}</span>
              <ChevronDown size={14} />
            </button>
            {open && (
              <div className="dropdown">
                <div className="dropdown-head">
                  <strong>{user?.name}</strong>
                  <small>{user?.email}</small>
                </div>
                <button
                  onClick={() => {
                    setOpen(false)
                    navigate('/settings')
                  }}
                >
                  <Settings size={15} /> Settings
                </button>
                <button
                  className="danger"
                  onClick={() => {
                    logout()
                    navigate('/login')
                  }}
                >
                  <LogOut size={15} /> Log out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
