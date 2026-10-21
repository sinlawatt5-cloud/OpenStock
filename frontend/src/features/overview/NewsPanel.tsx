import { useQuery } from '@tanstack/react-query'
import { ExternalLink, Newspaper, Sparkles } from 'lucide-react'
import { useMemo } from 'react'
import { SkeletonBlock } from '../../components/States'
import { apiGet } from '../../lib/api'
import { providerLabel, timeAgo } from '../../lib/format'
import type { NewsResponse, NewsSummary } from '../../lib/types'
import { useWatchlist } from '../../lib/watchlist'

export function NewsPanel() {
  const { symbols } = useWatchlist()
  const focus = useMemo(() => symbols.slice(0, 4).join(','), [symbols])

  const news = useQuery({
    queryKey: ['news', focus],
    queryFn: () => apiGet<NewsResponse>('/news', { limit: 8, symbols: focus || undefined }),
    staleTime: 5 * 60_000,
  })

  const summary = useQuery({
    queryKey: ['news-summary', focus],
    queryFn: () => apiGet<NewsSummary>('/news/summary', { symbols: focus || undefined }),
    staleTime: 10 * 60_000,
    retry: 0,
  })

  const items = news.data?.items ?? []
  const provider = summary.data ? providerLabel(summary.data.provider) : ''

  return (
    <div className="news-grid">
      <section className="summary-card" aria-label="สรุปข่าววันนี้">
        <div className="summary-top">
          <h2 className="card-title" style={{ fontSize: 15 }}>
            <Sparkles size={16} strokeWidth={2} aria-hidden="true" style={{ color: '#B7791F' }} />
            สรุปข่าววันนี้
          </h2>
          <span
            className="summary-badge"
            title={summary.data ? `โมเดล ${summary.data.model}` : 'กำลังประมวลผล'}
          >
            {summary.isPending ? 'กำลังสรุป…' : provider || 'สรุปอัตโนมัติ'}
          </span>
        </div>

        {summary.isPending ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }} aria-busy="true">
            <SkeletonBlock height={12} width="96%" />
            <SkeletonBlock height={12} width="88%" />
            <SkeletonBlock height={12} width="72%" />
          </div>
        ) : null}

        {summary.isError ? (
          <div>
            <p className="summary-text">สรุปข่าวยังไม่พร้อมใช้งาน — อ่านพาดหัวด้านขวาได้เลย</p>
            <button
              type="button"
              className="icon-btn"
              style={{ marginTop: 10 }}
              onClick={() => summary.refetch()}
            >
              ลองสรุปอีกครั้ง
            </button>
          </div>
        ) : null}

        {summary.data ? (
          <p className="summary-text">{summary.data.text}</p>
        ) : null}

        {summary.data?.sources?.length ? (
          <div className="summary-sources">
            <span style={{ fontSize: 10.5, color: '#9A7650', fontWeight: 600 }}>แหล่งข่าวที่ใช้สรุป</span>
            {summary.data.sources.slice(0, 3).map((source, index) => (
              <a
                key={`${source.title}-${index}`}
                className="summary-source"
                href={source.url ?? undefined}
                target="_blank"
                rel="noopener noreferrer"
              >
                <span>{source.source}</span>
                <span style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {source.title}
                </span>
              </a>
            ))}
          </div>
        ) : null}
      </section>

      <section className="card" aria-label="ข่าวและหุ้นที่ขยับ">
        <div className="card-head">
          <h2 className="card-title">
            <Newspaper size={16} strokeWidth={2} aria-hidden="true" />
            ข่าวและหุ้นที่ขยับ
          </h2>
          <span className="card-meta">{news.data ? `อัปเดต ${timeAgo(news.data.asOf)}` : ''}</span>
        </div>

        {news.isPending ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: '4px 16px 18px' }}>
            {[0, 1, 2, 3].map((row) => (
              <div key={row} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <SkeletonBlock height={12} width="92%" />
                <SkeletonBlock height={9} width="42%" />
              </div>
            ))}
          </div>
        ) : null}

        {news.isError ? (
          <p className="muted" style={{ padding: '8px 18px 18px', fontSize: 12.5 }}>
            โหลดข่าวไม่สำเร็จในขณะนี้ — ลองรีเฟรชอีกครั้ง
          </p>
        ) : null}

        {!news.isPending && !news.isError && items.length === 0 ? (
          <p className="muted" style={{ padding: '8px 18px 18px', fontSize: 12.5 }}>
            ยังไม่มีพาดหัวข่าวจากแหล่งข้อมูลฟรีในขณะนี้
          </p>
        ) : null}

        <div className="news-list">
          {items.map((item, index) => (
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
                  {item.publishedAt ? (
                    <>
                      <span aria-hidden="true">·</span>
                      <span>{timeAgo(item.publishedAt)}</span>
                    </>
                  ) : null}
                  {item.tickers.slice(0, 2).map((ticker) => (
                    <span className="ticker-tag" key={ticker}>
                      {ticker}
                    </span>
                  ))}
                </div>
              </a>
              <ExternalLink size={13} className="faint" aria-hidden="true" style={{ marginTop: 3 }} />
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}
