const BASE = (import.meta.env.VITE_API_BASE as string | undefined)?.replace(/\/$/, '') ?? '/api'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

type Query = Record<string, string | number | boolean | undefined | null>

export async function apiGet<T>(path: string, query?: Query): Promise<T> {
  const url = new URL(`${BASE}${path}`, window.location.origin)
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value))
      }
    }
  }
  let response: Response
  try {
    response = await fetch(url.toString(), { headers: { Accept: 'application/json' } })
  } catch {
    throw new ApiError('เชื่อมต่อเซิร์ฟเวอร์ข้อมูลไม่ได้', 0)
  }
  if (!response.ok) {
    let detail = ''
    try {
      const body = (await response.json()) as { detail?: string }
      detail = body.detail ?? ''
    } catch {
      detail = ''
    }
    throw new ApiError(detail || `คำขอข้อมูลล้มเหลว (${response.status})`, response.status)
  }
  return (await response.json()) as T
}
