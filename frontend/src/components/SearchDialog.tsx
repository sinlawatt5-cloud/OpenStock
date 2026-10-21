import { useQuery } from '@tanstack/react-query'
import { Search, TrendingUp } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiGet } from '../lib/api'
import type { SearchResponse, SymbolItem } from '../lib/types'
import { useDebounced } from '../lib/useDebounced'
import { Avatar } from './Avatar'
import { SkeletonBlock } from './States'

type Props = {
  open: boolean
  onClose: () => void
}

export function SearchDialog({ open, onClose }: Props) {
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()
  const debounced = useDebounced(query.trim(), 200)

  const popular = useQuery({
    queryKey: ['symbols', 'popular'],
    queryFn: () => apiGet<{ items: SymbolItem[] }>('/symbols', { limit: 30 }),
    enabled: open,
    staleTime: 10 * 60_000,
  })

  const search = useQuery({
    queryKey: ['search', debounced],
    queryFn: () => apiGet<SearchResponse>('/search', { q: debounced }),
    enabled: open && debounced.length >= 1,
    staleTime: 5 * 60_000,
  })

  const results = useMemo(() => {
    if (debounced.length >= 1) {
      return (search.data?.results ?? []).slice(0, 8).map((row) => ({
        symbol: row.symbol,
        name: row.nameTh || row.name,
        sub: row.nameTh ? row.name : row.exchange || '',
        exchange: row.exchange,
      }))
    }
    return (popular.data?.items ?? []).slice(0, 6).map((row) => ({
      symbol: row.symbol,
      name: row.nameTh || row.name,
      sub: row.name,
      exchange: row.exchange,
    }))
  }, [debounced, search.data, popular.data])

  useEffect(() => {
    if (!open) return
    setQuery('')
    setActive(0)
    const timer = window.setTimeout(() => inputRef.current?.focus(), 30)
    return () => window.clearTimeout(timer)
  }, [open])

  useEffect(() => {
    setActive(0)
  }, [debounced])

  useEffect(() => {
    if (!open) return
    const original = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = original
    }
  }, [open])

  if (!open) return null

  const choose = (symbol: string) => {
    navigate(`/symbol/${symbol}`)
    onClose()
  }

  return (
    <div
      className="overlay"
      role="dialog"
      aria-modal="true"
      aria-label="ค้นหาหุ้น"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <div
        className="dialog"
        onKeyDown={(event) => {
          if (event.key === 'Escape') {
            event.stopPropagation()
            onClose()
          } else if (event.key === 'ArrowDown') {
            event.preventDefault()
            setActive((current) => Math.min(current + 1, results.length - 1))
          } else if (event.key === 'ArrowUp') {
            event.preventDefault()
            setActive((current) => Math.max(current - 1, 0))
          } else if (event.key === 'Enter' && results[active]) {
            event.preventDefault()
            choose(results[active].symbol)
          }
        }}
      >
        <div className="dialog-search">
          <Search size={17} strokeWidth={1.9} aria-hidden="true" />
          <input
            ref={inputRef}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="ค้นหาชื่อหุ้นหรือ ticker เช่น NVDA, Apple"
            aria-label="คำค้นหา"
            autoComplete="off"
            spellCheck={false}
          />
          <button type="button" className="icon-btn square" onClick={onClose} aria-label="ปิดการค้นหา">
            ESC
          </button>
        </div>
        <div className="dialog-list" role="listbox" aria-label="ผลการค้นหา">
          {debounced.length >= 1 && search.isLoading ? (
            <div style={{ padding: 8, display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[0, 1, 2].map((row) => (
                <SkeletonBlock key={row} height={38} />
              ))}
            </div>
          ) : null}
          {results.map((row, index) => (
            <button
              key={row.symbol}
              type="button"
              role="option"
              aria-selected={index === active}
              className={`dialog-row${index === active ? ' active' : ''}`}
              onMouseEnter={() => setActive(index)}
              onClick={() => choose(row.symbol)}
            >
              <Avatar symbol={row.symbol} name={row.name} />
              <span style={{ minWidth: 0, flex: 1 }}>
                <span className="sym" style={{ display: 'block' }}>
                  {row.symbol}
                </span>
                <span className="sym-name" style={{ display: 'block' }}>
                  {row.name}
                </span>
              </span>
              {row.exchange ? <span className="card-meta">{row.exchange}</span> : null}
            </button>
          ))}
          {debounced.length >= 1 && !search.isLoading && results.length === 0 ? (
            <div className="error-box" style={{ border: 0, background: 'transparent' }}>
              <TrendingUp size={18} aria-hidden="true" />
              <span>ไม่พบหุ้นที่ตรงกับ “{debounced}”</span>
            </div>
          ) : null}
          {debounced.length === 0 ? (
            <div className="card-meta" style={{ padding: '8px 10px 4px', display: 'flex', alignItems: 'center', gap: 6 }}>
              <TrendingUp size={12} aria-hidden="true" /> หุ้นยอดนิยม
            </div>
          ) : null}
        </div>
        <div className="dialog-hint">
          ↑ ↓ เลือก · Enter เปิด · ESC ปิด — เพิ่มใน Watchlist ได้จากหน้าหุ้นรายตัว
        </div>
      </div>
    </div>
  )
}
