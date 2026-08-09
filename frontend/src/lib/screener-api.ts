const BASE = "/api/screener"

/** Statuses the UI reasons about, independent of backend wording. */
export type RunStatus = "running" | "succeeded" | "failed"

export type ResultView = string

export type ScreenerScreen = { id: string; label: string; url: string }

export type Strategy = {
  id: string
  label: string
  description: string
  views: ResultView[]
  defaultView: ResultView
  screens: ScreenerScreen[]
}

export type ScreenerRun = {
  id: string
  status: RunStatus
  /** Raw backend status, shown verbatim so the UI never invents wording. */
  statusLabel: string
  startedAt: string | null
  finishedAt: string | null
  scored: number | null
  passed: number | null
  skipped: number | null
  error: string | null
  legacy: boolean
}

export type ResultValue = string | number | boolean | null

export type ResultRow = Record<string, ResultValue>

export type ScreenerResults = {
  runId: string
  view: ResultView
  status: RunStatus
  columns: string[]
  rows: ResultRow[]
  rowCount: number
}

type RawStrategy = {
  id?: string
  label?: string
  description?: string
  views?: ResultView[]
  default_view?: ResultView
  screens?: ScreenerScreen[]
}

type RawRun = {
  run_id?: string
  status?: string
  started_at?: string | null
  finished_at?: string | null
  scored?: number | null
  passed?: number | null
  skipped?: number | null
  error?: string | null
  legacy?: boolean
}

type RawResults = {
  run_id?: string
  view?: ResultView
  status?: string
  columns?: string[]
  rows?: ResultRow[]
  row_count?: number
}

export function isTerminal(status: RunStatus) {
  return status !== "running"
}

function normalizeStatus(raw: string | undefined): RunStatus {
  switch (raw) {
    case "completed":
      return "succeeded"
    case "failed":
      return "failed"
    default:
      // Unknown states are treated as in-flight so polling keeps following them.
      return "running"
  }
}

function normalizeStrategy(raw: RawStrategy): Strategy {
  return {
    id: raw.id ?? "",
    label: raw.label ?? "",
    description: raw.description ?? "",
    views: raw.views ?? [],
    defaultView: raw.default_view ?? "",
    screens: raw.screens ?? [],
  }
}

function normalizeRun(raw: RawRun): ScreenerRun {
  return {
    id: raw.run_id ?? "",
    status: normalizeStatus(raw.status),
    statusLabel: raw.status ?? "unknown",
    startedAt: raw.started_at ?? null,
    finishedAt: raw.finished_at ?? null,
    scored: raw.scored ?? null,
    passed: raw.passed ?? null,
    skipped: raw.skipped ?? null,
    error: raw.error ?? null,
    legacy: raw.legacy ?? false,
  }
}

function normalizeResults(
  raw: RawResults,
  runId: string,
  view: ResultView
): ScreenerResults {
  const rows = raw.rows ?? []
  const columns =
    raw.columns && raw.columns.length > 0
      ? raw.columns
      : Object.keys(rows[0] ?? {})

  return {
    runId: raw.run_id ?? runId,
    view: raw.view ?? view,
    status: normalizeStatus(raw.status),
    columns,
    rows,
    rowCount: raw.row_count ?? rows.length,
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    headers: { Accept: "application/json", ...init?.headers },
    ...init,
  })

  if (!response.ok) {
    throw new Error(await readError(response))
  }

  return (await response.json()) as T
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

export async function listStrategies(signal?: AbortSignal): Promise<Strategy[]> {
  const payload = await request<{ strategies?: RawStrategy[] }>("/strategies", {
    signal,
  })
  return (payload.strategies ?? []).map(normalizeStrategy)
}

export async function startRun(
  strategyId: string,
  options?: Record<string, boolean>,
  signal?: AbortSignal
): Promise<ScreenerRun> {
  const raw = await request<RawRun>(
    `/${encodeURIComponent(strategyId)}/runs`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ options: options ?? {} }),
      signal,
    }
  )
  return normalizeRun(raw)
}

export async function listRuns(
  strategyId: string,
  signal?: AbortSignal
): Promise<ScreenerRun[]> {
  const payload = await request<{ runs?: RawRun[] }>(
    `/${encodeURIComponent(strategyId)}/runs`,
    { signal }
  )
  return (payload.runs ?? []).map(normalizeRun)
}

export async function getRun(
  strategyId: string,
  runId: string,
  signal?: AbortSignal
): Promise<ScreenerRun> {
  const raw = await request<RawRun>(
    `/${encodeURIComponent(strategyId)}/runs/${encodeURIComponent(runId)}`,
    {
      signal,
    }
  )
  return normalizeRun({ ...raw, run_id: raw.run_id ?? runId })
}

export async function getResults(
  strategyId: string,
  runId: string,
  view: ResultView,
  signal?: AbortSignal
): Promise<ScreenerResults> {
  const raw = await request<RawResults>(
    `/${encodeURIComponent(strategyId)}/runs/${encodeURIComponent(runId)}/results?view=${view}`,
    { signal }
  )
  return normalizeResults(raw, runId, view)
}

export function downloadUrl(
  strategyId: string,
  runId: string,
  view: ResultView
): string {
  return `${BASE}/${encodeURIComponent(strategyId)}/runs/${encodeURIComponent(runId)}/download?view=${view}`
}
