import { Search, Sun } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { marketClock } from '../lib/format'

type Props = {
  onSearch: () => void
}

function MarketStatus() {
  const [clock, setClock] = useState(() => marketClock())

  useEffect(() => {
    const timer = window.setInterval(() => setClock(marketClock()), 60_000)
    return () => window.clearInterval(timer)
  }, [])

  return (
    <span
      className="market-status"
      title="อ้างอิงเวลาทำการปกติของตลาดสหรัฐ 09:30–16:00 น. เวลานิวยอร์ก"
    >
      <span className={`dot${clock.isOpen ? '' : ' closed'}`} aria-hidden="true" />
      {clock.label}
      <span className="num faint" style={{ fontSize: 11 }}>
        {clock.bangkokTime} น.
      </span>
    </span>
  )
}

export function TopNav({ onSearch }: Props) {
  return (
    <header className="topbar">
      <Link to="/" className="brand" aria-label="OpenStock ภาพรวมตลาด">
        <span className="brand-mark" aria-hidden="true">
          <Sun size={16} strokeWidth={2.2} />
        </span>
        <span className="brand-name">OpenStock</span>
      </Link>

      <nav className="nav-tabs" aria-label="เมนูหลัก">
        <NavLink to="/" end className={({ isActive }) => `nav-tab${isActive ? ' active' : ''}`}>
          ภาพรวม
        </NavLink>
        <NavLink to="/flows" className={({ isActive }) => `nav-tab${isActive ? ' active' : ''}`}>
          กระแสเงิน
        </NavLink>
        <NavLink to="/watchlist" className={({ isActive }) => `nav-tab${isActive ? ' active' : ''}`}>
          Watchlist
        </NavLink>
      </nav>

      <div className="topbar-tools">
        <button type="button" className="icon-btn" onClick={onSearch} aria-label="ค้นหาหุ้น">
          <Search size={14} strokeWidth={2} aria-hidden="true" />
          <span className="label">ค้นหา</span>
          <kbd className="kbd">⌘K</kbd>
        </button>
        <MarketStatus />
      </div>
    </header>
  )
}
