import {
  useEffect,
  useMemo,
  useState,
  type ComponentProps,
  type FormEvent,
} from "react"
import { Plus, Trash2 } from "lucide-react"

import { StatusBadge } from "@/components/status-badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  createTrade,
  deleteTrade,
  fetchLedger,
  updateTrade,
  type Trade,
  type TradeInput,
} from "@/lib/pnl-api"
import { tradingViewUrl } from "@/lib/tradingview"
import { usePersistentState } from "@/lib/use-persistent-state"
import { cn } from "@/lib/utils"

type StatusFilter = "all" | "open" | "closed"

type Draft = {
  ticker: string
  entry_date: string
  exit_date: string
  entry_price: string
  exit_price: string
  shares: string
  notes: string
  account: string
}

const FILTERS: { id: StatusFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "open", label: "Open" },
  { id: "closed", label: "Closed" },
]

const EMPTY_TRADES: Trade[] = []

const cellInputClass =
  "h-8 min-w-0 border-transparent bg-transparent px-1.5 shadow-none md:text-sm"

function CellInput({
  className,
  onCommit,
  ...props
}: ComponentProps<typeof Input> & { onCommit: () => void }) {
  return (
    <Input
      {...props}
      className={cn(cellInputClass, className)}
      onBlur={() => onCommit()}
      onKeyDown={(event) => {
        if (event.key === "Enter") event.currentTarget.blur()
      }}
    />
  )
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong."
}

function todayIso() {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, "0")
  const day = String(now.getDate()).padStart(2, "0")
  return `${now.getFullYear()}-${month}-${day}`
}

function emptyDraft(account: string): Draft {
  return {
    ticker: "",
    entry_date: todayIso(),
    exit_date: "",
    entry_price: "",
    exit_price: "",
    shares: "",
    notes: "",
    account,
  }
}

function tradeToDraft(trade: Trade): Draft {
  return {
    ticker: trade.ticker,
    entry_date: trade.entry_date,
    exit_date: trade.exit_date ?? "",
    entry_price: String(trade.entry_price),
    exit_price: trade.exit_price == null ? "" : String(trade.exit_price),
    shares: String(trade.shares),
    notes: trade.notes,
    account: trade.account,
  }
}

function parseNumber(raw: string): number | null {
  const trimmed = raw.trim()
  if (!trimmed) return null
  const value = Number(trimmed)
  return Number.isFinite(value) ? value : null
}

function draftToInput(draft: Draft): TradeInput {
  const entryPrice = parseNumber(draft.entry_price)
  const shares = parseNumber(draft.shares)
  if (!draft.ticker.trim()) throw new Error("Enter a ticker.")
  if (!draft.entry_date) throw new Error("Enter an entry date.")
  if (entryPrice == null) throw new Error("Enter a valid entry price.")
  if (shares == null) throw new Error("Enter a valid share count.")
  return {
    ticker: draft.ticker.trim(),
    entry_date: draft.entry_date,
    entry_price: entryPrice,
    shares,
    exit_date: draft.exit_date.trim() || null,
    exit_price: parseNumber(draft.exit_price),
    notes: draft.notes,
    account: draft.account.trim(),
  }
}

function sameInput(trade: Trade, input: TradeInput) {
  return (
    trade.ticker === input.ticker.toUpperCase() &&
    trade.entry_date === input.entry_date &&
    trade.entry_price === input.entry_price &&
    trade.shares === input.shares &&
    (trade.exit_date ?? null) === (input.exit_date ?? null) &&
    (trade.exit_price ?? null) === (input.exit_price ?? null) &&
    trade.notes === (input.notes ?? "") &&
    trade.account === (input.account ?? "")
  )
}

