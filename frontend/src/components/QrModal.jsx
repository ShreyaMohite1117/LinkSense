import { useState } from 'react'
import { Download } from 'lucide-react'
import Modal from './Modal'
import CopyButton from './CopyButton'

const API = `${import.meta.env.VITE_API_URL || ''}/api`
const COLORS = ['111827', '0d9488', '4f46e5', 'be123c', 'b45309']

export default function QrModal({ link, onClose }) {
  const [fg, setFg] = useState(COLORS[0])
  const src = `${API}/qr/${link.short_code}?fg=${fg}`

  return (
    <Modal title="QR code" onClose={onClose} width={400}>
      <div className="qr-wrap">
        <img src={src} alt={`QR code for ${link.short_url}`} width="240" height="240" />
        <div className="qr-colors">
          {COLORS.map((c) => (
            <button
              key={c}
              className={`swatch ${c === fg ? 'on' : ''}`}
              style={{ background: `#${c}` }}
              onClick={() => setFg(c)}
              aria-label={`Colour #${c}`}
            />
          ))}
        </div>
        <div className="qr-url">
          <code>{link.short_url}</code>
          <CopyButton text={link.short_url} />
        </div>
        <a className="btn primary block" href={`${src}&download=1`} download={`${link.short_code}-qr.png`}>
          <Download size={16} /> Download PNG
        </a>
      </div>
    </Modal>
  )
}
