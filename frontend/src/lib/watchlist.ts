import { useSyncExternalStore } from 'react'

const KEY = 'openstock:watchlist'
const MAX = 20

function read(): string[] {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as unknown
    if (!Array.isArray(parsed)) return []
    return parsed
      .filter((item): item is string => typeof item === 'string')
      .map((item) => item.toUpperCase())
      .slice(0, MAX)
  } catch {
    return []
  }
}

let symbols: string[] = typeof window === 'undefined' ? [] : read()
const listeners = new Set<() => void>()

function emit() {
  listeners.forEach((listener) => listener())
}

function persist(next: string[]) {
  symbols = [...new Set(next)].slice(0, MAX)
  try {
    localStorage.setItem(KEY, JSON.stringify(symbols))
  } catch {
    /* storage can be unavailable in private mode */
  }
  emit()
}

function subscribe(listener: () => void) {
  listeners.add(listener)
  const onStorage = (event: StorageEvent) => {
    if (event.key === KEY) {
      symbols = read()
      emit()
    }
  }
  window.addEventListener('storage', onStorage)
  return () => {
    listeners.delete(listener)
    window.removeEventListener('storage', onStorage)
  }
}

export function useWatchlist() {
  const items = useSyncExternalStore(subscribe, () => symbols, () => symbols)
  return {
    symbols: items,
    has: (symbol: string) => items.includes(symbol.toUpperCase()),
    add(symbol: string) {
      persist([...symbols, symbol.toUpperCase()])
    },
    remove(symbol: string) {
      persist(symbols.filter((item) => item !== symbol.toUpperCase()))
    },
    toggle(symbol: string) {
      const upper = symbol.toUpperCase()
      persist(items.includes(upper) ? items.filter((item) => item !== upper) : [...items, upper])
    },
  }
}

export const WATCHLIST_MAX = MAX
