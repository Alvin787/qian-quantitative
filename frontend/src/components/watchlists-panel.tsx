import { useEffect, useMemo, useState, type FormEvent } from "react"

import { StatusBadge } from "@/components/status-badge"
import { TokenPills, decodeDisplayText } from "@/components/token-pills"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { formatValue, humanizeToken } from "@/lib/screener-columns"
import { tradingViewUrl } from "@/lib/tradingview"
import { cn } from "@/lib/utils"
import {
  failReasonLabel,
  listLabel,
  READINESS_ORDER,
  screenFullLabel,
  screenShortLabel,
} from "@/lib/watchlists-display"
import {
  deleteName,
  fetchFunnel,
  getReview,
  moveName,
  startReview,
  upsertName,
  type FunnelName,
  type FunnelState,
} from "@/lib/watchlists-api"

type FunnelView = "tonight" | "master" | "stalk" | "focus" | "back"

const VIEWS: FunnelView[] = ["tonight", "master", "stalk", "focus", "back"]
const POLL_INTERVAL_MS = 3000

const GATES_NOTE =
  "Automated gates: ADR% ≥ 3, $ volume, biotech exclude, 10/20-MA stack, extension ≤ 4× ADR% from 50-MA, earnings ≥ 6 sessions, RS vs SPY, declining-200 room. Review highlights; it does not promote."

const CHART_NOTE =
  "Chart pass (you): VCP tightness, linearity, pivot/alert, leader in a leading group, catalytic-move quality, gap-up LoD exception. Volume dry-up and range compression are bonus flags only."

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong."
}

function listForAdd(view: FunnelView): Exclude<FunnelView, "tonight"> {
  return view === "tonight" ? "master" : view
}

function promoteTarget(list: string): string | null {
  if (list === "master") return "stalk"
  if (list === "stalk") return "focus"
  return null
}

function demoteTarget(list: string): string | null {
  if (list === "focus") return "stalk"
  if (list === "stalk") return "master"
  return null
}

function viewLabel(view: FunnelView) {
  return view === "tonight" ? "Tonight" : listLabel(view)
}

function readinessTone(
  readiness: string
): "positive" | "negative" | "neutral" {
  if (readiness === "focus_ready") return "positive"
  if (
    readiness === "disrupted" ||
    readiness === "earnings_blocked" ||
    readiness === "unknown"
  ) {
    return "negative"
  }
  return "neutral"
}

function formatExtension(value: number | null) {
  if (value == null || !Number.isFinite(value)) return "—"
  return `${formatValue(value)}×`
}

function namesForView(names: FunnelName[], view: FunnelView) {
  return names.filter((name) =>
    view === "tonight" ? name.queue_reason != null : name.list === view
  )
}

function FunnelViewTabs({
  view,
  counts,
  onChange,
}: {
  view: FunnelView
  counts: Record<FunnelView, number>
  onChange: (view: FunnelView) => void
}) {
  return (
    <div
      role="group"
      aria-label="Watchlist"
      className="border-input flex w-fit flex-wrap overflow-hidden rounded-md border"
    >
      {VIEWS.map((item) => {
        const selected = view === item
        return (
          <button
            key={item}
            type="button"
            aria-pressed={selected}
            onClick={() => onChange(item)}
            className={cn(
              "focus-visible:ring-ring flex items-center gap-1.5 px-3 py-1.5 text-sm outline-none focus-visible:ring-2",
              "transition-[color,background-color,transform] duration-[160ms] ease-[var(--ease-out)]",
              "active:scale-[0.98]",
              selected
                ? "bg-primary text-primary-foreground"
                : "hover:bg-accent"
            )}
          >
            {viewLabel(item)}
            <span
              className={cn(
                "tabular-nums text-xs",
                selected ? "opacity-80" : "text-muted-foreground"
              )}
            >
              {counts[item]}
            </span>
          </button>
        )
      })}
    </div>
  )
}

