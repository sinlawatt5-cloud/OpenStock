import { useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { SearchDialog } from './SearchDialog'
import { TopNav } from './TopNav'

export function AppShell() {
  const [searchOpen, setSearchOpen] = useState(false)
  const location = useLocation()

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'auto' })
  }, [location.pathname])

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setSearchOpen((open) => !open)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  return (
    <div className="shell">
      <TopNav onSearch={() => setSearchOpen(true)} />
      <main>
        <Outlet />
      </main>
      <footer className="site-footer">
        <p>
          <strong>OpenStock</strong> · ข้อมูลจาก Yahoo Finance, Finnhub และ Alpha Vantage
        </p>
        <p>
          ราคาอาจล่าช้าประมาณ 15 นาที · กระแสเงินเป็นประมาณการจากราคาและมูลค่าซื้อขาย · ไม่ใช่คำแนะนำการลงทุน
        </p>
      </footer>
      <SearchDialog open={searchOpen} onClose={() => setSearchOpen(false)} />
    </div>
  )
}
