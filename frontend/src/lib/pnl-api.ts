const BASE = "/api/pnl"

export type TradeStatus = "open" | "closed"

export type Trade = {
  id: string
  ticker: string
  entry_date: string
  entry_price: number
  shares: number
  exit_date: string | null
  exit_price: number | null
  notes: string
  account: string
  value: number
  pnl: number | null
  percent: number | null
  status: TradeStatus
}

export type Ledger = {
  updated_at: string
  trades: Trade[]
  total_pnl: number
  open_count: number
  closed_count: number
  open_value: number
}

export type TradeInput = {
  ticker: string
  entry_date: string
  entry_price: number
  shares: number
  exit_date?: string | null
  exit_price?: number | null
  notes?: string
  account?: string
}

async function readError(response: Response) {
  const fallback = `Request failed with status ${response.status}`
  try {
    const body = (await response.json()) as { detail?: unknown; error?: unknown }
    const detail = body.detail ?? body.error
    return typeof detail === "string" && detail ? detail : fallback
  } catch {
    return fallback
  }
}

export async function fetchLedger(signal?: AbortSignal): Promise<Ledger> {
  const response = await fetch(`${BASE}/`, { signal })
  if (!response.ok) {
    throw new Error(await readError(response))
  }
  return response.json() as Promise<Ledger>
}

export async function createTrade(
  body: TradeInput,
  signal?: AbortSignal
): Promise<Trade> {
  const response = await fetch(`${BASE}/trades`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  })
  if (!response.ok) {
    throw new Error(await readError(response))
  }
  return response.json() as Promise<Trade>
}

export async function updateTrade(
  tradeId: string,
  body: TradeInput,
  signal?: AbortSignal
): Promise<Trade> {
  const response = await fetch(
    `${BASE}/trades/${encodeURIComponent(tradeId)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    }
  )
  if (!response.ok) {
    throw new Error(await readError(response))
  }
  return response.json() as Promise<Trade>
}

export async function deleteTrade(
  tradeId: string,
  signal?: AbortSignal
): Promise<void> {
  const response = await fetch(
    `${BASE}/trades/${encodeURIComponent(tradeId)}`,
    { method: "DELETE", signal }
  )
  if (!response.ok) {
    throw new Error(await readError(response))
  }
}