function ReadinessFilters({
  counts,
  selected,
  total,
  onToggle,
  onClear,
}: {
  counts: Map<string, number>
  selected: string[]
  total: number
  onToggle: (readiness: string) => void
  onClear: () => void
}) {
  const chips = READINESS_ORDER.filter(
    (readiness) =>
      selected.includes(readiness) || (counts.get(readiness) ?? 0) > 0
  )
  const showingAll = selected.length === 0

  if (chips.length === 0) return null

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="text-muted-foreground mr-1 text-xs font-medium tracking-wide">
        Show
      </span>
      <button
        type="button"
        aria-pressed={showingAll}
        onClick={onClear}
        className={cn(
          "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium",
          "transition-[color,background-color,transform] duration-[160ms] ease-[var(--ease-out)]",
          "active:scale-[0.97]",
          "focus-visible:ring-ring outline-none focus-visible:ring-2",
          showingAll
            ? "bg-primary text-primary-foreground"
            : "bg-muted/70 text-muted-foreground hover:bg-accent hover:text-accent-foreground"
        )}
      >
        All
        <span className="tabular-nums opacity-80">{total}</span>
      </button>
      {chips.map((readiness) => {
        const active = selected.includes(readiness)
        return (
          <button
            key={readiness}
            type="button"
            aria-pressed={active}
            onClick={() => onToggle(readiness)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium",
              "transition-[color,background-color,transform] duration-[160ms] ease-[var(--ease-out)]",
              "active:scale-[0.97]",
              "focus-visible:ring-ring outline-none focus-visible:ring-2",
              active
                ? "bg-primary text-primary-foreground"
                : "bg-muted/70 text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            )}
          >
            {humanizeToken(readiness)}
            <span className="tabular-nums opacity-80">
              {counts.get(readiness) ?? 0}
            </span>
          </button>
        )
      })}
    </div>
  )
}

