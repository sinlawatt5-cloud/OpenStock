export type Meta = {
  stale: boolean
  asOf: string | null
  ageSeconds: number
  provider: string
}

export type IndexQuote = {
  symbol: string
  label: string
  short: string
  kind: 'index' | 'crypto' | 'commodity'
  price: number
  change: number | null
  changePct: number | null
  sparkline: number[]
}

export type Breadth = {
  pctAboveMa200: number
  above: number
  universeSize: number
  stale?: boolean
  ageSeconds?: number
  asOf?: string | null
}

export type SpyTrend = {
  price: number
  changePct: number | null
  ma200: number
  vsMa200Pct: number
  aboveMa200: boolean
}

export type Overview = Meta & {
  indices: IndexQuote[]
  spy: SpyTrend | null
  breadth: Breadth | null
}

export type MoverRow = {
  symbol: string
  name: string
  price: number
  change: number | null
  changePct: number | null
  volume: number | null
  exchange?: string | null
  logo?: string | null
}

export type MoversResponse = Meta & {
  list: 'gainers' | 'losers' | 'actives'
  rows: MoverRow[]
}

export type FlowRow = {
  symbol: string
  name: string
  nameTh: string
  price: number
  change: number
  pct: number
  dollarVolume: number
  flowScore: number
  benchmark: boolean
}

export type RiskSignalStatus = 'positive' | 'negative' | 'unavailable'

export type RiskSignal = {
  id: string
  label: string
  description: string
  formula: string
  status: RiskSignalStatus
  values: Record<string, number> | null
}

export type RiskOnSummary = {
  score: number
  of: number
  signals: RiskSignal[]
}

export type FlowsResponse = Meta & {
  group: string
  range: string
  mode: string
  description: string
  rows: FlowRow[]
  summary: {
    inflow: number
    outflow: number
    total: number
    benchmarkPct: number | null
    label: string
  }
  riskOn?: RiskOnSummary
}

export type NewsItem = {
  title: string
  url: string | null
  source: string
  publishedAt: string | null
  summary?: string | null
  tickers: string[]
}

export type NewsResponse = Meta & {
  items: NewsItem[]
  focus: string[]
}

export type NewsSummary = {
  status: 'ready' | 'fallback' | string
  text: string
  provider: 'gemini' | 'openrouter' | 'rules' | string
  model: string
  cached: boolean
  sources: NewsItem[]
  stale?: boolean
  asOf?: string
}

export type Bar = {
  t: number
  dt: string
  o: number
  h: number
  l: number
  c: number
  v: number
}

export type HistoryResponse = Meta & {
  symbol: string
  name?: string | null
  nameTh?: string | null
  range: string
  interval: string
  bars: Bar[]
  last: Bar | null
}

export type Level = {
  price: number
  zoneLow: number
  zoneHigh: number
  touches: number
  strength: number
  distancePct: number
  source: 'structure' | 'pivot' | 'range' | string
}

export type LevelsResponse = Meta & {
  symbol: string
  range: string
  method: 'structure' | 'pivot' | string
  atr: number
  fallback: boolean
  price: number | null
  supports: Level[]
  resistances: Level[]
}

export type Quote = Meta & {
  symbol: string
  price: number
  change: number
  changePct: number
  volume: number | null
  prevClose: number
  name?: string | null
  nameTh?: string | null
  sector?: string | null
  industry?: string | null
}

export type Profile = Meta & {
  symbol: string
  name: string
  nameTh?: string | null
  exchange?: string | null
  sector?: string | null
  industry?: string | null
  logo?: string | null
  website?: string | null
  summary?: string | null
  employees?: number | null
  marketCap?: number | null
  peTrailing?: number | null
  peForward?: number | null
  week52High?: number | null
  week52Low?: number | null
  avgVolume?: number | null
  dividendYield?: number | null
  beta?: number | null
  currency?: string | null
}

export type Peer = {
  symbol: string
  name: string
  nameTh: string | null
  sector: string | null
}

export type SymbolPageResponse = {
  symbol: string
  quote: Quote
  profile: Profile
  peers: Peer[]
}

export type SymbolItem = {
  symbol: string
  name: string
  nameTh: string
  exchange: string | null
  sector: string | null
  industry: string | null
}

export type SearchResponse = {
  query: string
  source: string
  results: {
    symbol: string
    name: string
    nameTh: string | null
    exchange: string | null
    sector: string | null
    source: string
  }[]
}

export type CatalogGroup = {
  key: string
  label: string
  description: string
  items: { symbol: string; name: string; name_th: string }[]
}

export type Catalog = {
  groups: CatalogGroup[]
  ranges: { key: string; label: string }[]
  benchmark: { symbol: string; name: string; name_th: string }
  indices: { symbol: string; label: string; kind: string }[]
  disclaimer: string
}
