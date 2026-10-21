import { describe, expect, it } from 'vitest'
import {
  fmtPct,
  fmtPrice,
  fmtSigned,
  fmtVolume,
  initials,
  marketClock,
  providerLabel,
  strengthLabel,
} from './format'

describe('number formatting', () => {
  it('formats prices with two decimals and separators', () => {
    expect(fmtPrice(7712.569)).toBe('7,712.57')
    expect(fmtPrice(null)).toBe('—')
    expect(fmtPrice(0)).toBe('0.00')
  })

  it('adds a plus sign only for positive percentages', () => {
    expect(fmtPct(1.2)).toBe('+1.20%')
    expect(fmtPct(-9.043)).toBe('-9.04%')
    expect(fmtPct(0)).toBe('0.00%')
    expect(fmtPct(undefined)).toBe('—')
  })

  it('formats signed changes and compact volume', () => {
    expect(fmtSigned(2.5)).toBe('+2.50')
    expect(fmtSigned(-2.5)).toBe('-2.50')
    expect(fmtVolume(64_608_302)).toBe('64.6M')
    expect(fmtVolume(1_180_000_000)).toBe('1.2B')
  })

  it('uses the first two letters of the ticker for avatars', () => {
    expect(initials('NVDA')).toBe('NV')
    expect(initials('BRK.B')).toBe('BR')
  })
})

describe('labels', () => {
  it('maps level strength to Thai labels', () => {
    expect(strengthLabel(0.8).label).toBe('แข็ง')
    expect(strengthLabel(0.5).label).toBe('ปานกลาง')
    expect(strengthLabel(0.2).label).toBe('อ่อน')
  })

  it('labels the summary provider', () => {
    expect(providerLabel('gemini')).toBe('AI · Gemini')
    expect(providerLabel('openrouter')).toBe('AI · OpenRouter')
    expect(providerLabel('rules')).toBe('สรุปอัตโนมัติ')
  })
})

describe('market clock', () => {
  it('marks a weekday mid-session as open', () => {
    const clock = marketClock(new Date('2026-10-20T15:00:00Z')) // 11:00 ET
    expect(clock.isOpen).toBe(true)
    expect(clock.label).toBe('ตลาดเปิด')
    expect(clock.bangkokTime).toMatch(/^\d{2}:\d{2}$/)
  })

  it('marks weekends as closed', () => {
    expect(marketClock(new Date('2026-10-24T15:00:00Z')).isOpen).toBe(false)
  })
})