function formatMoney(value: number | null) {
  if (value == null || !Number.isFinite(value)) return "—"
  return value.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function formatSignedMoney(value: number | null) {
  if (value == null || !Number.isFinite(value)) return "—"
  const formatted = formatMoney(Math.abs(value))
  if (value > 0) return `+${formatted}`
  if (value < 0) return `−${formatted}`
  return formatted
}

function formatPercent(value: number | null) {
  if (value == null || !Number.isFinite(value)) return "—"
  const sign = value > 0 ? "+" : value < 0 ? "−" : ""
  return `${sign}${Math.abs(value).toFixed(2)}%`
}

function pnlClass(value: number | null) {
  if (value == null || value === 0) return "text-muted-foreground"
  return value > 0
    ? "text-emerald-700 dark:text-emerald-300"
    : "text-red-700 dark:text-red-300"
}

function uniqueAccounts(trades: Trade[]) {
  const seen = new Set<string>()
  const accounts: string[] = []
  for (const trade of trades) {
    const account = trade.account.trim()
    if (!account || seen.has(account)) continue
    seen.add(account)
    accounts.push(account)
  }
  return accounts
}

function FilterChips({
  filter,
  counts,
  onChange,
}: {
  filter: StatusFilter
  counts: Record<StatusFilter, number>
  onChange: (filter: StatusFilter) => void
}) {
  return (
    <div
      role="group"
      aria-label="Trade status"
      className="border-input flex w-fit overflow-hidden rounded-md border"
    >
      {FILTERS.map((item) => {
        const selected = filter === item.id
        return (
          <button
            key={item.id}
            type="button"
            aria-pressed={selected}
            onClick={() => onChange(item.id)}
            className={cn(
              "focus-visible:ring-ring flex items-center gap-1.5 px-3 py-1.5 text-sm outline-none focus-visible:ring-2",
              "transition-[color,background-color,transform] duration-[160ms] ease-[var(--ease-out)]",
              "active:scale-[0.98]",
              selected
                ? "bg-primary text-primary-foreground"
                : "hover:bg-accent"
            )}
          >
            {item.label}
            <span
              className={cn(
                "tabular-nums text-xs",
                selected ? "opacity-80" : "text-muted-foreground"
              )}
            >
              {counts[item.id]}
            </span>
          </button>
        )
      })}
    </div>
  )
}

function SummaryCard({
  label,
  value,
  hint,
  valueClassName,
}: {
  label: string
  value: string
  hint?: string
  valueClassName?: string
}) {
  return (
    <div className="border-border bg-card/70 min-w-[10rem] flex-1 rounded-xl border px-4 py-3 shadow-xs">
      <p className="text-muted-foreground text-xs font-medium tracking-[0.12em] uppercase">
        {label}
      </p>
      <p
        className={cn(
          "display-tight mt-1 text-2xl font-semibold tabular-nums tracking-tight",
          valueClassName
        )}
      >
        {value}
      </p>
      {hint ? (
        <p className="text-muted-foreground mt-1 text-xs">{hint}</p>
      ) : null}
    </div>
  )
}

function TradeRow({
  trade,
  accountsId,
  onSave,
  onDelete,
}: {
  trade: Trade
  accountsId: string
  onSave: (id: string, input: TradeInput) => Promise<void>
  onDelete: (id: string) => Promise<void>
}) {
  const [draft, setDraft] = useState(() => tradeToDraft(trade))
  const [busy, setBusy] = useState(false)
  const tickerHref = tradingViewUrl(trade.ticker)

  useEffect(() => {
    setDraft(tradeToDraft(trade))
  }, [trade])

  function setField<K extends keyof Draft>(field: K, value: Draft[K]) {
    setDraft((current) => ({ ...current, [field]: value }))
  }

  async function commit() {
    let input: TradeInput
    try {
      input = draftToInput(draft)
    } catch {
      setDraft(tradeToDraft(trade))
      return
    }
    if (sameInput(trade, input)) return
    setBusy(true)
    try {
      await onSave(trade.id, input)
    } finally {
      setBusy(false)
    }
  }

  return (
    <TableRow className={cn(busy && "opacity-70")}>
      <TableCell className="px-2 py-1.5">
        <div className="flex items-center gap-2">
          <CellInput
            aria-label={`${trade.ticker} ticker`}
            value={draft.ticker}
            onChange={(event) =>
              setField("ticker", event.target.value.toUpperCase())
            }
            onCommit={() => void commit()}
            className="w-[5.5rem] font-medium uppercase"
          />
          <StatusBadge
            tone={trade.status === "closed" ? "neutral" : "positive"}
            label={trade.status === "closed" ? "Closed" : "Open"}
          />
          {tickerHref ? (
            <a
              href={tickerHref}
              target="_blank"
              rel="noopener noreferrer"
              className="text-muted-foreground hover:text-foreground text-xs underline decoration-muted-foreground/50 underline-offset-2"
              title={`Open ${trade.ticker} on TradingView`}
            >
              TV
            </a>
          ) : null}
        </div>
      </TableCell>
      <TableCell className="px-2 py-1.5">
        <CellInput
          type="date"
          aria-label={`${trade.ticker} entry date`}
          value={draft.entry_date}
          onChange={(event) => setField("entry_date", event.target.value)}
          onCommit={() => void commit()}
          className="w-[9.75rem]"
        />
      </TableCell>
      <TableCell className="px-2 py-1.5">
        <CellInput
          type="date"
          aria-label={`${trade.ticker} exit date`}
          value={draft.exit_date}
          onChange={(event) => setField("exit_date", event.target.value)}
          onCommit={() => void commit()}
          className="w-[9.75rem]"
        />
      </TableCell>
      <TableCell className="px-2 py-1.5">
        <CellInput
          inputMode="decimal"
          aria-label={`${trade.ticker} entry price`}
          value={draft.entry_price}
          onChange={(event) => setField("entry_price", event.target.value)}
          onCommit={() => void commit()}
          className="w-[5.5rem] text-right tabular-nums"
        />
      </TableCell>
      <TableCell className="px-2 py-1.5">
        <CellInput
          inputMode="decimal"
          aria-label={`${trade.ticker} exit price`}
          value={draft.exit_price}
          onChange={(event) => setField("exit_price", event.target.value)}
          onCommit={() => void commit()}
          className="w-[5.5rem] text-right tabular-nums"
        />
      </TableCell>
      <TableCell className="px-2 py-1.5">
        <CellInput
          inputMode="decimal"
          aria-label={`${trade.ticker} shares`}
          value={draft.shares}
          onChange={(event) => setField("shares", event.target.value)}
          onCommit={() => void commit()}
          className="w-[4.5rem] text-right tabular-nums"
        />
      </TableCell>
      <TableCell className="text-muted-foreground px-2 py-1.5 text-right tabular-nums">
        {formatMoney(trade.value)}
      </TableCell>
      <TableCell
        className={cn(
          "px-2 py-1.5 text-right font-medium tabular-nums",
          pnlClass(trade.pnl)
        )}
      >
        {formatSignedMoney(trade.pnl)}
      </TableCell>
      <TableCell
        className={cn(
          "px-2 py-1.5 text-right tabular-nums",
          pnlClass(trade.percent)
        )}
      >
        {formatPercent(trade.percent)}
      </TableCell>
      <TableCell className="px-2 py-1.5">
        <textarea
          aria-label={`${trade.ticker} notes`}
          value={draft.notes}
          rows={2}
          onChange={(event) => setField("notes", event.target.value)}
          onBlur={() => void commit()}
          className={cn(
            "placeholder:text-muted-foreground w-full min-w-[14rem] resize-y rounded-md border border-transparent bg-transparent px-1.5 py-1 text-sm outline-none",
            "focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
          )}
        />
      </TableCell>
      <TableCell className="px-2 py-1.5">
        <CellInput
          aria-label={`${trade.ticker} account`}
          list={accountsId}
          value={draft.account}
          onChange={(event) => setField("account", event.target.value)}
          onCommit={() => void commit()}
          className="w-[6.5rem]"
        />
      </TableCell>
      <TableCell className="px-2 py-1.5">
        <Button
          type="button"
          size="icon"
          variant="ghost"
          aria-label={`Delete ${trade.ticker}`}
          disabled={busy}
          onClick={() => void onDelete(trade.id)}
        >
          <Trash2 aria-hidden />
        </Button>
      </TableCell>
    </TableRow>
  )
}

export function PnlPanel() {
  const [ledger, setLedger] = useState<Awaited<
    ReturnType<typeof fetchLedger>
  > | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<StatusFilter>("all")
  const [accountFilter, setAccountFilter] = useState<string>("all")
  const [lastAccount, setLastAccount] = usePersistentState("qq.pnl.account", "")
  const [draft, setDraft] = useState(() => emptyDraft(lastAccount))
  const [adding, setAdding] = useState(false)
  const accountsId = "pnl-account-options"

  async function refresh(signal?: AbortSignal) {
    const next = await fetchLedger(signal)
    setLedger(next)
    setError(null)
  }

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    refresh(controller.signal)
      .catch((err: unknown) => {
        if (controller.signal.aborted) return
        if (err instanceof DOMException && err.name === "AbortError") return
        if (err instanceof Error && err.name === "AbortError") return
        setError(errorMessage(err))
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [])

  const trades = ledger?.trades ?? EMPTY_TRADES
  const accounts = useMemo(() => uniqueAccounts(trades), [trades])
  const visible = useMemo(() => {
    return trades.filter((trade) => {
      if (filter !== "all" && trade.status !== filter) return false
      if (accountFilter !== "all" && trade.account !== accountFilter) {
        return false
      }
      return true
    })
  }, [accountFilter, filter, trades])
  const visiblePnl = visible.reduce(
    (sum, trade) => sum + (trade.pnl ?? 0),
    0
  )

  async function onAdd(event: FormEvent) {
    event.preventDefault()
    setAdding(true)
    try {
      const input = draftToInput(draft)
      await createTrade(input)
      setLastAccount(input.account ?? "")
      setDraft(emptyDraft(input.account ?? ""))
      await refresh()
    } catch (err: unknown) {
      setError(errorMessage(err))
    } finally {
      setAdding(false)
    }
  }

  async function onSave(id: string, input: TradeInput) {
    try {
      await updateTrade(id, input)
      await refresh()
    } catch (err: unknown) {
      setError(errorMessage(err))
    }
  }

  async function onDelete(id: string) {
    try {
      await deleteTrade(id)
      await refresh()
    } catch (err: unknown) {
      setError(errorMessage(err))
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-[110rem] flex-col gap-5 px-4 py-5 sm:px-6 lg:px-8">
      <div className="flex flex-wrap gap-3">
        <SummaryCard
          label="Total PnL"
          value={formatSignedMoney(ledger?.total_pnl ?? 0)}
          hint="Realized closes only"
          valueClassName={pnlClass(ledger?.total_pnl ?? 0)}
        />
        <SummaryCard
          label="Open"
          value={String(ledger?.open_count ?? 0)}
          hint={`${formatMoney(ledger?.open_value ?? 0)} cost`}
        />
        <SummaryCard
          label="Closed"
          value={String(ledger?.closed_count ?? 0)}
          hint="Included in total PnL"
        />
      </div>

      <form
        onSubmit={onAdd}
        className="border-border bg-card/70 flex flex-col gap-3 rounded-xl border p-4 shadow-xs"
      >
        <div className="flex items-center justify-between gap-3">
          <h2 className="display-tight text-sm font-semibold">Add trade</h2>
          <p className="text-muted-foreground text-xs">
            Leave exit blank for an open position. Value, PnL, and percent fill
            in automatically.
          </p>
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <label className="flex min-w-[6rem] flex-col gap-1 text-xs">
            <span className="text-muted-foreground">Stock</span>
            <Input
              value={draft.ticker}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  ticker: event.target.value.toUpperCase(),
                }))
              }
              name="ticker"
              placeholder="RBLX"
              className="h-8 w-24 uppercase"
              required
            />
          </label>
          <label className="flex flex-col gap-1 text-xs">
            <span className="text-muted-foreground">Entry date</span>
            <Input
              type="date"
              value={draft.entry_date}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  entry_date: event.target.value,
                }))
              }
              className="h-8 w-[9.75rem]"
              required
            />
          </label>
          <label className="flex flex-col gap-1 text-xs">
            <span className="text-muted-foreground">Exit date</span>
            <Input
              type="date"
              value={draft.exit_date}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  exit_date: event.target.value,
                }))
              }
              className="h-8 w-[9.75rem]"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs">
            <span className="text-muted-foreground">Entry price</span>
            <Input
              inputMode="decimal"
              value={draft.entry_price}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  entry_price: event.target.value,
                }))
              }
              placeholder="34.56"
              className="h-8 w-24"
              required
            />
          </label>
          <label className="flex flex-col gap-1 text-xs">
            <span className="text-muted-foreground">Exit price</span>
            <Input
              inputMode="decimal"
              value={draft.exit_price}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  exit_price: event.target.value,
                }))
              }
              placeholder="—"
              className="h-8 w-24"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs">
            <span className="text-muted-foreground">Shares</span>
            <Input
              inputMode="decimal"
              value={draft.shares}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  shares: event.target.value,
                }))
              }
              placeholder="100"
              className="h-8 w-20"
              required
            />
          </label>
          <label className="flex min-w-[8rem] flex-1 flex-col gap-1 text-xs">
            <span className="text-muted-foreground">Notes</span>
            <Input
              value={draft.notes}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  notes: event.target.value,
                }))
              }
              placeholder="Setup, thesis, mistakes"
              className="h-8"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs">
            <span className="text-muted-foreground">Account</span>
            <Input
              list={accountsId}
              value={draft.account}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  account: event.target.value,
                }))
              }
              placeholder="401k"
              className="h-8 w-28"
            />
          </label>
          <Button type="submit" size="sm" disabled={adding}>
            <Plus aria-hidden />
            Add
          </Button>
        </div>
      </form>

      <div className="flex flex-wrap items-center gap-3">
        <FilterChips
          filter={filter}
          counts={{
            all: trades.length,
            open: trades.filter((trade) => trade.status === "open").length,
            closed: trades.filter((trade) => trade.status === "closed").length,
          }}
          onChange={setFilter}
        />
        {accounts.length > 1 ? (
          <label className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground text-xs">Account</span>
            <select
              value={accountFilter}
              onChange={(event) => setAccountFilter(event.target.value)}
              className="border-input bg-background/70 focus-visible:border-ring focus-visible:ring-ring/50 h-8 rounded-md border px-2 text-sm shadow-xs outline-none focus-visible:ring-[3px]"
            >
              <option value="all">All</option>
              {accounts.map((account) => (
                <option key={account} value={account}>
                  {account}
                </option>
              ))}
            </select>
          </label>
        ) : null}
      </div>

      {error ? (
        <p role="alert" className="text-destructive text-sm">
          {error}
        </p>
      ) : null}

      <datalist id={accountsId}>
        {accounts.map((account) => (
          <option key={account} value={account} />
        ))}
      </datalist>

      <div className="border-border bg-card/40 overflow-hidden rounded-xl border shadow-xs">
        <Table className="min-w-full text-xs sm:text-sm">
          <TableHeader className="bg-muted/50 sticky top-0 z-10">
            <TableRow>
              <TableHead className="px-2">Stock</TableHead>
              <TableHead className="px-2">Entry date</TableHead>
              <TableHead className="px-2">Exit date</TableHead>
              <TableHead className="px-2 text-right">Entry price</TableHead>
              <TableHead className="px-2 text-right">Exit price</TableHead>
              <TableHead className="px-2 text-right">Shares</TableHead>
              <TableHead className="px-2 text-right">Value</TableHead>
              <TableHead className="px-2 text-right">PnL</TableHead>
              <TableHead className="px-2 text-right">Percent</TableHead>
              <TableHead className="px-2">Notes</TableHead>
              <TableHead className="px-2">Account</TableHead>
              <TableHead className="px-2">
                <span className="sr-only">Actions</span>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {visible.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={12}
                  className="text-muted-foreground h-24 text-center"
                >
                  {loading
                    ? "Loading trades…"
                    : trades.length === 0
                      ? "No trades yet. Add an entry above."
                      : "No trades match the current filters."}
                </TableCell>
              </TableRow>
            ) : (
              visible.map((trade) => (
                <TradeRow
                  key={trade.id}
                  trade={trade}
                  accountsId={accountsId}
                  onSave={onSave}
                  onDelete={onDelete}
                />
              ))
            )}
          </TableBody>
          {visible.length > 0 && filter !== "open" ? (
            <TableFooter>
              <TableRow>
                <TableCell colSpan={7} className="px-2 py-2 text-right">
                  Realized PnL
                </TableCell>
                <TableCell
                  className={cn(
                    "px-2 py-2 text-right font-semibold tabular-nums",
                    pnlClass(visiblePnl)
                  )}
                >
                  {formatSignedMoney(visiblePnl)}
                </TableCell>
                <TableCell colSpan={4} />
              </TableRow>
            </TableFooter>
          ) : null}
        </Table>
      </div>
    </div>
  )
}
