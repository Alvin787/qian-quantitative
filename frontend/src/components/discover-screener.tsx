import { useCallback, useEffect, useId, useMemo, useState } from "react"
import { Download, Loader2, Play, RefreshCw, Search } from "lucide-react"

import { ColumnVisibilityMenu } from "@/components/column-visibility-menu"
import { ScreenerResultsTable } from "@/components/screener-results-table"
import { Button, buttonVariants } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  downloadUrl,
  getResults,
  getRun,
  isTerminal,
  listRuns,
  startRun,
  type ResultView,
  type ScreenerResults,
  type ScreenerRun,
} from "@/lib/screener-api"
import { DEFAULT_VISIBLE_COLUMNS } from "@/lib/screener-columns"
import { usePersistentState } from "@/lib/use-persistent-state"
import { cn } from "@/lib/utils"

const COLUMNS_STORAGE_KEY = "qq.discover.columns"
const POLL_INTERVAL_MS = 3000
/** The API always returns this window; it is not configurable per request. */
const HISTORY_DAYS = 14

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong."
}

function formatRunTime(value: string | null) {
  if (!value) return "Unknown time"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })
}

function runOptionLabel(run: ScreenerRun) {
  const counts =
    run.passed != null && run.scored != null
      ? ` · ${run.passed}/${run.scored}`
      : ""
  const prefix = run.legacy ? "Legacy · " : ""
  return `${prefix}${formatRunTime(run.startedAt)} · ${run.statusLabel}${counts}`
}

function StatusPill({ run }: { run: ScreenerRun }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
        run.status === "succeeded" && "bg-emerald-500/10 text-emerald-600",
        run.status === "failed" && "bg-destructive/10 text-destructive",
        run.status === "running" && "bg-amber-500/10 text-amber-600"
      )}
    >
      {run.status === "running" ? (
        <Loader2 className="size-3 animate-spin" aria-hidden />
      ) : null}
      {run.statusLabel}
    </span>
  )
}

