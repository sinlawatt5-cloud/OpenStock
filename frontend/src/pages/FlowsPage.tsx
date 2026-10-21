import { useQuery, useQueryClient } from '@tanstack/react-query'
import type { LucideIcon } from 'lucide-react'
import {
  Factory,
  Globe2,
  Info,
  Layers,
  RefreshCw,
  Sparkles,
  TrendingDown,
  TrendingUp,
} from 'lucide-react'
import type { CSSProperties } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ErrorState, SkeletonBlock, StaleBadge } from '../components/States'
import { apiGet } from '../lib/api'
import { fmtPct, fmtThaiTime, fmtVolume } from '../lib/format'
import type { Catalog, FlowRow, FlowsResponse } from '../lib/types'
import { useDocumentTitle } from '../lib/useDocumentTitle'

const GROUP_ICONS: Record<string, LucideIcon> = {
  broad: Globe2,
  sectors: Factory,
  industries: Layers,
  themes: Sparkles,
  all: Info,
}

const MODES = [
  { key: 'all', label: 'ทั้งหมด' },
  { key: 'inflow', label: 'ไหลเข้า' },
  { key: 'outflow', label: 'ไหลออก' },
]

export function FlowsPage() {
  useDocumentTitle('กระแสเงิน')
  const queryClient = useQueryClient()
  const [params, setParams] = useSearchParams()
  const group = params.get('group') ?? 'sectors'
  const range = params.get('range') ?? '1d'
  const mode = params.get('mode') ?? 'all'

  const setParam = (key: string, value: string) => {
    const next = new URLSearchParams(params)
    next.set(key, value)
    setParams(next, { replace: true })
  }

  const catalog = useQuery({
    queryKey: ['catalog'],
    queryFn: () => apiGet<Catalog>('/catalog'),
    staleTime: 60 * 60_000,
  })

  const flows = useQuery({
    queryKey: ['flows', group, range, mode],
    queryFn: () => apiGet<FlowsResponse>('/flows', { group, range, mode }),
  })

  const summary = flows.data?.summary
  const netPositive = (summary?.inflow ?? 0) >= (summary?.outflow ?? 0)
  const SummaryIcon = netPositive ? TrendingUp : TrendingDown
  const rows = flows.data?.rows ?? []

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">กระแสเงินตามกลุ่ม</h1>
          <div className="page-sub">
            <span>เทียบเปอร์เซ็นต์การเคลื่อนไหวของ ETF ตัวแทนแต่ละกลุ่ม</span>
            {flows.data ? (
              <>
                <span className="faint" aria-hidden="true">·</span>
                <span>อัปเดต {fmtThaiTime(flows.data.asOf)} น.</span>
                <StaleBadge stale={flows.data.stale} ageSeconds={flows.data.ageSeconds} />
              </>
            ) : null}
          </div>
        </div>
        <div className="head-tools">
          <button
            type="button"
            className="icon-btn"
            onClick={() => queryClient.invalidateQueries({ queryKey: ['flows'] })}
            disabled={flows.isFetching}
          >
            <RefreshCw size={14} className={flows.isFetching ? 'spin' : undefined} aria-hidden="true" />
            {flows.isFetching ? 'กำลังอัปเดต' : 'รีเฟรช'}
          </button>
        </div>
      </div>

      <section className="card card-pad" aria-label="ตัวกรองกระแสเงิน">
        <div className="filter-block" style={{ marginBottom: 12 }}>
          <span className="filter-label">มุมมอง</span>
          <div className="segmented" role="group" aria-label="เลือกมุมมอง">
            {MODES.map((item) => (
              <button
                key={item.key}
                type="button"
                className={mode === item.key ? 'active' : ''}
                aria-pressed={mode === item.key}
                onClick={() => setParam('mode', item.key)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        <div className="filter-block" style={{ marginBottom: 12 }}>
          <span className="filter-label">กลุ่ม</span>
          <div className="chip-row">
            {catalog.isPending
              ? [110, 92, 120, 110, 72].map((width, index) => (
                  <SkeletonBlock key={index} height={36} width={width} radius={999} />
                ))
              : null}
            {catalog.data?.groups.map((item) => {
              const Icon = GROUP_ICONS[item.key] ?? Layers
              return (
                <button
                  key={item.key}
                  type="button"
                  className={`chip${group === item.key ? ' active' : ''}`}
                  aria-pressed={group === item.key}
                  onClick={() => setParam('group', item.key)}
                >
                  <Icon size={13} strokeWidth={1.9} aria-hidden="true" />
                  {item.label}
                </button>
              )
            })}
            <button
              type="button"
              className={`chip${group === 'all' ? ' active' : ''}`}
              aria-pressed={group === 'all'}
              onClick={() => setParam('group', 'all')}
            >
              <Layers size={13} strokeWidth={1.9} aria-hidden="true" />
              ทั้งหมด
            </button>
          </div>
        </div>

        <div className="filter-block">
          <span className="filter-label">ช่วงเวลา</span>
          <div className="segmented" role="group" aria-label="เลือกช่วงเวลา">
            {(catalog.data?.ranges ?? []).map((item) => (
              <button
                key={item.key}
                type="button"
                className={range === item.key ? 'active' : ''}
                aria-pressed={range === item.key}
                onClick={() => setParam('range', item.key)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="card flow-panel" aria-label="อันดับกระแสเงินตามกลุ่ม">
        {flows.data ? <p className="flow-desc">{flows.data.description}</p> : null}

        {flows.isPending ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '4px 2px' }} aria-busy="true">
            {Array.from({ length: 9 }).map((_, index) => (
              <div key={index} style={{ display: 'grid', gridTemplateColumns: '190px 1fr 64px', gap: 12, alignItems: 'center' }}>
                <SkeletonBlock height={12} width={`${55 + (index % 4) * 10}%`} />
                <SkeletonBlock height={18} radius={999} />
                <SkeletonBlock height={12} width={48} />
              </div>
            ))}
          </div>
        ) : null}

        {flows.isError ? (
          <ErrorState message={flows.error.message} onRetry={() => flows.refetch()} />
        ) : null}

        {summary ? (
          <div className="flow-summary">
            <SummaryIcon size={16} strokeWidth={2.1} aria-hidden="true" />
            <span>
              {netPositive ? 'แรงซื้อ' : 'แรงขาย'} {netPositive ? summary.inflow : summary.outflow}/
              {summary.total} กลุ่ม · {summary.label}
            </span>
            <em>· ประมาณการจากราคาและมูลค่าซื้อขาย</em>
          </div>
        ) : null}

        {!flows.isPending && !flows.isError && rows.length === 0 ? (
          <p className="muted" style={{ padding: '14px 4px', fontSize: 13 }}>
            ไม่มีกลุ่มที่ตรงกับตัวกรองนี้ — ลองเปลี่ยนมุมมองหรือช่วงเวลา
          </p>
        ) : null}

        <div className="flow-list">
          {rows.map((row, index) => (
            <FlowBar key={row.symbol} row={row} index={index} />
          ))}
        </div>

        <p className="flow-note">
          แต่ละแท่งคือ % เปลี่ยนแปลงของ ETF ตัวแทนกลุ่มนั้น ไม่ใช่ตัวเลขเงินเข้าออกจริง ·
          มูลค่าซื้อขายคำนวณจากราคาปิด × ปริมาณซื้อขายล่าสุด · แถวเส้นประคือ S&P 500 ที่ใช้เป็น benchmark
          {catalog.data ? ` · ${catalog.data.disclaimer}` : ''}
        </p>
      </section>
    </div>
  )
}

function FlowBar({ row, index }: { row: FlowRow; index: number }) {
  const positive = row.pct >= 0
  const width = Math.max(2, Math.min(100, row.flowScore))
  const delay = `${Math.min(index, 14) * 16}ms`
  const style = { '--delay': delay } as CSSProperties

  return (
    <div
      className={`flow-row${row.benchmark ? ' flow-row--bench' : ''}`}
      style={style}
      aria-label={`${row.nameTh} ${fmtPct(row.pct)}`}
    >
      <div className="flow-name">
        <strong>{row.nameTh}</strong>
        <span className="flow-ticker">{row.symbol}</span>
      </div>
      <div
        className="flow-track"
        title={`มูลค่าซื้อขาย ≈ $${fmtVolume(row.dollarVolume)} · ราคา ${row.price.toFixed(2)}`}
      >
        <div
          className={`flow-fill ${
            row.benchmark ? 'flow-fill--bench' : positive ? 'flow-fill--up' : 'flow-fill--down'
          }`}
          style={{ width: `${width}%`, '--delay': delay } as CSSProperties}
        />
      </div>
      <div className={`flow-pct ${positive ? 'up' : 'down'}`}>{fmtPct(row.pct)}</div>
    </div>
  )
}
