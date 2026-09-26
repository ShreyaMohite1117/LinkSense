import { BrainCircuit, ShieldCheck, Zap } from 'lucide-react'
import Logo from './Logo'
import ThemeToggle from './ThemeToggle'

export default function AuthLayout({ title, subtitle, children }) {
  return (
    <div className="auth-page">
      <ThemeToggle floating />
      <aside className="auth-side">
        <Logo />
        <div className="auth-pitch">
          <h2>Short links that know when something's off.</h2>
          <ul>
            <li>
              <ShieldCheck size={18} /> Phishing URLs are caught before they get a short link
            </li>
            <li>
              <BrainCircuit size={18} /> Random Forest forecasts your next 24 hours of clicks
            </li>
            <li>
              <Zap size={18} /> Redis-cached redirects and bot detection on every click
            </li>
          </ul>
        </div>
        <p className="auth-foot">Built with React, Flask, MongoDB &amp; scikit-learn</p>
      </aside>
      <section className="auth-main">
        <div className="auth-card">
          <div className="auth-mobile-logo">
            <Logo />
          </div>
          <h1>{title}</h1>
          <p className="muted">{subtitle}</p>
          {children}
        </div>
      </section>
    </div>
  )
}
