import { useState } from 'react'
import { Check, Copy } from 'lucide-react'
import toast from 'react-hot-toast'
import { copyText } from '../utils/format'

export default function CopyButton({ text, label, className = 'icon-btn' }) {
  const [done, setDone] = useState(false)
  const onClick = async () => {
    if (await copyText(text)) {
      setDone(true)
      toast.success('Copied to clipboard')
      setTimeout(() => setDone(false), 1500)
    }
  }
  return (
    <button type="button" className={className} onClick={onClick} title="Copy">
      {done ? <Check size={16} /> : <Copy size={16} />}
      {label && <span>{label}</span>}
    </button>
  )
}
