import { Check, CircleAlert, Minus } from 'lucide-react'
import type { RiskSignal, RiskOnSummary } from '../../lib/types'

const STATUS_META = {
  positive: { icon: Check, className: 'risk-signal--up', text: 'ผ่าน' },
  negative: { icon: Minus, className: 'risk-signal--down', text: 'ไม่ผ่าน' },
  unavailable: { icon: CircleAlert, className: 'risk-signal--na', text: 'ข้อมูลไม่พร้อม' },
} as const

export function RiskOnPanel({ riskOn }: { riskOn: RiskOnSummary }) {
  return (
    <section className="card risk-panel" aria-label="สัญญาณ risk-on 6 ข้อ">
      <div className="risk-panel-head">
        <div>
          <h2 className="risk-panel-title">ภาวะเสี่ยง (Risk-On)</h2>
          <p className="risk-panel-sub">ประเมินจากผลตอบแทน ETF ในช่วงเวลาที่เลือก</p>
        </div>
        <div className="risk-score" aria-label={`คะแนน ${riskOn.score} จาก 6 สัญญาณ`}>
          <strong>{riskOn.score}/{riskOn.of}</strong>
          <span>สัญญาณ</span>
        </div>
      </div>

      <ul className="risk-signals">
        {riskOn.signals.map((signal: RiskSignal) => {
          const meta = STATUS_META[signal.status]
          const Icon = meta.icon
          return (
            <li key={signal.id} className={`risk-signal ${meta.className}`}>
              <span className={`risk-signal-icon ${meta.className}`}>
                <Icon size={13} strokeWidth={2.4} aria-hidden="true" />
              </span>
              <div className="risk-signal-body">
                <strong>{signal.label}</strong>
                <p>{signal.description}</p>
              </div>
              <span className="risk-signal-status">{meta.text}</span>
            </li>
          )
        })}
      </ul>

      <p className="risk-note">
        แผงนี้ประเมินภาวะเสี่ยงจาก <strong>การเคลื่อนไหวของราคา ETF</strong> เท่านั้น ไม่ใช่ยอดเงินไหลเข้า/ออกกองทุนจริง
        และไม่ใช่คำแนะนำลงทุน · สัญญาณที่ข้อมูลไม่พร้อมจะไม่ถูกนับเป็นผ่าน
      </p>
    </section>
  )
}
