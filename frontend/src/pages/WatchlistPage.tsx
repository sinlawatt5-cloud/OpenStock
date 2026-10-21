import { useQueries, useQuery } from '@tanstack/react-query'
import { ArrowRight, Plus, Search, Star, Trash2, X } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Avatar } from '../components/Avatar'
import { Delta } from '../components/Delta'
import { SkeletonBlock } from '../components/States'
import { Sparkline } from '../components/Sparkline'
import { apiGet } from '../lib/api'
import { fmtPrice, timeAgo } from '../lib/format'
import type { HistoryResponse, SearchResponse, SymbolItem } from '../lib/types'
import { useDebounced } from '../lib/useDebounced'
import { useDocumentTitle } from '../lib/useDocumentTitle'
import { WATCHLIST_MAX, useWatchlist } from '../lib/watchlist'

export function WatchlistPage() {
  useDocumentTitle('Watchlist')
  const { symbols, add, remove, has } = useWatchlist()
  const [query, setQuery] = useState('')
  const [toast, setToast] = useState<string | null>(null)
  const debounced = useDebounced(query.trim(), 220)

  const popular = useQuery({
    queryKey: ['symbols', 'popular'],
    queryFn: () => apiGet<{ items: SymbolItem[] }>('/symbols', { limit: 30 }),
    staleTime: 10 * 60_000,
  })

  const search = useQuery({
    queryKey: ['search', debounced],
    queryFn: () => apiGet<SearchResponse>('/search', { q: debounced }),
    enabled: debounced.length >= 1,
    staleTime: 5 * 60_000,
  })

  const histories = useQueries({
    queries: symbols.map((symbol) => ({
      queryKey: ['history', symbol, '1mo'],
      queryFn: () => apiGet<HistoryResponse>(`/history/${symbol}`, { range: '1mo' }),
      staleTime: 5 * 60_000,
    })),
  })

  const notify = (message: string) => {
    setToast(message)
    window.setTimeout(() => setToast(null), 2200)
  }

  const addSymbol = (symbol: string) => {
    if (has(symbol)) {
      notify(`${symbol} อยู่ใน Watchlist แล้ว`)
      return
    }
    if (symbols.length >= WATCHLIST_MAX) {
      notify(`เพิ่มได้สูงสุด ${WATCHLIST_MAX} หุ้น`)
      return
    }
    add(symbol)
    setQuery('')
    notify(`เพิ่ม ${symbol} ใน Watchlist แล้ว`)
  }

  const suggestions = (popular.data?.items ?? []).filter((item) => !has(item.symbol))
  const results = (search.data?.results ?? []).slice(0, 5)
  const empty = symbols.length === 0

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">Watchlist ของคุณ</h1>
          <div className="page-sub">
            <span>
              ติดตาม {symbols.length}/{WATCHLIST_MAX} หุ้น · เก็บไว้ในเบราว์เซอร์นี้
            </span>
          </div>
        </div>
        <div className="head-tools">
          <div className="search-wrap">
            <label className="search-field">
              <Search size={15} strokeWidth={2} aria-hidden="true" className="faint" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') {
                    const first = results[0]?.symbol
                    if (first) addSymbol(first)
                    else if (/^[A-Za-z.]{1,6}$/.test(query.trim())) addSymbol(query.trim().toUpperCase())
                  }
                }}
                placeholder="เพิ่มหุ้น เช่น NVDA หรือ Apple"
                aria-label="ค้นหาเพื่อเพิ่มหุ้นใน Watchlist"
                autoComplete="off"
              />
              {query ? (
                <button type="button" className="remove-btn" onClick={() => setQuery('')} aria-label="ล้างคำค้นหา">
                  <X size={14} />
                </button>
              ) : null}
            </label>
            {debounced.length >= 1 ? (
              <div className="search-results" role="listbox" aria-label="ผลการค้นหาเพื่อเพิ่ม">
                {results.map((row) => (
                  <button
                    key={row.symbol}
                    type="button"
                    className="dialog-row"
                    onClick={() => addSymbol(row.symbol)}
                  >
                    <Avatar symbol={row.symbol} name={row.nameTh || row.name} />
                    <span style={{ minWidth: 0 }}>
                      <span className="sym">{row.symbol}</span>
                      <span className="sym-name">{row.nameTh || row.name}</span>
                    </span>
                    <Plus size={15} style={{ marginLeft: 'auto' }} aria-hidden="true" />
                  </button>
                ))}
                {!search.isFetching && results.length === 0 ? (
                  <p className="muted" style={{ padding: '10px 12px', fontSize: 12 }}>
                    ไม่พบหุ้น — กด Enter เพื่อเพิ่ม ticker ที่พิมพ์ไว้
                  </p>
                ) : null}
              </div>
            ) : null}
          </div>
        </div>
      </div>

      <div className="watch-grid">
        <section className="card" aria-label="รายการหุ้นที่ติดตาม">
          {empty ? (
            <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div className="empty-illustration" aria-hidden="true">
                <Star size={26} strokeWidth={1.6} />
              </div>
              <div>
                <h2 className="card-title" style={{ fontSize: 17 }}>
                  ยังไม่มีหุ้นที่ติดตาม
                </h2>
                <p className="muted" style={{ fontSize: 12.5, marginTop: 4 }}>
                  เลือกจากหุ้นยอดนิยมด้านขวา หรือค้นหาจากช่องด้านบน — Watchlist จะอยู่กับคุณหลังรีเฟรช
                </p>
              </div>
              <p className="muted" style={{ fontSize: 11.5 }}>
                เคล็ดลับ: กด ⌘K หรือ Ctrl+K เพื่อค้นหาและเปิดหน้าหุ้นได้ทุกเมื่อ
              </p>
            </div>
          ) : (
            <div style={{ padding: '14px 16px 8px' }}>
              <table className="watch-table">
                <thead>
                  <tr>
                    <th>หุ้น</th>
                    <th className="right">ราคา</th>
                    <th className="right">เปลี่ยนแปลง</th>
                    <th>1 เดือน</th>
                    <th aria-label="จัดการ" />
                  </tr>
                </thead>
                <tbody>
                  {symbols.map((symbol, index) => {
                    const history = histories[index]
                    const bars = history.data?.bars ?? []
                    const last = bars[bars.length - 1]
                    const prev = bars[bars.length - 2]
                    const pct = last && prev ? ((last.c / prev.c - 1) * 100) : null
                    const spark = bars.slice(-22).map((bar) => bar.c)
                    return (
                      <tr key={symbol}>
                        <td>
                          <Link to={`/symbol/${symbol}`} className="watch-sym">
                            <Avatar symbol={symbol} name={history.data?.nameTh || history.data?.name} />
                            <span style={{ minWidth: 0 }}>
                              <span className="sym">{symbol}</span>
                              <span className="sym-name" style={{ display: 'block', maxWidth: 220 }}>
                                {history.data?.nameTh || history.data?.name || '—'}
                              </span>
                            </span>
                          </Link>
                        </td>
                        <td className="right">
                          {history.isPending ? (
                            <SkeletonBlock height={12} width={56} />
                          ) : (
                            <span className="num">{fmtPrice(last?.c)}</span>
                          )}
                        </td>
                        <td className="right">
                          {history.isPending ? (
                            <SkeletonBlock height={12} width={46} />
                          ) : (
                            <Delta value={pct} showIcon={false} />
                          )}
                        </td>
                        <td>
                          {spark.length > 2 ? (
                            <Sparkline
                              data={spark}
                              tone={(pct ?? 0) >= 0 ? 'up' : 'down'}
                              className="mini-spark"
                              width={96}
                              height={30}
                            />
                          ) : (
                            <span className="faint" style={{ fontSize: 11 }}>—</span>
                          )}
                        </td>
                        <td className="right">
                          <button
                            type="button"
                            className="remove-btn"
                            onClick={() => {
                              remove(symbol)
                              notify(`นำ ${symbol} ออกจาก Watchlist แล้ว`)
                            }}
                            aria-label={`นำ ${symbol} ออกจาก Watchlist`}
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
              <p className="muted" style={{ fontSize: 11, padding: '10px 4px 4px' }}>
                {histories[0]?.data?.asOf ? `ข้อมูลล่าสุด ${timeAgo(histories[0].data.asOf)}` : ''}
              </p>
            </div>
          )}
        </section>

        <aside style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <section className="card" aria-label="หุ้นยอดนิยม">
            <div className="card-head">
              <h2 className="card-title">
                <Star size={16} strokeWidth={1.9} aria-hidden="true" />
                หุ้นยอดนิยม
              </h2>
              <span className="card-meta">30 ตัวในฐานข้อมูล</span>
            </div>
            <div style={{ padding: '0 14px 14px', display: 'flex', flexDirection: 'column', gap: 7 }}>
              {popular.isPending
                ? [0, 1, 2, 3, 4].map((row) => <SkeletonBlock key={row} height={44} radius={13} />)
                : suggestions.slice(0, 6).map((item) => (
                    <SuggestCard key={item.symbol} item={item} onAdd={() => addSymbol(item.symbol)} />
                  ))}
              {!popular.isPending && suggestions.length === 0 ? (
                <p className="muted" style={{ fontSize: 12, padding: '6px 2px' }}>
                  เพิ่มครบทั้ง 30 หุ้นยอดนิยมแล้ว — สุดยอด!
                </p>
              ) : null}
            </div>
          </section>

          <section className="card card-pad">
            <h2 className="card-title" style={{ fontSize: 14 }}>
              วิธีใช้ Watchlist
            </h2>
            <p className="muted" style={{ fontSize: 12, marginTop: 6, lineHeight: 1.7 }}>
              พิมพ์ ticker หรือชื่อบริษัทในช่องค้นหา แล้วกด Enter หรือเลือกจากผลลัพธ์
              รายการถูกเก็บในเบราว์เซอร์และซิงก์ข้ามแท็บให้อัตโนมัติ
            </p>
            <Link className="link-more" to="/" style={{ marginTop: 6, paddingLeft: 0 }}>
              กลับไปภาพรวมตลาด <ArrowRight size={13} aria-hidden="true" />
            </Link>
          </section>
        </aside>
      </div>

      {toast ? <div className="toast" role="status">{toast}</div> : null}
    </div>
  )
}

function SuggestCard({ item, onAdd }: { item: SymbolItem; onAdd: () => void }) {
  return (
    <button type="button" className="suggest-card" onClick={onAdd}>
      <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
        <span className="suggest-sym">{item.symbol}</span>
        <Plus size={13} aria-hidden="true" className="faint" />
      </span>
      <span className="suggest-name" style={{ display: 'block' }}>
        {item.nameTh || item.name}
      </span>
    </button>
  )
}