export function DiscoverScreener() {
  const [runs, setRuns] = useState<ScreenerRun[]>([])
  const [runsError, setRunsError] = useState<string | null>(null)
  const [runsLoading, setRunsLoading] = useState(true)

  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [run, setRun] = useState<ScreenerRun | null>(null)
  const [runError, setRunError] = useState<string | null>(null)
  const [starting, setStarting] = useState(false)

  const [view, setView] = useState<ResultView>("candidates")
  const [results, setResults] = useState<ScreenerResults | null>(null)
  const [resultsLoading, setResultsLoading] = useState(false)
  const [resultsError, setResultsError] = useState<string | null>(null)

  const [search, setSearch] = useState("")
  const [visibleColumns, setVisibleColumns, resetVisibleColumns] =
    usePersistentState<string[]>(COLUMNS_STORAGE_KEY, DEFAULT_VISIBLE_COLUMNS)

  const searchId = useId()
  const historyId = useId()

  const refreshRuns = useCallback(async (autoSelect: boolean) => {
    setRunsLoading(true)
    try {
      const list = await listRuns()
      setRuns(list)
      setRunsError(null)
      if (autoSelect && list.length > 0) {
        setSelectedRunId((current) => current ?? list[0].id)
      }
    } catch (error) {
      setRunsError(errorMessage(error))
    } finally {
      setRunsLoading(false)
    }
  }, [])

  useEffect(() => {
    void refreshRuns(true)
  }, [refreshRuns])

  useEffect(() => {
    if (!selectedRunId) {
      setRun(null)
      return
    }

    const controller = new AbortController()
    let timer: number | undefined
    let cancelled = false

    const poll = async () => {
      try {
        const detail = await getRun(selectedRunId, controller.signal)
        if (cancelled) return
        setRun(detail)
        setRunError(null)
        // Keep the history entry in sync so labels, counts, and the in-progress
        // guard reflect the polled state without waiting for a list refresh.
        setRuns((current) =>
          current.map((item) => (item.id === detail.id ? detail : item))
        )
        if (isTerminal(detail.status)) {
          void refreshRuns(false)
        } else {
          timer = window.setTimeout(poll, POLL_INTERVAL_MS)
        }
      } catch (error) {
        if (cancelled) return
        setRunError(errorMessage(error))
      }
    }

    void poll()

    return () => {
      cancelled = true
      controller.abort()
      window.clearTimeout(timer)
    }
  }, [selectedRunId, refreshRuns])

  const runStatus = run?.status
  useEffect(() => {
    if (!selectedRunId || runStatus !== "succeeded") {
      setResults(null)
      return
    }

    const controller = new AbortController()
    setResultsLoading(true)

    getResults(selectedRunId, view, controller.signal)
      .then((payload) => {
        setResults(payload)
        setResultsError(null)
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return
        setResults(null)
        setResultsError(errorMessage(error))
      })
      .finally(() => {
        if (!controller.signal.aborted) setResultsLoading(false)
      })

    return () => controller.abort()
  }, [selectedRunId, runStatus, view])

  // The API allows one run at a time and answers 409 otherwise, so the button
  // stays disabled while any known run is still in flight.
  const activeRun = useMemo(() => {
    if (run?.status === "running") return run
    return runs.find((item) => item.status === "running") ?? null
  }, [run, runs])
  const startDisabled = starting || activeRun !== null

  async function handleStartRun() {
    setStarting(true)
    try {
      const created = await startRun()
      setRuns((current) => [
        created,
        ...current.filter((item) => item.id !== created.id),
      ])
      setSelectedRunId(created.id)
      setRun(created)
      setRunError(null)
    } catch (error) {
      setRunError(errorMessage(error))
      void refreshRuns(false)
    } finally {
      setStarting(false)
    }
  }

  const availableColumns = useMemo(() => results?.columns ?? [], [results])
  const displayColumns = useMemo(
    () => availableColumns.filter((column) => visibleColumns.includes(column)),
    [availableColumns, visibleColumns]
  )

  const filteredRows = useMemo(() => {
    const rows = results?.rows ?? []
    const query = search.trim().toLowerCase()
    if (!query) return rows
    return rows.filter((row) => {
      const ticker = row.ticker ?? row.symbol
      return String(ticker ?? "")
        .toLowerCase()
        .includes(query)
    })
  }, [results, search])

  const totalRows = results?.rowCount ?? 0

  return (
    <div className="mx-auto flex w-full max-w-[110rem] flex-col gap-5 px-4 py-5 sm:px-6 lg:px-8">
      <section
        aria-labelledby="run-controls-heading"
        className="border-border bg-muted/30 flex flex-col gap-3 rounded-xl border p-3 sm:p-4"
      >
        <h2 id="run-controls-heading" className="sr-only">
          Screener run controls
        </h2>

        <div className="flex flex-wrap items-end gap-3">
          <Button
            type="button"
            onClick={handleStartRun}
            disabled={startDisabled}
            title={
              activeRun
                ? "A screener run is already in progress"
                : "Start a new screener run"
            }
          >
            {startDisabled ? (
              <Loader2 className="animate-spin" aria-hidden />
            ) : (
              <Play aria-hidden />
            )}
            {activeRun ? "Run in progress" : "Run screener"}
          </Button>

          <div className="flex min-w-0 flex-1 flex-col gap-1 sm:max-w-sm">
            <label
              htmlFor={historyId}
              className="text-muted-foreground text-xs font-medium"
            >
              Run history (last {HISTORY_DAYS} days)
            </label>
            <select
              id={historyId}
              value={selectedRunId ?? ""}
              disabled={runs.length === 0}
              onChange={(event) => setSelectedRunId(event.target.value || null)}
              className="border-input focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-full rounded-md border bg-transparent px-3 text-sm shadow-xs outline-none focus-visible:ring-[3px] disabled:opacity-50"
            >
              {runs.length === 0 ? (
                <option value="">
                  {runsLoading ? "Loading runs…" : "No runs yet"}
                </option>
              ) : null}
              {runs.map((item) => (
                <option key={item.id} value={item.id}>
                  {runOptionLabel(item)}
                </option>
              ))}
            </select>
          </div>

          <Button
            type="button"
            variant="outline"
            size="icon"
            aria-label="Refresh run history"
            title="Refresh run history"
            onClick={() => void refreshRuns(true)}
            disabled={runsLoading}
          >
            <RefreshCw
              className={cn(runsLoading && "animate-spin")}
              aria-hidden
            />
          </Button>

          {run ? (
            <div className="flex items-center gap-2 text-sm">
              <StatusPill run={run} />
              {run.status === "succeeded" ? (
                <span className="text-muted-foreground tabular-nums">
                  {run.passed ?? 0} candidates / {run.scored ?? 0} scored
                  {run.skipped ? ` · ${run.skipped} skipped` : ""}
                </span>
              ) : null}
            </div>
          ) : null}
        </div>

        {runsError ? (
          <p role="alert" className="text-destructive text-sm">
            Could not load run history: {runsError}
          </p>
        ) : null}
        {runError ? (
          <p role="alert" className="text-destructive text-sm">
            {runError}
          </p>
        ) : null}
        {run?.status === "failed" ? (
          <p role="alert" className="text-destructive text-sm">
            Run failed{run.error ? `: ${run.error}` : "."}
          </p>
        ) : null}
      </section>

      <section
        aria-labelledby="results-heading"
        className="flex flex-col gap-3"
      >
        <div className="flex flex-wrap items-center gap-2">
          <h2
            id="results-heading"
            className="mr-auto text-base font-semibold tracking-tight"
          >
            Results
            {results ? (
              <span className="text-muted-foreground ml-2 text-sm font-normal tabular-nums">
                {filteredRows.length}
                {filteredRows.length !== totalRows ? ` of ${totalRows}` : ""}{" "}
                rows
              </span>
            ) : null}
          </h2>

          <div
            role="group"
            aria-label="Result view"
            className="border-input flex overflow-hidden rounded-md border"
          >
            {(["candidates", "all"] as const).map((option) => (
              <button
                key={option}
                type="button"
                aria-pressed={view === option}
                onClick={() => setView(option)}
                className={cn(
                  "focus-visible:ring-ring px-3 py-1.5 text-sm capitalize outline-none focus-visible:ring-2",
                  view === option
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-accent"
                )}
              >
                {option}
              </button>
            ))}
          </div>

          <div className="relative w-full sm:w-56">
            <label htmlFor={searchId} className="sr-only">
              Search by ticker
            </label>
            <Search
              className="text-muted-foreground pointer-events-none absolute top-1/2 left-2 size-4 -translate-y-1/2"
              aria-hidden
            />
            <Input
              id={searchId}
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search ticker…"
              className="h-9 pl-8"
            />
          </div>

          <ColumnVisibilityMenu
            columns={availableColumns}
            visibleColumns={visibleColumns}
            onReset={resetVisibleColumns}
            onToggle={(column, visible) =>
              setVisibleColumns((current) =>
                visible
                  ? [...current, column]
                  : current.filter((item) => item !== column)
              )
            }
          />

          <a
            href={selectedRunId ? downloadUrl(selectedRunId, view) : undefined}
            aria-disabled={!results}
            className={cn(
              buttonVariants({ variant: "outline", size: "sm" }),
              !results && "pointer-events-none opacity-50"
            )}
          >
            <Download aria-hidden />
            CSV
          </a>
        </div>

        <div className="border-border overflow-hidden rounded-xl border">
          {resultsError ? (
            <p role="alert" className="text-destructive p-6 text-sm">
              Could not load results: {resultsError}
            </p>
          ) : resultsLoading ? (
            <p className="text-muted-foreground flex items-center gap-2 p-6 text-sm">
              <Loader2 className="size-4 animate-spin" aria-hidden />
              Loading results…
            </p>
          ) : !selectedRunId ? (
            <p className="text-muted-foreground p-6 text-sm">
              No screener runs in the last {HISTORY_DAYS} days. Start a run to
              see results.
            </p>
          ) : run?.status === "running" ? (
            <p className="text-muted-foreground flex items-center gap-2 p-6 text-sm">
              <Loader2 className="size-4 animate-spin" aria-hidden />
              Screener is {run.statusLabel}. Results appear when it finishes.
            </p>
          ) : run?.status === "failed" ? (
            <p className="text-muted-foreground p-6 text-sm">
              This run failed, so it has no results.
            </p>
          ) : results ? (
            <ScreenerResultsTable
              columns={displayColumns}
              rows={filteredRows}
              emptyMessage={
                search
                  ? `No tickers match “${search}”.`
                  : view === "candidates"
                    ? "This run produced no candidates."
                    : "This run produced no rows."
              }
            />
          ) : (
            <p className="text-muted-foreground p-6 text-sm">
              No results available for this run.
            </p>
          )}
        </div>
      </section>
    </div>
  )
}
