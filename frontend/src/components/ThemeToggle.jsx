import { Moon, Sun } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'

export default function ThemeToggle({ floating = false }) {
  const { theme, toggle } = useTheme()
  const dark = theme === 'dark'
  return (
    <button
      type="button"
      className={`theme-toggle ${floating ? 'floating' : ''}`}
      onClick={toggle}
      aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={dark ? 'Light mode' : 'Dark mode'}
    >
      <span className={`theme-thumb ${dark ? 'on' : ''}`}>{dark ? <Moon size={14} /> : <Sun size={14} />}</span>
    </button>
  )
}
