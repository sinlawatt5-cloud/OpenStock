import { ArrowDownRight, ArrowUpRight } from 'lucide-react'
import { fmtPct } from '../lib/format'

type Props = {
  value: number | null | undefined
  hero?: boolean
  showIcon?: boolean
  title?: string
}

export function Delta({ value, hero = false, showIcon = true, title }: Props) {
  const tone = value === null || value === undefined || !Number.isFinite(value)
    ? 'flat'
    : value > 0
      ? 'up'
      : value < 0
        ? 'down'
        : 'flat'
  const Icon = tone === 'up' ? ArrowUpRight : tone === 'down' ? ArrowDownRight : null
  const label =
    tone === 'up'
      ? 'เพิ่มขึ้น'
      : tone === 'down'
        ? 'ลดลง'
        : 'ไม่เปลี่ยนแปลง'

  return (
    <span
      className={`delta delta--${tone}${hero ? ' delta--hero' : ''}`}
      title={title}
      aria-label={`${label} ${fmtPct(value === null || value === undefined ? null : Math.abs(value))}`}
    >
      {showIcon && Icon ? <Icon aria-hidden="true" strokeWidth={2.4} /> : null}
      {fmtPct(value)}
    </span>
  )
}
