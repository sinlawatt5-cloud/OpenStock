import { useQuery } from '@tanstack/react-query'
import { Flame, TrendingDown, TrendingUp } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Avatar } from '../../components/Avatar'
import { Delta } from '../../components/Delta'
import { ErrorState, RowsSkeleton } from '../../components/States'
import { apiGet } from '../../lib/api'
import { fmtPrice, fmtThaiTime, fmtVolume } from '../../lib/format'
import type { MoversResponse } from '../../lib/types'

type ListKey = 'gainers' | 'losers' | 'actives'

const CONFIG = {
  gainers: {
    title: 'อันดับขึ้น',
    icon: TrendingUp,
    color: 'var(--up)',
    empty: 'ยังไม่มีหุ้นที่ปรับขึ้นแรงในรอบนี้',
  },
  losers: {
    title: 'อันดับลง',
    icon: TrendingDown,
    color: 'var(--down)',
    empty: 'ยังไม่มีหุ้นที่ปรับลงแรงในรอบนี้',
  },
  actives: {
    title: 'ซื้อขายคึกคัก',
    icon: Flame,
    color: 'var(--sun-1)',
    empty: 'ยังไม่มีข้อมูลปริมาณซื้อขาย',
  },
} as const

export function MoversBoard({ list }: { list: ListKey }) {
  const config = CONFIG[list]
  const Icon = config.icon
  const query = useQuery({
    queryKey: ['movers', list],
    queryFn: () => apiGet<MoversResponse>('/market/movers', { list, limit: 5 }),
  })

  return (
    <section className="card board" aria-label={config.title}>
      <div className="card-head">
        <h2 className="card-title">
          <Icon size={16} strokeWidth={2} aria-hidden="true" style={{ color: config.color }} />
          {config.title}
        </h2>
        <span className="card-meta">
          {query.data ? `อัปเดต ${fmtThaiTime(query.data.asOf)} น.` : '5 อันดับ'}
        </span>
      </div>

      {query.isPending ? <RowsSkeleton rows={5} /> : null}

      {query.isError ? (
        <div style={{ padding: 12 }}>
          <ErrorState message={query.error.message} onRetry={() => query.refetch()} compact />
        </div>
      ) : null}

      {query.data && query.data.rows.length === 0 ? (
        <p className="muted" style={{ padding: '10px 18px 18px', fontSize: 12.5 }}>
          {config.empty}
        </p>
      ) : null}

      {query.data && query.data.rows.length > 0 ? (
        <div className="board-list">
          {query.data.rows.slice(0, 5).map((row, index) => (
            <Link key={row.symbol} to={`/symbol/${row.symbol}`} className="board-row">
              <span className="rank">{index + 1}</span>
              <Avatar symbol={row.symbol} name={row.name} logo={row.logo} />
              <span className="board-sym">
                <span className="sym">{row.symbol}</span>
                <span className="sym-name" title={row.name}>
                  {row.name}
                </span>
              </span>
              <span className="row-price">
                {fmtPrice(row.price)}
                {list === 'actives' ? <small>{fmtVolume(row.volume)} หุ้น</small> : null}
              </span>
              <Delta value={row.changePct} showIcon={false} />
            </Link>
          ))}
        </div>
      ) : null}
    </section>
  )
}
