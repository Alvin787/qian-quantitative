const BASE = "/api/watchlists"

export type Gates = {
  adr_pct: number | null
  adr_ok: boolean | null
  avg_dollar_vol: number | null
  liq_ok: boolean | null
  close: number | null
  sma10: number | null
  sma20: number | null
  sma50: number | null
  sma200: number | null
  above_10: boolean | null
  above_20: boolean | null
  rising_10: boolean | null
  rising_20: boolean | null
  extension_x: number | null
  ext_ok: boolean | null
  rs_3m_pp: number | null
  rs_ok: boolean | null
  earnings_date: string | null
  days_to_earnings: number | null
  earn_ok: string | null
  biotech: boolean | null
  declining_200: boolean | null
  room_to_200_adr: number | null
  room_to_200_ok: boolean | null
  volume_dryup: boolean | null
  range_compress: boolean | null
  near_10_20: boolean | null
  atr_pct: number | null
  extension_basis: string | null
  rs_sessions: number | null
  price_as_of: string | null
  data_fresh: boolean | null
}

export type ChartChecklist = {
  catalyst: boolean | null
  vcp: boolean | null
  linearity: boolean | null
  pivot: boolean | null
  group_leader: boolean | null
  gap_resistance_ok: boolean | null
  stop_planned: boolean | null
  alert_set: boolean | null
  earnings_verified: boolean | null
}

export type Readiness =
  | "unscored"
  | "watch"
  | "stalk_ready"
  | "chart_review_ready"
  | "earnings_blocked"
  | "data_incomplete"
  | "disrupted"
  | "excluded"
  | "unknown"

export type WatchlistName = {
  ticker: string
  list: string
  added_at: string
  source_screens: string[]
  historical_source_screens: string[]
  screen_count: number | null
  screen_family_count: number | null
  industry: string
  note: string
  group: string
  readiness: Readiness | string
  queue_reason: string | null
  fail_reasons: string
  gates: Gates
  chart_checklist: ChartChecklist
  manual_focus_approved_at: string | null
  last_scored_at: string | null
}

export type FunnelName = WatchlistName

export type ReviewMeta = {
  review_id: string | null
  status: string
  started_at: string | null
  finished_at: string | null
  ingested: number | null
  scored: number | null
  unknown: number | null
  error: string | null
  notes: string | null
  breakout_run_id: string | null
}

export type FunnelState = {
  updated_at: string
  review: ReviewMeta
  names: WatchlistName[]
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

export async function fetchFunnel(signal?: AbortSignal): Promise<FunnelState> {
  const response = await fetch(`${BASE}/`, { signal })
  if (!response.ok) {
    throw new Error(await readError(response))
  }
  return response.json() as Promise<FunnelState>
}

export async function upsertName(
  body: {
    ticker: string
    list: string
    note?: string | null
    group?: string | null
    chart_checklist?: Partial<ChartChecklist> | null
  },
  signal?: AbortSignal
): Promise<WatchlistName> {
  const response = await fetch(`${BASE}/names`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  })
  if (!response.ok) {
    throw new Error(await readError(response))
  }
  return response.json() as Promise<WatchlistName>
}

export async function moveName(
  ticker: string,
  list: string,
  signal?: AbortSignal
): Promise<WatchlistName> {
  const response = await fetch(
    `${BASE}/names/${encodeURIComponent(ticker)}/move`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ list }),
      signal,
    }
  )
  if (!response.ok) {
    throw new Error(await readError(response))
  }
  return response.json() as Promise<WatchlistName>
}

export async function updateChecklist(
  ticker: string,
  checklist: Partial<ChartChecklist>,
  signal?: AbortSignal
): Promise<WatchlistName> {
  const response = await fetch(
    `${BASE}/names/${encodeURIComponent(ticker)}/checklist`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(checklist),
      signal,
    }
  )
  if (!response.ok) {
    throw new Error(await readError(response))
  }
  return response.json() as Promise<WatchlistName>
}

export async function deleteName(
  ticker: string,
  signal?: AbortSignal
): Promise<void> {
  const response = await fetch(
    `${BASE}/names/${encodeURIComponent(ticker)}`,
    {
      method: "DELETE",
      signal,
    }
  )
  if (!response.ok) {
    throw new Error(await readError(response))
  }
}

export async function startReview(signal?: AbortSignal): Promise<ReviewMeta> {
  const response = await fetch(`${BASE}/reviews`, { method: "POST", signal })
  if (!response.ok) {
    throw new Error(await readError(response))
  }
  return response.json() as Promise<ReviewMeta>
}

export async function getReview(
  id: string,
  signal?: AbortSignal
): Promise<ReviewMeta> {
  const response = await fetch(
    `${BASE}/reviews/${encodeURIComponent(id)}`,
    { signal }
  )
  if (!response.ok) {
    throw new Error(await readError(response))
  }
  return response.json() as Promise<ReviewMeta>
}

