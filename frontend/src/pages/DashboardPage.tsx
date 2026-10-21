import { useIsFetching, useQuery, useQueryClient } from '@tanstack/react-query'
import { RefreshCw } from 'lucide-react'
import { ErrorState, StaleBadge } from '../components/States'
import { BreadthRibbon } from '../features/overview/BreadthRibbon'
import { IndexStrip } from '../features/overview/IndexStrip'
import { MoversBoard } from '../features/overview/MoversBoard'
import { NewsPanel } from '../features/overview/NewsPanel'
import { apiGet } from '../lib/api'
import { fmtThaiDate, fmtThaiTime } from '../lib/format'
import type { Overview } from '../lib/types'
import { useDocumentTitle } from '../lib/useDocumentTitle'

export function DashboardPage() {
  useDocumentTitle('ภาพรวมตลาด')
  const queryClient = useQueryClient()
  const fetching = useIsFetching()

  const overview = useQuery({
    queryKey: ['overview'],
    queryFn: () => apiGet<Overview>('/market/overview'),
  })

  const asOf = overview.data?.asOf
  const updated = asOf ? `${fmtThaiTime(asOf)} น.` : '—'

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">ภาพรวมตลาดสหรัฐ</h1>
          <div className="page-sub">
            <span>{fmtThaiDate(new Date().toISOString())}</span>
            <span className="faint" aria-hidden="true">·</span>
            <span>อัปเดตล่าสุด {updated}</span>
            <StaleBadge stale={overview.data?.stale} ageSeconds={overview.data?.ageSeconds} />
          </div>
        </div>
        <div className="head-tools">
          <button
            type="button"
            className="icon-btn"
            onClick={() => queryClient.invalidateQueries()}
            disabled={fetching > 0}
          >
            <RefreshCw
              size={14}
              className={fetching > 0 ? 'spin' : undefined}
              aria-hidden="true"
            />
            {fetching > 0 ? 'กำลังอัปเดต' : 'รีเฟรช'}
          </button>
        </div>
      </div>

      {overview.isError ? (
        <ErrorState message={overview.error.message} onRetry={() => overview.refetch()} />
      ) : (
        <>
          <IndexStrip data={overview.data} loading={overview.isPending} />
          <BreadthRibbon
            breadth={overview.data?.breadth ?? null}
            spy={overview.data?.spy ?? null}
            loading={overview.isPending}
          />
        </>
      )}

      <div className="board-grid">
        <MoversBoard list="gainers" />
        <MoversBoard list="losers" />
        <MoversBoard list="actives" />
      </div>

      <NewsPanel />

      <p className="muted" style={{ fontSize: 11.5, padding: '2px 4px', lineHeight: 1.6 }}>
        ราคาอ้างอิงผู้ให้บริการฟรีและอาจล่าช้า · มูลค่าซื้อขายแสดงเฉพาะหุ้นที่คึกคัก ·
        ตัวเลขทั้งหมดเป็นข้อมูลเพื่อการศึกษา ไม่ใช่คำแนะนำการลงทุน
      </p>
    </div>
  )
}
