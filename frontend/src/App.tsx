import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { DashboardPage } from './pages/DashboardPage'
import { FlowsPage } from './pages/FlowsPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { SymbolPage } from './pages/SymbolPage'
import { WatchlistPage } from './pages/WatchlistPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="flows" element={<FlowsPage />} />
          <Route path="watchlist" element={<WatchlistPage />} />
          <Route path="symbol/:symbol" element={<SymbolPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </QueryClientProvider>
  )
}
