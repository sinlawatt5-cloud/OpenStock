import { Sparkline } from '../../components/Sparkline'
import { SkeletonBlock } from '../../components/States'
import { Delta } from '../../components/Delta'
import { fmtPrice } from '../../lib/format'
import type { Overview } from '../../lib/types'

type Props = {
  data?: Overview
  loading: boolean
}

const KIND_LABEL: Record<string, string> = {
  index: 'INDEX',
  crypto: 'CRYPTO',
  commodity: 'COMMODITY',
}

export function IndexStrip({ data, loading }: Props) {
  if (loading || !data) {
    return (
      <div className="index-grid" aria-busy="true" aria-label="กำลังโหลดดัชนีตลาด">
        {Array.from({ length: 5 }).map((_, index) => (
          <div key={index} className="index-card" style={{ gap: 14 }}>
            <SkeletonBlock height={11} width="55%" />
            <SkeletonBlock height={26} width="80%" />
            <SkeletonBlock height={12} width="45%" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="index-grid">
      {data.indices.map((item, index) => {
        const hero = index === 0
        return (
          <article key={item.symbol} className={`index-card${hero ? ' index-card--hero' : ''}`}>
            {hero ? (
              <svg className="hero-sun" viewBox="0 0 120 120" aria-hidden="true">
                <path d="M8 96a52 52 0 0 1 104 0" fill="none" stroke="rgba(255,255,255,.55)" strokeWidth="14" strokeLinecap="round" />
                <path d="M26 96a34 34 0 0 1 68 0" fill="none" stroke="rgba(255,255,255,.45)" strokeWidth="7" strokeLinecap="round" />
              </svg>
            ) : null}
            <div className="index-top">
              <span className="index-label">{item.label}</span>
              <span className="index-kind">{KIND_LABEL[item.kind] ?? item.kind}</span>
            </div>
            <div className="index-price" title={fmtPrice(item.price)}>
              {fmtPrice(item.price)}
            </div>
            <div className="index-bottom">
              <Delta value={item.changePct} hero={hero} />
              {item.sparkline.length > 2 ? (
                <Sparkline
                  data={item.sparkline}
                  tone={(item.changePct ?? 0) >= 0 ? 'up' : 'down'}
                  className="sparkline"
                />
              ) : (
                <span className="index-sub">{item.symbol}</span>
              )}
            </div>
          </article>
        )
      })}
    </div>
  )
}
