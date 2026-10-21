import { useId } from 'react'

type Props = {
  data: number[]
  tone?: 'up' | 'down' | 'neutral'
  className?: string
  width?: number
  height?: number
}

export function Sparkline({ data, tone = 'neutral', className = 'sparkline', width = 88, height = 26 }: Props) {
  const gradientId = useId().replace(/:/g, '')
  if (!data || data.length < 2) {
    return <svg className={className} viewBox={`0 0 ${width} ${height}`} aria-hidden="true" />
  }
  const min = Math.min(...data)
  const max = Math.max(...data)
  const span = max - min || 1
  const step = width / (data.length - 1)
  const points = data.map((value, index) => {
    const x = index * step
    const y = height - 3 - ((value - min) / span) * (height - 6)
    return [x, y] as const
  })
  const line = points.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`).join(' ')
  const area = `${line} L${width},${height} L0,${height} Z`
  const stroke = tone === 'up' ? '#0E9F6E' : tone === 'down' ? '#D93F3F' : '#B7791F'

  return (
    <svg
      className={className}
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label="กราฟราคาขนาดย่อ"
      preserveAspectRatio="none"
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={stroke} stopOpacity="0.22" />
          <stop offset="100%" stopColor={stroke} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gradientId})`} />
      <path
        d={line}
        fill="none"
        stroke={stroke}
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
