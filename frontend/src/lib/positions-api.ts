const BASE = "/api/positions"

export type StopLevel = {
  label: string
  price: number
  shares: number
  r_fraction: number
}

export type SizeRequest = {
  equity: number
  entry_price: number
  final_stop: number
  method?: "fixed_pct" | "kelly" | "half_kelly"
  risk_pct?: number
  max_risk_pct?: number
  win_rate?: number | null
  avg_win_r?: number | null
  avg_loss_r?: number | null
  adr_pct?: number | null
}

export type SizeResponse = {
  method: string
  equity: number
  risk_pct: number
  risk_dollars: number
  entry_price: number
  final_stop: number
  r_per_share: number
  shares: number
  stop_book: StopLevel[]
  expected_full_stop_r: number
  kelly_f_star: number | null
  suggested_risk_pct: number | null
  suggested_shares: number | null
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

export async function computePositionSize(
  body: SizeRequest,
  signal?: AbortSignal
): Promise<SizeResponse> {
  const response = await fetch(`${BASE}/size`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    signal,
  })

  if (!response.ok) {
    throw new Error(await readError(response))
  }

  return (await response.json()) as SizeResponse
}

export type PlanRequest = {
  shares: number
  entry_price: number
  final_stop: number
  entry_date: string
  as_of_date: string
  current_price?: number | null
  shave_2r_taken?: boolean
  day3_partial_taken?: boolean
  consolidated_to_be?: boolean
  ma10?: number | null
  ma50?: number | null
  atr_pct?: number | null
  close_below_10ma_date?: string | null
  orl?: number | null
  stops_33_hit?: boolean
  stops_66_hit?: boolean
  prior_day_high?: number | null
  rescale_alert_triggered?: boolean
  sideways_consolidation?: boolean
  extension_override?: number | null
}

export type PlanAction = {
  code: string
  severity: string
  message: string
}

export type PlanResponse = {
  day_index: number
  phase: string
  entry_price: number
  final_stop: number
  r_per_share: number
  net_shares: number
  unrealized_r: number | null
  stop_mode: string
  stop_book: StopLevel[]
  mental_stop: string | null
  actions: PlanAction[]
}

export async function computePositionPlan(
  body: PlanRequest,
  signal?: AbortSignal
): Promise<PlanResponse> {
  const response = await fetch(`${BASE}/plan`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    signal,
  })

  if (!response.ok) {
    throw new Error(await readError(response))
  }

  return (await response.json()) as PlanResponse
}
