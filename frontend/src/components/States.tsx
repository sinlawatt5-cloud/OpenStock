import { CloudOff, Clock3, RotateCw } from 'lucide-react'
import type { ReactNode } from 'react'
import { ageLabel } from '../lib/format'

export function SkeletonBlock({
  height = 16,
  width = '100%',
  radius = 8,
  className = '',
}: {
  height?: number
  width?: number | string
  radius?: number
  className?: string
}) {
  return (
    <span
      aria-hidden="true"
      className={`skeleton ${className}`}
      style={{ display: 'block', height, width, borderRadius: radius }}
    />
  )
}

export function RowsSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '6px 10px 12px' }}>
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <SkeletonBlock height={34} width={34} radius={11} />
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 5 }}>
            <SkeletonBlock height={10} width={`${52 + (index % 3) * 12}%`} />
            <SkeletonBlock height={8} width={`${30 + (index % 2) * 14}%`} />
          </div>
          <SkeletonBlock height={12} width={54} />
        </div>
      ))}
    </div>
  )
}

export function ErrorState({
  message,
  onRetry,
  compact = false,
}: {
  message: string
  onRetry?: () => void
  compact?: boolean
}) {
  return (
    <div className="error-box" style={compact ? { padding: 16 } : undefined} role="alert">
      <CloudOff size={22} strokeWidth={1.7} aria-hidden="true" />
      <strong>ดึงข้อมูลไม่สำเร็จ</strong>
      <span>{message}</span>
      {onRetry ? (
        <button type="button" className="icon-btn" onClick={onRetry} style={{ marginTop: 4 }}>
          <RotateCw size={13} aria-hidden="true" />
          ลองอีกครั้ง
        </button>
      ) : null}
    </div>
  )
}

export function StaleBadge({ stale, ageSeconds }: { stale?: boolean; ageSeconds?: number }) {
  if (!stale) return null
  return (
    <span className="stale-badge" title="กำลังแสดงข้อมูลจากแคชระหว่างรอรีเฟรช">
      <Clock3 size={11} aria-hidden="true" />
      ข้อมูลล่าช้า {ageLabel(ageSeconds)}
    </span>
  )
}

export function AsyncNote({ children }: { children: ReactNode }) {
  return (
    <p className="muted" style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
      {children}
    </p>
  )
}
