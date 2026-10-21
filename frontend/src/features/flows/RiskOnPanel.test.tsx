// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import type { RiskOnSummary } from '../../lib/types'
import { RiskOnPanel } from './RiskOnPanel'

afterEach(cleanup)

function summaryFixture(overrides: Partial<RiskOnSummary> = {}): RiskOnSummary {
  return {
    score: 4,
    of: 6,
    signals: [
      { id: 'small_caps_lead', label: 'หุ้นเล็กนำตลาด', description: 'IWM เหนือ SPY', formula: 'return(IWM) - return(SPY)', status: 'positive', values: { IWM: 2, SPY: 1 } },
      { id: 'equal_weight_wins', label: 'หุ้นถ่วงน้ำหนักเท่ากันชนะตลาดรวม', description: 'RSP เหนือ SPY', formula: 'return(RSP) - return(SPY)', status: 'positive', values: { RSP: 2, SPY: 1 } },
      { id: 'junk_beats_ig', label: 'เครดิตเสี่ยงชนะเครดิตเกรดลงทุน', description: 'HYG เหนือ LQD', formula: 'return(HYG) - return(LQD)', status: 'negative', values: { HYG: 0.5, LQD: 1 } },
      { id: 'em_wins', label: 'ตลาดเกิดใหม่ชนะตลาดรวม', description: 'EEM เหนือ SPY', formula: 'return(EEM) - return(SPY)', status: 'positive', values: { EEM: 2, SPY: 1 } },
      { id: 'dollar_weak', label: 'ดอลลาร์อ่อนค่า', description: 'UUP ติดลบ', formula: 'return(UUP)', status: 'unavailable', values: null },
      { id: 'gold_loses', label: 'ทองคำแพ้ตลาดรวม', description: 'GLD แย่กว่า SPY', formula: 'return(GLD) - return(SPY)', status: 'positive', values: { GLD: 0.5, SPY: 1 } },
    ],
    ...overrides,
  }
}

describe('RiskOnPanel', () => {
  it('shows the n/6 score prominently', () => {
    render(<RiskOnPanel riskOn={summaryFixture()} />)
    expect(screen.getByText('4/6')).toBeTruthy()
  })

  it('lists all six signal labels', () => {
    render(<RiskOnPanel riskOn={summaryFixture()} />)
    expect(screen.getByText('หุ้นเล็กนำตลาด')).toBeTruthy()
    expect(screen.getByText('ดอลลาร์อ่อนค่า')).toBeTruthy()
    expect(screen.getByText('ทองคำแพ้ตลาดรวม')).toBeTruthy()
  })

  it('marks unavailable signals instead of guessing pass/fail', () => {
    render(<RiskOnPanel riskOn={summaryFixture()} />)
    const unavailableCount = screen.getAllByText('ข้อมูลไม่พร้อม').length
    expect(unavailableCount).toBe(1)
  })

  it('discloses the price-proxy limitation', () => {
    render(<RiskOnPanel riskOn={summaryFixture()} />)
    expect(screen.getByText(/ไม่ใช่ยอดเงินไหลเข้า\/ออกกองทุนจริง/)).toBeTruthy()
  })

  it('renders a zero score', () => {
    const signals = summaryFixture().signals.map((s) => ({ ...s, status: s.status === 'positive' ? 'negative' : s.status }))
    render(<RiskOnPanel riskOn={summaryFixture({ score: 0, signals })} />)
    expect(screen.getByText('0/6')).toBeTruthy()
  })
})
