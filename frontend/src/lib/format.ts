const priceFmt = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

const compactFmt = new Intl.NumberFormat('en-US', {
  notation: 'compact',
  maximumFractionDigits: 1,
})

const relativeFmt = new Intl.RelativeTimeFormat('th', { numeric: 'auto' })

export function fmtPrice(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—'
  if (digits === 2) return priceFmt.format(value)
  return value.toLocaleString('en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

export function fmtPct(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(digits)}%`
}

export function fmtSigned(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(digits)}`
}

export function fmtVolume(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—'
  return compactFmt.format(value)
}

export function fmtMoneyCompact(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—'
  return `$${compactFmt.format(value)}`
}

export function fmtInt(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—'
  return new Intl.NumberFormat('th-TH').format(value)
}

export function fmtThaiDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('th-TH', {
    timeZone: 'Asia/Bangkok',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(date)
}

export function fmtThaiShortDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('th-TH', {
    timeZone: 'Asia/Bangkok',
    day: 'numeric',
    month: 'short',
  }).format(date)
}

export function fmtThaiTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('th-TH', {
    timeZone: 'Asia/Bangkok',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date)
}

export function timeAgo(iso: string | null | undefined): string {
  if (!iso) return ''
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  const diff = date.getTime() - Date.now()
  const abs = Math.abs(diff)
  if (abs < 60_000) return 'เมื่อสักครู่'
  if (abs < 3_600_000) return relativeFmt.format(Math.round(diff / 60_000), 'minute')
  if (abs < 86_400_000) return relativeFmt.format(Math.round(diff / 3_600_000), 'hour')
  return relativeFmt.format(Math.round(diff / 86_400_000), 'day')
}

export function ageLabel(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return ''
  if (seconds < 90) return 'เมื่อสักครู่'
  if (seconds < 3600) return `${Math.round(seconds / 60)} นาทีที่แล้ว`
  return `${Math.round(seconds / 3600)} ชั่วโมงที่แล้ว`
}

type MarketClock = {
  isOpen: boolean
  label: string
  bangkokTime: string
}

/** Regular US session (Mon–Fri 09:30–16:00 ET). Holidays are not modelled. */
export function marketClock(now = new Date()): MarketClock {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    weekday: 'short',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).formatToParts(now)
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? ''
  const weekday = get('weekday')
  const hour = Number(get('hour'))
  const minute = Number(get('minute'))
  const minutes = hour * 60 + minute
  const tradingDay = !['Sat', 'Sun'].includes(weekday)
  const isOpen = tradingDay && minutes >= 570 && minutes < 960
  const bangkokTime = new Intl.DateTimeFormat('th-TH', {
    timeZone: 'Asia/Bangkok',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(now)
  return {
    isOpen,
    label: isOpen ? 'ตลาดเปิด' : 'ตลาดปิด',
    bangkokTime,
  }
}

export function strengthLabel(strength: number): { label: string; tone: 'strong' | 'mid' | 'weak' } {
  if (strength >= 0.62) return { label: 'แข็ง', tone: 'strong' }
  if (strength >= 0.44) return { label: 'ปานกลาง', tone: 'mid' }
  return { label: 'อ่อน', tone: 'weak' }
}

export function providerLabel(provider: string): string {
  if (provider === 'gemini') return 'AI · Gemini'
  if (provider === 'openrouter') return 'AI · OpenRouter'
  return 'สรุปอัตโนมัติ'
}

const AVATAR_COLORS = ['#FFE0B8', '#FFD6CF', '#E2F3E9', '#FFEBC6', '#F6DEEA', '#E3EBF8', '#F3E4CE']

export function avatarColor(seed: string): string {
  let hash = 0
  for (let i = 0; i < seed.length; i += 1) hash = (hash * 31 + seed.charCodeAt(i)) % 9973
  return AVATAR_COLORS[hash % AVATAR_COLORS.length]
}

export function initials(symbol: string): string {
  return symbol.replace(/[^A-Z0-9]/gi, '').slice(0, 2).toUpperCase()
}