export function WatchlistsPanel() {
  const [funnel, setFunnel] = useState<FunnelState | null>(null)
  const [view, setView] = useState<FunnelView>("tonight")
  const [ticker, setTicker] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [activeReviewId, setActiveReviewId] = useState<string | null>(null)
  const [readinessFilter, setReadinessFilter] = useState<string[]>([])

  async function refresh(signal?: AbortSignal) {
    try {
      const state = await fetchFunnel(signal)
      setFunnel(state)
      setError(null)
    } catch (err: unknown) {
      if (signal?.aborted) return
      if (err instanceof DOMException && err.name === "AbortError") return
      if (err instanceof Error && err.name === "AbortError") return
      setError(errorMessage(err))
    }
  }

  useEffect(() => {
    const controller = new AbortController()
    fetchFunnel(controller.signal)
      .then((state) => {
        setFunnel(state)
        setError(null)
        if (state.review.status === "running" && state.review.review_id) {
          setActiveReviewId(state.review.review_id)
        }
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return
        if (err instanceof DOMException && err.name === "AbortError") return
        if (err instanceof Error && err.name === "AbortError") return
        setError(errorMessage(err))
      })
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (!activeReviewId) return
    const reviewId = activeReviewId
    const controller = new AbortController()
    let cancelled = false
    let timer: ReturnType<typeof setTimeout> | undefined

    async function poll() {
      if (cancelled) return
      try {
        const meta = await getReview(reviewId, controller.signal)
        if (cancelled) return
        if (meta.status === "completed" || meta.status === "failed") {
          await refresh(controller.signal)
          if (!cancelled) setActiveReviewId(null)
          return
        }
      } catch (err: unknown) {
        if (cancelled) return
        if (controller.signal.aborted) return
        if (err instanceof DOMException && err.name === "AbortError") return
        if (err instanceof Error && err.name === "AbortError") return
        setError(errorMessage(err))
        return
      }
      timer = setTimeout(() => {
        void poll()
      }, POLL_INTERVAL_MS)
    }

    void poll()
    return () => {
      cancelled = true
      controller.abort()
      if (timer !== undefined) clearTimeout(timer)
    }
  }, [activeReviewId])

  const names = funnel?.names ?? []
  const viewCounts = useMemo(
    () => ({
      tonight: namesForView(names, "tonight").length,
      master: namesForView(names, "master").length,
      stalk: namesForView(names, "stalk").length,
      focus: namesForView(names, "focus").length,
      back: namesForView(names, "back").length,
    }),
    [names]
  )
  const inView = useMemo(() => namesForView(names, view), [names, view])
  const readinessCounts = useMemo(() => {
    const counts = new Map<string, number>()
    for (const name of inView) {
      counts.set(name.readiness, (counts.get(name.readiness) ?? 0) + 1)
    }
    return counts
  }, [inView])
  const visible = useMemo(
    () =>
      readinessFilter.length === 0
        ? inView
        : inView.filter((name) => readinessFilter.includes(name.readiness)),
    [inView, readinessFilter]
  )
  const showList = view === "tonight"
  const columnCount = showList ? 12 : 11
  const reviewDisabled =
    funnel?.review.status === "running" || activeReviewId != null

  async function onAdd(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    try {
      await upsertName({ ticker, list: listForAdd(view) })
      setTicker("")
      await refresh()
    } catch (err: unknown) {
      setError(errorMessage(err))
    }
  }

  async function onMove(name: FunnelName, list: string) {
    try {
      await moveName(name.ticker, list)
      await refresh()
    } catch (err: unknown) {
      setError(errorMessage(err))
    }
  }

  async function onRemove(name: FunnelName) {
    try {
      await deleteName(name.ticker)
      await refresh()
    } catch (err: unknown) {
      setError(errorMessage(err))
    }
  }

  async function onReview() {
    try {
      const meta = await startReview()
      if (meta.review_id) setActiveReviewId(meta.review_id)
      setError(null)
    } catch (err: unknown) {
      setError(errorMessage(err))
    }
  }

  function onCopy() {
    void navigator.clipboard.writeText(visible.map((n) => n.ticker).join(","))
  }

  function toggleReadiness(readiness: string) {
    setReadinessFilter((current) =>
      current.includes(readiness)
        ? current.filter((item) => item !== readiness)
        : [...current, readiness]
    )
  }

  return (
    <div className="mx-auto flex w-full max-w-[110rem] flex-col gap-5 px-4 py-5 sm:px-6 lg:px-8">
      <FunnelViewTabs view={view} counts={viewCounts} onChange={setView} />

      <div className="flex flex-wrap items-end gap-2">
        <form className="flex flex-wrap items-end gap-2" onSubmit={onAdd}>
          <Input
            value={ticker}
            onChange={(event) => setTicker(event.target.value)}
            name="ticker"
            placeholder="Ticker"
            className="h-8 w-32"
          />
          <Button type="submit" size="sm">
            Add
          </Button>
        </form>
        <Button type="button" size="sm" variant="outline" onClick={onCopy}>
          Copy tickers
        </Button>
        <Button
          type="button"
          size="sm"
          disabled={reviewDisabled}
          onClick={() => void onReview()}
        >
          Review
        </Button>
        {reviewDisabled ? (
          <span className="text-muted-foreground text-sm">Review running…</span>
        ) : null}
      </div>

      <ReadinessFilters
        counts={readinessCounts}
        selected={readinessFilter}
        total={inView.length}
        onToggle={toggleReadiness}
        onClear={() => setReadinessFilter([])}
      />

      <p className="text-muted-foreground text-sm">{GATES_NOTE}</p>
      <p className="text-muted-foreground text-sm">{CHART_NOTE}</p>

      {error ? (
        <p role="alert" className="text-destructive text-sm">
          {error}
        </p>
      ) : null}

      <div className="border-border bg-card/40 overflow-hidden rounded-xl border shadow-xs">
        <div className="border-border flex items-baseline justify-between gap-3 border-b px-4 py-3">
          <h2 className="display-tight text-lg font-semibold text-primary">
            {viewLabel(view)}
          </h2>
          <p className="text-muted-foreground text-sm tabular-nums">
            {visible.length}
            {visible.length !== inView.length ? ` of ${inView.length}` : ""}{" "}
            names
          </p>
        </div>
        <Table className="min-w-full text-xs sm:text-sm">
          <TableHeader className="bg-muted/50 sticky top-0 z-10">
            <TableRow>
              <TableHead className="px-2">Ticker</TableHead>
              {showList ? <TableHead className="px-2">List</TableHead> : null}
              <TableHead className="px-2">Industry</TableHead>
              <TableHead className="px-2">Source screens</TableHead>
              <TableHead className="px-2">Note</TableHead>
              <TableHead className="px-2">Readiness</TableHead>
              <TableHead className="px-2">Queue reason</TableHead>
              <TableHead className="px-2">Fail reasons</TableHead>
              <TableHead className="px-2 text-center">ADR%</TableHead>
              <TableHead className="px-2 text-center">Extension</TableHead>
              <TableHead className="px-2 text-center">
                Days to earnings
              </TableHead>
              <TableHead className="px-2">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {visible.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={columnCount}
                  className="text-muted-foreground h-24 text-center"
                >
                  {funnel == null && !error
                    ? "Loading watchlists…"
                    : inView.length === 0
                      ? `No names on ${viewLabel(view)}.`
                      : "No names match the selected filters."}
                </TableCell>
              </TableRow>
            ) : (
              visible.map((name) => {
                const promote = promoteTarget(name.list)
                const demote = demoteTarget(name.list)
                const tickerHref = tradingViewUrl(name.ticker)
                return (
                  <TableRow key={name.ticker}>
                    <TableCell className="px-2 py-1.5 font-medium">
                      {tickerHref ? (
                        <a
                          href={tickerHref}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-foreground underline decoration-muted-foreground/50 underline-offset-2 hover:decoration-foreground"
                          title={`Open ${name.ticker} on TradingView`}
                        >
                          {name.ticker}
                        </a>
                      ) : (
                        name.ticker
                      )}
                    </TableCell>
                    {showList ? (
                      <TableCell className="px-2 py-1.5">
                        <span className="bg-muted text-muted-foreground inline-flex rounded-md px-2 py-0.5 text-xs font-medium">
                          {listLabel(name.list)}
                        </span>
                      </TableCell>
                    ) : null}
                    <TableCell className="max-w-[12rem] truncate px-2 py-1.5">
                      {name.industry ? decodeDisplayText(name.industry) : "—"}
                    </TableCell>
                    <TableCell className="max-w-sm px-2 py-1.5 whitespace-normal">
                      <TokenPills
                        items={name.source_screens}
                        variant="neutral"
                        labelFor={screenShortLabel}
                        titleFor={screenFullLabel}
                      />
                    </TableCell>
                    <TableCell className="max-w-[12rem] truncate px-2 py-1.5">
                      {name.note || (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell className="px-2 py-1.5">
                      <StatusBadge
                        tone={readinessTone(name.readiness)}
                        label={humanizeToken(name.readiness)}
                      />
                    </TableCell>
                    <TableCell className="px-2 py-1.5">
                      {name.queue_reason ? (
                        <StatusBadge
                          tone="neutral"
                          label={humanizeToken(name.queue_reason)}
                        />
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell className="max-w-sm px-2 py-1.5 whitespace-normal">
                      <TokenPills
                        items={name.fail_reasons.split(";")}
                        variant="failure"
                        labelFor={failReasonLabel}
                      />
                    </TableCell>
                    <TableCell className="px-2 py-1.5 text-center tabular-nums">
                      {formatValue(name.gates.adr_pct)}
                    </TableCell>
                    <TableCell className="px-2 py-1.5 text-center tabular-nums">
                      {formatExtension(name.gates.extension_x)}
                    </TableCell>
                    <TableCell className="px-2 py-1.5 text-center tabular-nums">
                      {formatValue(name.gates.days_to_earnings)}
                    </TableCell>
                    <TableCell className="px-2 py-1.5">
                      <div className="flex flex-wrap gap-1">
                        {promote ? (
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            onClick={() => void onMove(name, promote)}
                          >
                            Promote
                          </Button>
                        ) : null}
                        {demote ? (
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            onClick={() => void onMove(name, demote)}
                          >
                            Demote
                          </Button>
                        ) : null}
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          onClick={() => void onMove(name, "back")}
                        >
                          To back
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="ghost"
                          onClick={() => void onRemove(name)}
                        >
                          Remove
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
