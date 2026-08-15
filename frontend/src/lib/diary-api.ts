const BASE = "/api/diary"

export type EtfRow = {
  symbol: string
  last: number
  daily_change_pct: number
  pct_from_52w_low: number
  pct_from_52w_high: number
  short_term_trend: string
  priority?: boolean
  ratio_to?: string | null
  ratio_value?: number | null
}

export type BarchartHistoryPoint = {
  date: string
  last: number
}

export type BreadthBlock = {
  mmtw_last: number | null
  mmtw_history: BarchartHistoryPoint[]
  mmtw_bullish_bias: boolean | null
  finviz_new_highs: number | null
  finviz_new_lows: number | null
  finviz_net: number | null
  nyhl: number | null
  nahl: number | null
  sources: {
    mmtw: string
    finviz_nhnl: string
    nyhl_nahl: string
  }
}

export type CnbcBrief = {
  title: string
  url: string
  excerpt: string | null
  published: string | null
}

export type Narrative = {
  date: string
  body: string
  updated_at: string
}

export type DiarySnapshot = {
  as_of: string
  as_of_date: string
  market: EtfRow[]
  market_ratios: EtfRow[]
  submarket: EtfRow[]
  sectors: EtfRow[]
  breadth: BreadthBlock | null
  cnbc: CnbcBrief | null
  sections: Record<string, { status: string; source: string; error: string | null }>
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

export async function fetchDiarySnapshot(
  signal?: AbortSignal
): Promise<DiarySnapshot> {
  const response = await fetch(`${BASE}/snapshot`, {
    headers: { Accept: "application/json" },
    signal,
  })

  if (!response.ok) {
    throw new Error(await readError(response))
  }

  return (await response.json()) as DiarySnapshot
}

export async function fetchNarrative(
  date: string,
  signal?: AbortSignal
): Promise<Narrative | null> {
  const response = await fetch(
    `${BASE}/narrative?date=${encodeURIComponent(date)}`,
    {
      headers: { Accept: "application/json" },
      signal,
    }
  )

  if (response.status === 404) {
    return null
  }

  if (!response.ok) {
    throw new Error(await readError(response))
  }

  return (await response.json()) as Narrative
}

export async function putNarrative(
  date: string,
  body: string,
  signal?: AbortSignal
): Promise<Narrative> {
  const response = await fetch(`${BASE}/narrative`, {
    method: "PUT",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ date, body }),
    signal,
  })

  if (!response.ok) {
    throw new Error(await readError(response))
  }

  return (await response.json()) as Narrative
}

export type FocusItem = {
  ticker: string
  group: string
  note: string
}

export type NamedGroup = {
  name: string
  tickers: string[]
}

export type Watchlists = {
  focus: FocusItem[]
  stalk: string[]
  themes: NamedGroup[]
  leadership: NamedGroup[]
}

export type EnrichRow = {
  ticker: string
  daily_change_pct: number | null
  pct_from_52w_low: number | null
  avg_dollar_volume_20: number | null
  error: string | null
}

export async function fetchWatchlists(
  signal?: AbortSignal
): Promise<Watchlists> {
  const response = await fetch(`${BASE}/watchlists`, {
    headers: { Accept: "application/json" },
    signal,
  })

  if (!response.ok) {
    throw new Error(await readError(response))
  }

  return (await response.json()) as Watchlists
}

export async function putWatchlists(
  watchlists: Watchlists,
  signal?: AbortSignal
): Promise<Watchlists> {
  const response = await fetch(`${BASE}/watchlists`, {
    method: "PUT",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(watchlists),
    signal,
  })

  if (!response.ok) {
    throw new Error(await readError(response))
  }

  return (await response.json()) as Watchlists
}

export async function enrichWatchlists(
  tickers: string[],
  signal?: AbortSignal
): Promise<EnrichRow[]> {
  const response = await fetch(`${BASE}/watchlists/enrich`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ tickers }),
    signal,
  })

  if (!response.ok) {
    throw new Error(await readError(response))
  }

  const body = (await response.json()) as { rows: EnrichRow[] }
  return body.rows
}
