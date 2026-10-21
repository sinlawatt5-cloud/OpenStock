import { Compass } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useDocumentTitle } from '../lib/useDocumentTitle'

export function NotFoundPage() {
  useDocumentTitle('ไม่พบหน้านี้')
  return (
    <div className="page">
      <section className="card card-pad" style={{ textAlign: 'center', padding: 42 }}>
        <div className="empty-illustration" style={{ maxWidth: 320, margin: '0 auto 18px' }} aria-hidden="true">
          <Compass size={26} strokeWidth={1.7} />
        </div>
        <h1 className="page-title" style={{ fontSize: 26 }}>
          ไม่พบหน้าที่ค้นหา
        </h1>
        <p className="muted" style={{ marginTop: 8, fontSize: 13 }}>
          ลิงก์อาจเปลี่ยนไปแล้ว — กลับไปดูภาพรวมตลาดหรือค้นหาหุ้นจากเมนูด้านบน
        </p>
        <Link className="icon-btn" to="/" style={{ marginTop: 16 }}>
          กลับภาพรวมตลาด
        </Link>
      </section>
    </div>
  )
}
