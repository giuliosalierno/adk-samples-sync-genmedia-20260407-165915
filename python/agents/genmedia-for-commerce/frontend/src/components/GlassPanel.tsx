import { ReactNode } from 'react'

interface GlassPanelProps {
  children: ReactNode
  className?: string
  onClick?: () => void
}

function GlassPanel({ children, className = '', onClick }: GlassPanelProps) {
  return (
    <div
      className={`glass-panel ${className}`}
      onClick={onClick}
    >
      {children}
    </div>
  )
}

export default GlassPanel
