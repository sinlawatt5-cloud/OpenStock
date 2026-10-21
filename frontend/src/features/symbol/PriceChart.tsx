import {
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  LineStyle,
  createChart,
  type CandlestickData,
  type Time,
  type UTCTimestamp,
} from 'lightweight-charts'
import { useEffect, useRef } from 'react'
import type { Bar, LevelsResponse } from '../../lib/types'

type Props = {
  bars: Bar[]
  levels?: LevelsResponse
  showLevels: boolean
  intraday: boolean
  loading?: boolean
}

export function PriceChart({ bars, levels, showLevels, intraday, loading }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container || bars.length === 0) return

    const chart = createChart(container, {
      width: container.clientWidth || 640,
      height: container.clientHeight || 360,
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#7A6154',
        fontFamily: "'Space Grotesk', 'IBM Plex Sans Thai', sans-serif",
        fontSize: 11,
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: 'rgba(241, 222, 201, 0.5)' },
        horzLines: { color: 'rgba(241, 222, 201, 0.5)' },
      },
      rightPriceScale: {
        borderVisible: false,
        scaleMargins: { top: 0.12, bottom: 0.08 },
      },
      timeScale: {
        borderVisible: false,
        timeVisible: intraday,
        secondsVisible: false,
        rightOffset: 4,
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: 'rgba(43, 26, 18, 0.28)',
          style: LineStyle.Dashed,
          labelBackgroundColor: '#2B1A12',
        },
        horzLine: {
          color: 'rgba(43, 26, 18, 0.28)',
          style: LineStyle.Dashed,
          labelBackgroundColor: '#2B1A12',
        },
      },
      localization: { locale: 'th-TH' },
    })

    const series = chart.addSeries(CandlestickSeries, {
      upColor: '#0E9F6E',
      downColor: '#D93F3F',
      borderUpColor: '#0E9F6E',
      borderDownColor: '#D93F3F',
      wickUpColor: '#0E9F6E',
      wickDownColor: '#D93F3F',
      priceLineVisible: false,
      lastValueVisible: true,
    })

    const data: CandlestickData<Time>[] = bars.map((bar) => ({
      time: (intraday ? bar.t : bar.dt.slice(0, 10)) as Time | UTCTimestamp,
      open: bar.o,
      high: bar.h,
      low: bar.l,
      close: bar.c,
    }))
    series.setData(data)

    if (showLevels && levels) {
      levels.supports.forEach((level, index) => {
        series.createPriceLine({
          price: level.price,
          color: '#0E9F6E',
          lineWidth: 1,
          lineStyle: LineStyle.Dashed,
          axisLabelVisible: true,
          title: `แนวรับ ${index + 1}`,
        })
      })
      levels.resistances.forEach((level, index) => {
        series.createPriceLine({
          price: level.price,
          color: '#D93F3F',
          lineWidth: 1,
          lineStyle: LineStyle.Dashed,
          axisLabelVisible: true,
          title: `แนวต้าน ${index + 1}`,
        })
      })
    }

    chart.timeScale().fitContent()

    const observer = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect.width
      if (width) chart.applyOptions({ width })
    })
    observer.observe(container)

    return () => {
      observer.disconnect()
      chart.remove()
    }
  }, [bars, levels, showLevels, intraday])

  return (
    <div
      className="chart-box"
      ref={containerRef}
      role="img"
      aria-label={
        loading
          ? 'กำลังโหลดกราฟราคา'
          : `กราฟราคา ${bars.length} แท่ง${showLevels ? ' พร้อมเส้นแนวรับและแนวต้าน' : ''}`
      }
    >
      {bars.length === 0 ? (
        <p className="muted" style={{ padding: 24, fontSize: 13 }}>
          {loading ? 'กำลังโหลดกราฟ…' : 'ยังไม่มีข้อมูลราคาในช่วงนี้'}
        </p>
      ) : null}
    </div>
  )
}
