import { Activity } from 'lucide-react'
import { SkeletonBlock } from '../../components/States'
import type { Breadth, SpyTrend } from '../../lib/types'

type Props = {
  breadth: Breadth | null
  spy: SpyTrend | null
  loading: boolean
}

export function BreadthRibbon({ breadth, spy, loading }: Props) {
  const pct = breadth ? Math.max(0, Math.min(100, breadth.pctAboveMa200)) : 0
  const title = spy
    ? `SPY ${spy.aboveMa200 ? 'เหนือ' : 'ต่ำกว่า'} MA200 ${Math.abs(spy.vsMa200Pct).toFixed(2)}%`
    : 'ความกว้างของตลาด'
  const subtitle = breadth
    ? `หุ้นขนาดใหญ่ ${breadth.above}/${breadth.universeSize} ตัวยืนเหนือเส้นค่าเฉลี่ย 200 วัน`
    : 'กำลังคำนวณจำนวนหุ้นที่ยืนเหนือ MA200'

  return (
    <section className="breadth" aria-label="ความกว้างของตลาด">
      <span className="breadth-icon" aria-hidden="true">
        <Activity size={17} strokeWidth={2} />
      </span>
      <div>
        <h2 className="breadth-title">{title}</h2>
        <p className="breadth-sub">{subtitle}</p>
      </div>
      <div className="breadth-meter">
        {loading || !breadth ? (
          <SkeletonBlock height={8} radius={999} />
        ) : (
          <>
            <div
              className="breadth-track"
              role="meter"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={pct}
              aria-label="เปอร์เซ็นต์หุ้นที่ยืนเหนือ MA200"
            >
              <div className="breadth-fill" style={{ width: `${pct}%` }} />
            </div>
            <div className="breadth-legend">
              <span>{pct}% เหนือ MA200</span>
              <span>100%</span>
            </div>
          </>
        )}
      </div>
    </section>
  )
}
