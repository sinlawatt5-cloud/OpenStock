import { useQuery } from '@tanstack/react-query'
import { ChevronLeft, ExternalLink, Info, Star, Target } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Avatar } from '../components/Avatar'
import { Delta } from '../components/Delta'
import { ErrorState, SkeletonBlock, StaleBadge } from '../components/States'
import { PriceChart } from '../features/symbol/PriceChart'
import { apiGet } from '../lib/api'
import {
  fmtInt,
  fmtMoneyCompact,
  fmtPct,
  fmtPrice,
  fmtThaiTime,
  fmtVolume,
  strengthLabel,
  timeAgo,
} from '../lib/format'
import type {
  HistoryResponse,
  LevelsResponse,
  NewsResponse,
  SymbolPageResponse,
} from '../lib/types'
import { useDocumentTitle } from '../lib/useDocumentTitle'
import { useWatchlist } from '../lib/watchlist'

const RANGES = [
  { key: '1d', label: '1D' },
  { key: '5d', label: '5D' },
  { key: '1mo', label: '1M' },
  { key: '6mo', label: '6M' },
  { key: '1y', label: '1Y' },
  { key: '5y', label: '5Y' },
]

export function SymbolPage() {
  const params = useParams()
  const symbol = (params.symbol ?? '').toUpperCase()
  useDocumentTitle(symbol || 'หุ้นรายตัว')

  const [range, setRange] = useState('6mo')
  const [showLevels, setShowLevels] = useState(true)
  const [method, setMethod] = useState<'structure' | 'pivot'>('structure')
  const [expanded, setExpanded] = useState(false)
  const watchlist = useWatchlist()

  const page = useQuery({
    queryKey: ['symbol-page', symbol],
    queryFn: () => apiGet<SymbolPageResponse>(`/symbol/${symbol}/profile`),
    enabled: symbol.length > 0,
  })

  const history = useQuery({
    queryKey: ['history', symbol, range],
    queryFn: () => apiGet<HistoryResponse>(`/history/${symbol}`, { range }),
    enabled: symbol.length > 0,
  })

  const levels = useQuery({
    queryKey: ['levels', symbol, range, method],
    queryFn: () => apiGet<LevelsResponse>(`/symbol/${symbol}/levels`, { range, method }),
    enabled: symbol.length > 0 && showLevels,
  })

  const news = useQuery({
    queryKey: ['news', symbol],
    queryFn: () => apiGet<NewsResponse>('/news', { symbols: symbol, limit: 6, scope: 'company' }),
    enabled: symbol.length > 0,
    staleTime: 5 * 60_000,
  })

  const intraday = range === '1d' || range === '5d'

  if (!symbol) {
    return <ErrorState message="ไม่พบ ticker ในที่อยู่หน้านี้" />
  }

  if (page.isError) {
    return (
      <div className="page">
        <Link to="/" className="back-link">
          <ChevronLeft size={14} aria-hidden="true" /> กลับภาพรวมตลาด
        </Link>
        <ErrorState message={page.error.message} onRetry={() => page.refetch()} />
      </div>
    )
  }

  const quote = page.data?.quote
  const profile = page.data?.profile
  const name = profile?.nameTh || profile?.name || quote?.nameTh || quote?.name || symbol
  const followed = watchlist.has(symbol)
  const stats = [
    { label: 'มูลค่าตลาด', value: fmtMoneyCompact(profile?.marketCap) },
    { label: 'P/E (TTM)', value: fmtPrice(profile?.peTrailing) },
    { label: 'P/E ล่วงหน้า', value: fmtPrice(profile?.peForward) },
    {
      label: 'ช่วง 52 สัปดาห์',
      value:
        profile?.week52Low && profile?.week52High
          ? `${fmtPrice(profile.week52Low, 0)}–${fmtPrice(profile.week52High, 0)}`
          : '—',
    },
    { label: 'ปริมาณเฉลี่ย', value: fmtVolume(profile?.avgVolume) },
    {
      label: 'อัตราปันผล',
      value: profile?.dividendYield ? fmtPct(profile.dividendYield) : '—',
    },
    { label: 'Beta', value: fmtPrice(profile?.beta) },
    { label: 'พนักงาน', value: fmtInt(profile?.employees) },
  ]

  return (
    <div className="page">
      <div>
        <Link to="/" className="back-link">
          <ChevronLeft size={14} aria-hidden="true" /> กลับภาพรวมตลาด
        </Link>
      </div>

      <section className="card card-pad symbol-head" aria-label={`ข้อมูล ${symbol}`}>
        <Avatar symbol={symbol} name={name} logo={profile?.logo} className="avatar symbol-avatar" />
        <div style={{ minWidth: 0, flex: 1 }}>
          <h1 className="symbol-name">{name}</h1>
          <div className="symbol-meta">
            <span className="num" style={{ fontWeight: 600, color: 'var(--ink-muted)' }}>
              {symbol}
            </span>
            {profile?.exchange ? <span>{profile.exchange}</span> : null}
            {profile?.sector ? <span>{profile.sector}</span> : null}
            {profile?.industry ? <span className="faint">{profile.industry}</span> : null}
            {quote ? <StaleBadge stale={quote.stale} ageSeconds={quote.ageSeconds} /> : null}
          </div>
        </div>

        <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
          {page.isPending ? (
            <SkeletonBlock height={40} width={150} />
          ) : (
            <>
              <div className="price-block" style={{ justifyContent: 'flex-end' }}>
                <span className="price-big">{fmtPrice(quote?.price)}</span>
                <Delta value={quote?.changePct} />
                <span className="faint" style={{ fontSize: 11 }}>
                  USD
                </span>
              </div>
              <p className="faint" style={{ fontSize: 11, marginTop: 5 }}>
                อัปเดต {fmtThaiTime(quote?.asOf)} น. · อ้างอิงผู้ให้บริการฟรี
              </p>
            </>
          )}
        </div>

        <button
          type="button"
          className="icon-btn"
          aria-pressed={followed}
          onClick={() => watchlist.toggle(symbol)}
          style={followed ? { borderColor: '#f0c9a1', background: 'var(--surface-warm)', color: 'var(--ink)' } : undefined}
        >
          <Star size={14} fill={followed ? 'currentColor' : 'none'} aria-hidden="true" />
          {followed ? 'ติดตามแล้ว' : 'เพิ่มใน Watchlist'}
        </button>
      </section>

      <div className="symbol-layout">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <section className="card chart-card" aria-label="กราฟราคาและแนวรับแนวต้าน">
            <div className="chart-toolbar">
              <div className="segmented" role="group" aria-label="ช่วงเวลากราฟ">
                {RANGES.map((item) => (
                  <button
                    key={item.key}
                    type="button"
                    className={range === item.key ? 'active' : ''}
                    aria-pressed={range === item.key}
                    onClick={() => setRange(item.key)}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={showLevels}
                    onChange={(event) => setShowLevels(event.target.checked)}
                  />
                  แนวรับ/แนวต้าน
                </label>
                {showLevels ? (
                  <div className="chip-row">
                    <button
                      type="button"
                      className={`chip${method === 'structure' ? ' active' : ''}`}
                      aria-pressed={method === 'structure'}
                      onClick={() => setMethod('structure')}
                      style={{ minHeight: 32, fontSize: 11.5, padding: '0 10px' }}
                    >
                      โครงสร้างราคา
                    </button>
                    <button
                      type="button"
                      className={`chip${method === 'pivot' ? ' active' : ''}`}
                      aria-pressed={method === 'pivot'}
                      onClick={() => setMethod('pivot')}
                      style={{ minHeight: 32, fontSize: 11.5, padding: '0 10px' }}
                    >
                      Pivot
                    </button>
                  </div>
                ) : null}
              </div>
            </div>

            {history.isError ? (
              <ErrorState message={history.error.message} onRetry={() => history.refetch()} compact />
            ) : (
              <PriceChart
                bars={history.data?.bars ?? []}
                levels={levels.data}
                showLevels={showLevels}
                intraday={intraday}
                loading={history.isPending}
              />
            )}

            <div className="chart-legend">
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <span className="legend-swatch up" aria-hidden="true" /> แนวรับ
              </span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <span className="legend-swatch" aria-hidden="true" /> แนวต้าน
              </span>
              <span>
                วิธี: {method === 'structure' ? 'จุดกลับตัวของราคา (swing pivots)' : 'Pivot คลาสสิกจากแท่งก่อนหน้า'}
              </span>
              {levels.data?.fallback ? <span className="faint">· บางเส้นใช้ค่าสำรอง</span> : null}
            </div>
          </section>

          <section className="card" aria-label="สถิติสำคัญ">
            <div className="card-head">
              <h2 className="card-title">
                <Info size={16} strokeWidth={1.9} aria-hidden="true" />
                สถิติสำคัญ
              </h2>
              <span className="card-meta">{timeAgo(profile?.asOf)}</span>
            </div>
            <div style={{ padding: '0 16px 16px' }}>
              {page.isPending ? (
                <div className="stats-grid">
                  {Array.from({ length: 8 }).map((_, index) => (
                    <div key={index} className="stat">
                      <SkeletonBlock height={9} width="60%" />
                      <div style={{ height: 8 }} />
                      <SkeletonBlock height={13} width="75%" />
                    </div>
                  ))}
                </div>
              ) : (
                <dl className="stats-grid" style={{ margin: 0 }}>
                  {stats.map((stat) => (
                    <div className="stat" key={stat.label}>
                      <dt>{stat.label}</dt>
                      <dd>{stat.value}</dd>
                    </div>
                  ))}
                </dl>
              )}
            </div>
          </section>

          <section className="card card-pad" aria-label="เกี่ยวกับบริษัทและหุ้นใกล้เคียง">
            <h2 className="card-title" style={{ fontSize: 14 }}>
              เกี่ยวกับบริษัท
            </h2>
            <p className={`about-text${expanded ? '' : ' clamped'}`} style={{ marginTop: 8 }}>
              {profile?.summary ||
                'ยังไม่มีคำอธิบายบริษัทจากแหล่งข้อมูลฟรีในขณะนี้ — ดูรายละเอียดเพิ่มเติมได้จากเว็บไซต์บริษัท'}
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginTop: 8, flexWrap: 'wrap' }}>
              {profile?.summary ? (
                <button
                  type="button"
                  className="link-more"
                  onClick={() => setExpanded((value) => !value)}
                  aria-expanded={expanded}
                  style={{ paddingLeft: 0 }}
                >
                  {expanded ? 'ย่อข้อความ' : 'อ่านต่อ'}
                </button>
              ) : null}
              {profile?.website ? (
                <a
                  className="link-more"
                  href={profile.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ paddingLeft: 0 }}
                >
                  เว็บไซต์บริษัท <ExternalLink size={12} aria-hidden="true" />
                </a>
              ) : null}
            </div>

            {page.data?.peers?.length ? (
              <div style={{ marginTop: 16 }}>
                <h3 style={{ fontSize: 12.5, color: 'var(--ink-muted)', marginBottom: 8 }}>
                  หุ้นในกลุ่มเดียวกัน
                </h3>
                <div className="peer-row">
                  {page.data.peers.map((peer) => (
                    <Link key={peer.symbol} to={`/symbol/${peer.symbol}`} className="peer-chip">
                      <strong>{peer.symbol}</strong>
                      <span className="muted">{peer.nameTh || peer.name}</span>
                    </Link>
                  ))}
                </div>
              </div>
            ) : null}
          </section>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <section className="card" aria-label="แนวรับและแนวต้าน">
            <div className="card-head">
              <h2 className="card-title">
                <Target size={16} strokeWidth={1.9} aria-hidden="true" />
                แนวรับ / แนวต้าน
              </h2>
              <span className="card-meta">
                {levels.data?.atr ? `ATR ${fmtPrice(levels.data.atr)}` : '2 + 2 ระดับ'}
              </span>
            </div>

            {!showLevels ? (
              <p className="muted" style={{ padding: '0 16px 16px', fontSize: 12 }}>
                เปิดสวิตช์ “แนวรับ/แนวต้าน” บนกราฟเพื่อแสดงเส้นระดับราคา
              </p>
            ) : null}

            {showLevels && levels.isPending ? (
              <div className="levels-grid">
                {Array.from({ length: 4 }).map((_, index) => (
                  <SkeletonBlock key={index} height={66} radius={13} />
                ))}
              </div>
            ) : null}

            {showLevels && levels.isError ? (
              <p className="muted" style={{ padding: '0 16px 16px', fontSize: 12 }}>
                คำนวณแนวรับ/แนวต้านไม่สำเร็จ — ลองเปลี่ยนช่วงเวลาหรือกดรีเฟรช
              </p>
            ) : null}

            {showLevels && levels.data ? (
              <div className="levels-grid">
                {[...levels.data.supports, ...levels.data.resistances].map((level, index) => {
                  const isResistance = index >= levels.data!.supports.length
                  const rank = isResistance
                    ? index - levels.data!.supports.length + 1
                    : index + 1
                  const strength = strengthLabel(level.strength)
                  return (
                    <div key={`${isResistance}-${level.price}`} className={`level-card${isResistance ? ' res' : ''}`}>
                      <div className="level-head">
                        <span>
                          {isResistance ? 'แนวต้าน' : 'แนวรับ'} {rank}
                        </span>
                        <span className={`strength strength--${strength.tone}`}>{strength.label}</span>
                      </div>
                      <div className="level-price">{fmtPrice(level.price)}</div>
                      <div className="level-sub">
                        <span>{fmtPct(level.distancePct)}</span>
                        <span>แตะ {level.touches} ครั้ง</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : null}

            <p className="flow-note" style={{ padding: '0 16px 16px' }}>
              คำนวณจากจุดกลับตัวและความหนาแน่นของการแตะในอดีต (±0.3 ATR) ·
              ใช้ประกอบการอ่านกราฟเท่านั้น ไม่ใช่คำแนะนำการลงทุน
            </p>
          </section>

          <section className="card" aria-label="ข่าวที่เกี่ยวข้อง">
            <div className="card-head">
              <h2 className="card-title" style={{ fontSize: 14 }}>
                ข่าวที่เกี่ยวข้อง
              </h2>
              <span className="card-meta">{news.data ? timeAgo(news.data.asOf) : ''}</span>
            </div>
            <div className="news-list">
              {news.isPending
                ? [0, 1, 2].map((row) => (
                    <div key={row} style={{ padding: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
                      <SkeletonBlock height={11} width="94%" />
                      <SkeletonBlock height={9} width="46%" />
                    </div>
                  ))
                : null}
              {(news.data?.items ?? []).slice(0, 6).map((item, index) => (
                <article className="news-item" key={`${item.title}-${index}`}>
                  <a
                    href={item.url ?? undefined}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ minWidth: 0 }}
                  >
                    <h3 className="news-title">{item.title}</h3>
                    <div className="news-meta">
                      <span>{item.source}</span>
                      <span aria-hidden="true">·</span>
                      <span>{timeAgo(item.publishedAt)}</span>
                    </div>
                  </a>
                </article>
              ))}
              {!news.isPending && (news.data?.items?.length ?? 0) === 0 ? (
                <p className="muted" style={{ padding: 14, fontSize: 12 }}>
                  ยังไม่มีข่าวของหุ้นตัวนี้จากแหล่งข้อมูลฟรี
                </p>
              ) : null}
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
