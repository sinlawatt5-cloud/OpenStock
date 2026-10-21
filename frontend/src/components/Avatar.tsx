import { avatarColor, initials } from '../lib/format'

type Props = {
  symbol: string
  name?: string | null
  logo?: string | null
  className?: string
}

export function Avatar({ symbol, logo, className = 'avatar' }: Props) {
  if (logo) {
    return (
      <span className={className} style={{ background: '#fff' }}>
        <img src={logo} alt="" loading="lazy" referrerPolicy="no-referrer" />
      </span>
    )
  }
  return (
    <span className={className} style={{ background: avatarColor(symbol) }} aria-hidden="true">
      {initials(symbol)}
    </span>
  )
}
