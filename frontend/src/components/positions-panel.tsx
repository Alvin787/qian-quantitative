import { useState, type FormEvent } from "react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  computePositionPlan,
  computePositionSize,
  type PlanResponse,
  type SizeResponse,
} from "@/lib/positions-api"
import { usePersistentState } from "@/lib/use-persistent-state"

type Method = "fixed_pct" | "kelly" | "half_kelly"

function parseOptionalFloat(raw: string): number | null {
  const trimmed = raw.trim()
  if (!trimmed) return null
  const value = Number(trimmed)
  return Number.isFinite(value) ? value : null
}

export function PositionsPanel() {
  const [equity, setEquity] = usePersistentState("qq.positions.equity", "")
  const [entryPrice, setEntryPrice] = useState("")
  const [finalStop, setFinalStop] = useState("")
  const [method, setMethod] = useState<Method>("fixed_pct")
  const [riskPct, setRiskPct] = useState("0.5")
  const [maxRiskPct, setMaxRiskPct] = useState("1.0")
  const [winRate, setWinRate] = useState("")
  const [avgWinR, setAvgWinR] = useState("")
  const [avgLossR, setAvgLossR] = useState("")
  const [adrPct, setAdrPct] = useState("")
  const [result, setResult] = useState<SizeResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const [mgmtShares, setMgmtShares] = useState("")
  const [mgmtEntryPrice, setMgmtEntryPrice] = useState("")
  const [mgmtFinalStop, setMgmtFinalStop] = useState("")
  const [mgmtEntryDate, setMgmtEntryDate] = useState("")
  const [mgmtAsOfDate, setMgmtAsOfDate] = useState("")
  const [mgmtCurrentPrice, setMgmtCurrentPrice] = useState("")
  const [shave2rTaken, setShave2rTaken] = useState(false)
  const [day3PartialTaken, setDay3PartialTaken] = useState(false)
  const [consolidatedToBe, setConsolidatedToBe] = useState(false)
  const [ma10, setMa10] = useState("")
  const [ma50, setMa50] = useState("")
  const [atrPct, setAtrPct] = useState("")
  const [closeBelow10maDate, setCloseBelow10maDate] = useState("")
  const [orl, setOrl] = useState("")
  const [stops33Hit, setStops33Hit] = useState(false)
  const [stops66Hit, setStops66Hit] = useState(false)
  const [priorDayHigh, setPriorDayHigh] = useState("")
  const [rescaleAlertTriggered, setRescaleAlertTriggered] = useState(false)
  const [sidewaysConsolidation, setSidewaysConsolidation] = useState(false)
  const [extensionOverride, setExtensionOverride] = useState("")
  const [planResult, setPlanResult] = useState<PlanResponse | null>(null)
  const [planError, setPlanError] = useState<string | null>(null)
  const [planLoading, setPlanLoading] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const equityNum = Number(equity)
      const entryNum = Number(entryPrice)
      const stopNum = Number(finalStop)
      const maxRiskNum = Number(maxRiskPct)
      if (
        !Number.isFinite(equityNum) ||
        !Number.isFinite(entryNum) ||
        !Number.isFinite(stopNum) ||
        !Number.isFinite(maxRiskNum)
      ) {
        throw new Error("Enter valid numbers for equity, entry, stop, and max risk %.")
      }

      const body = {
        equity: equityNum,
        entry_price: entryNum,
        final_stop: stopNum,
        method,
        max_risk_pct: maxRiskNum,
        risk_pct:
          method === "fixed_pct" ? Number(riskPct) : undefined,
        win_rate:
          method === "fixed_pct" ? undefined : parseOptionalFloat(winRate),
        avg_win_r:
          method === "fixed_pct" ? undefined : parseOptionalFloat(avgWinR),
        avg_loss_r:
          method === "fixed_pct" ? undefined : parseOptionalFloat(avgLossR),
        adr_pct: parseOptionalFloat(adrPct),
      }

      const response = await computePositionSize(body)
      setResult(response)
    } catch (err: unknown) {
      setResult(null)
      setError(err instanceof Error ? err.message : "Something went wrong.")
    } finally {
      setLoading(false)
    }
  }

  function useSizingResult() {
    if (!result) return
    setMgmtShares(String(result.shares))
    setMgmtEntryPrice(String(result.entry_price))
    setMgmtFinalStop(String(result.final_stop))
  }

  async function onPlanSubmit(event: FormEvent) {
    event.preventDefault()
    setPlanError(null)
    setPlanLoading(true)
    try {
      const sharesNum = Number(mgmtShares)
      const entryNum = Number(mgmtEntryPrice)
      const stopNum = Number(mgmtFinalStop)
      if (
        !Number.isFinite(sharesNum) ||
        !Number.isFinite(entryNum) ||
        !Number.isFinite(stopNum) ||
        !mgmtEntryDate.trim() ||
        !mgmtAsOfDate.trim()
      ) {
        throw new Error(
          "Enter valid shares, entry, stop, entry date, and as-of date."
        )
      }

      const response = await computePositionPlan({
        shares: Math.trunc(sharesNum),
        entry_price: entryNum,
        final_stop: stopNum,
        entry_date: mgmtEntryDate.trim(),
        as_of_date: mgmtAsOfDate.trim(),
        current_price: parseOptionalFloat(mgmtCurrentPrice),
        shave_2r_taken: shave2rTaken,
        day3_partial_taken: day3PartialTaken,
        consolidated_to_be: consolidatedToBe,
        ma10: parseOptionalFloat(ma10),
        ma50: parseOptionalFloat(ma50),
        atr_pct: parseOptionalFloat(atrPct),
        close_below_10ma_date: closeBelow10maDate.trim() || null,
        orl: parseOptionalFloat(orl),
        stops_33_hit: stops33Hit,
        stops_66_hit: stops66Hit,
        prior_day_high: parseOptionalFloat(priorDayHigh),
        rescale_alert_triggered: rescaleAlertTriggered,
        sideways_consolidation: sidewaysConsolidation,
        extension_override: parseOptionalFloat(extensionOverride),
      })
      setPlanResult(response)
    } catch (err: unknown) {
      setPlanResult(null)
      setPlanError(err instanceof Error ? err.message : "Something went wrong.")
    } finally {
      setPlanLoading(false)
    }
  }

  return (
    <div className="mx-auto w-full max-w-7xl p-4 sm:p-6 lg:p-8">
      <div className="grid items-start gap-6 xl:grid-cols-[minmax(21rem,0.85fr)_minmax(0,1.15fr)]">
        <section className="border-border bg-card/70 flex flex-col gap-5 rounded-2xl border p-4 shadow-sm sm:p-6">
          <header className="flex items-start gap-3">
            <span className="bg-primary text-primary-foreground flex size-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold tabular-nums">
              1
            </span>
            <div className="min-w-0">
              <p className="text-muted-foreground text-xs font-medium tracking-[0.12em] uppercase">
                Prepare the trade
              </p>
              <h2 className="display-tight mt-1 text-lg font-semibold">
                Position sizing
              </h2>
              <p className="text-muted-foreground mt-1 text-sm">
                Set risk before committing capital.
              </p>
            </div>
          </header>

          <form onSubmit={onSubmit} className="grid gap-3 sm:grid-cols-2">
            <label className="flex flex-col gap-1.5 text-sm sm:col-span-2">
              <span className="text-muted-foreground">Portfolio equity</span>
              <Input
                type="text"
                inputMode="decimal"
                value={equity}
                onChange={(e) => setEquity(e.target.value)}
                required
              />
            </label>

            <label className="flex flex-col gap-1.5 text-sm">
              <span className="text-muted-foreground">Entry price</span>
              <Input
                type="text"
                inputMode="decimal"
                value={entryPrice}
                onChange={(e) => setEntryPrice(e.target.value)}
                required
              />
            </label>

            <label className="flex flex-col gap-1.5 text-sm">
              <span className="text-muted-foreground">Final stop (LoD)</span>
              <Input
                type="text"
                inputMode="decimal"
                value={finalStop}
                onChange={(e) => setFinalStop(e.target.value)}
                required
              />
            </label>

            <label className="flex flex-col gap-1.5 text-sm">
              <span className="text-muted-foreground">Sizing method</span>
              <select
                className="border-input bg-background/70 focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-full rounded-md border px-3 text-sm shadow-xs outline-none focus-visible:ring-[3px]"
                value={method}
                onChange={(e) => setMethod(e.target.value as Method)}
              >
                <option value="fixed_pct">Fixed %</option>
                <option value="kelly">Kelly</option>
                <option value="half_kelly">Half Kelly</option>
              </select>
            </label>

            <label className="flex flex-col gap-1.5 text-sm">
              <span className="text-muted-foreground">Max risk %</span>
              <Input
                type="text"
                inputMode="decimal"
                value={maxRiskPct}
                onChange={(e) => setMaxRiskPct(e.target.value)}
                required
              />
            </label>

            {method === "fixed_pct" ? (
              <label className="flex flex-col gap-1.5 text-sm">
                <span className="text-muted-foreground">Risk %</span>
                <Input
                  type="text"
                  inputMode="decimal"
                  value={riskPct}
                  onChange={(e) => setRiskPct(e.target.value)}
                  required
                />
              </label>
            ) : null}

            <label className="flex flex-col gap-1.5 text-sm">
              <span className="text-muted-foreground">ADR% (optional)</span>
              <Input
                type="text"
                inputMode="decimal"
                value={adrPct}
                onChange={(e) => setAdrPct(e.target.value)}
              />
            </label>

            {method === "kelly" || method === "half_kelly" ? (
              <div className="border-border bg-muted/30 grid gap-3 rounded-xl border p-3 sm:col-span-2 sm:grid-cols-3">
                <p className="text-muted-foreground text-xs font-medium sm:col-span-3">
                  Historical edge inputs
                </p>
                <label className="flex flex-col gap-1.5 text-sm">
                  <span className="text-muted-foreground">Win rate</span>
                  <Input
                    type="text"
                    inputMode="decimal"
                    value={winRate}
                    onChange={(e) => setWinRate(e.target.value)}
                    required
                  />
                </label>
                <label className="flex flex-col gap-1.5 text-sm">
                  <span className="text-muted-foreground">Avg win R</span>
                  <Input
                    type="text"
                    inputMode="decimal"
                    value={avgWinR}
                    onChange={(e) => setAvgWinR(e.target.value)}
                    required
                  />
                </label>
                <label className="flex flex-col gap-1.5 text-sm">
                  <span className="text-muted-foreground">Avg loss R</span>
                  <Input
                    type="text"
                    inputMode="decimal"
                    value={avgLossR}
                    onChange={(e) => setAvgLossR(e.target.value)}
                    required
                  />
                </label>
              </div>
            ) : null}

            <div className="pt-1 sm:col-span-2">
              <Button type="submit" disabled={loading} className="w-full sm:w-auto">
                {loading ? "Calculating…" : "Calculate position"}
              </Button>
            </div>
          </form>

          {error ? (
            <p
              role="alert"
              className="border-destructive/25 bg-destructive/5 text-destructive rounded-lg border px-3 py-2 text-sm"
            >
              {error}
            </p>
          ) : null}

          {result ? (
            <div className="border-border bg-background/55 flex flex-col gap-4 rounded-xl border p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h3 className="text-sm font-semibold">Position plan</h3>
                  <p className="text-muted-foreground mt-0.5 text-xs">
                    Three-stop exit book
                  </p>
                </div>
                <span className="bg-primary/10 text-primary rounded-full px-2.5 py-1 text-xs font-medium tabular-nums">
                  {result.shares} shares
                </span>
              </div>

              <dl className="grid grid-cols-2 gap-2 text-sm">
                <div className="bg-muted/45 rounded-lg p-3">
                  <dt className="text-muted-foreground text-xs">Risk $</dt>
                  <dd className="mt-1 font-semibold tabular-nums">
                    {result.risk_dollars.toLocaleString(undefined, {
                      maximumFractionDigits: 2,
                    })}
                  </dd>
                </div>
                <div className="bg-muted/45 rounded-lg p-3">
                  <dt className="text-muted-foreground text-xs">1R / share</dt>
                  <dd className="mt-1 font-semibold tabular-nums">
                    {result.r_per_share.toLocaleString(undefined, {
                      maximumFractionDigits: 4,
                    })}
                  </dd>
                </div>
                <div className="bg-muted/45 rounded-lg p-3">
                  <dt className="text-muted-foreground text-xs">Full-stop R</dt>
                  <dd className="mt-1 font-semibold tabular-nums">
                    {result.expected_full_stop_r.toLocaleString(undefined, {
                      maximumFractionDigits: 4,
                    })}
                  </dd>
                </div>
                {result.suggested_risk_pct != null ? (
                  <div className="bg-muted/45 rounded-lg p-3">
                    <dt className="text-muted-foreground text-xs">
                      Suggested risk %
                    </dt>
                    <dd className="mt-1 font-semibold tabular-nums">
                      {result.suggested_risk_pct.toLocaleString(undefined, {
                        maximumFractionDigits: 4,
                      })}
                    </dd>
                  </div>
                ) : result.suggested_shares != null ? (
                  <div className="bg-muted/45 rounded-lg p-3">
                    <dt className="text-muted-foreground text-xs">
                      Suggested shares
                    </dt>
                    <dd className="mt-1 font-semibold tabular-nums">
                      {result.suggested_shares}
                    </dd>
                  </div>
                ) : null}
              </dl>

              <div className="border-border overflow-x-auto rounded-lg border">
                <table className="w-full min-w-[22rem] text-left text-sm">
                  <thead className="bg-muted/45 border-border border-b text-xs">
                    <tr>
                      <th className="px-3 py-2 font-medium">Stop</th>
                      <th className="px-3 py-2 font-medium">Price</th>
                      <th className="px-3 py-2 font-medium">Shares</th>
                      <th className="px-3 py-2 font-medium">R</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.stop_book.map((level) => (
                      <tr
                        key={level.label}
                        className="border-border border-b last:border-b-0"
                      >
                        <td className="px-3 py-2 font-medium">{level.label}</td>
                        <td className="px-3 py-2 tabular-nums">
                          {level.price.toLocaleString(undefined, {
                            maximumFractionDigits: 4,
                          })}
                        </td>
                        <td className="px-3 py-2 tabular-nums">{level.shares}</td>
                        <td className="px-3 py-2 tabular-nums">{level.r_fraction}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}
        </section>

        <section className="border-border bg-card/70 flex flex-col gap-5 rounded-2xl border p-4 shadow-sm sm:p-6">
          <header className="flex items-start gap-3">
            <span className="bg-secondary text-secondary-foreground flex size-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold tabular-nums">
              2
            </span>
            <div className="min-w-0">
              <p className="text-muted-foreground text-xs font-medium tracking-[0.12em] uppercase">
                Review the open trade
              </p>
              <h2 className="display-tight mt-1 text-lg font-semibold">
                Position management
              </h2>
              <p className="text-muted-foreground mt-1 text-sm">
                Turn the trade’s current state into a specific next action.
              </p>
            </div>
          </header>

          <form onSubmit={onPlanSubmit} className="flex flex-col gap-5">
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="sm:col-span-3">
                <h3 className="text-sm font-semibold">Position</h3>
                <p className="text-muted-foreground mt-0.5 text-xs">
                  The live position and its current price.
                </p>
              </div>
              <label className="flex flex-col gap-1.5 text-sm">
                <span className="text-muted-foreground">Shares</span>
                <Input
                  type="text"
                  inputMode="numeric"
                  value={mgmtShares}
                  onChange={(e) => setMgmtShares(e.target.value)}
                  required
                />
              </label>
              <label className="flex flex-col gap-1.5 text-sm">
                <span className="text-muted-foreground">Entry price</span>
                <Input
                  type="text"
                  inputMode="decimal"
                  value={mgmtEntryPrice}
                  onChange={(e) => setMgmtEntryPrice(e.target.value)}
                  required
                />
              </label>
              <label className="flex flex-col gap-1.5 text-sm">
                <span className="text-muted-foreground">Final stop</span>
                <Input
                  type="text"
                  inputMode="decimal"
                  value={mgmtFinalStop}
                  onChange={(e) => setMgmtFinalStop(e.target.value)}
                  required
                />
              </label>
              <label className="flex flex-col gap-1.5 text-sm">
                <span className="text-muted-foreground">Entry date</span>
                <Input
                  type="date"
                  value={mgmtEntryDate}
                  onChange={(e) => setMgmtEntryDate(e.target.value)}
                  required
                />
              </label>
              <label className="flex flex-col gap-1.5 text-sm">
                <span className="text-muted-foreground">As-of date</span>
                <Input
                  type="date"
                  value={mgmtAsOfDate}
                  onChange={(e) => setMgmtAsOfDate(e.target.value)}
                  required
                />
              </label>
              <label className="flex flex-col gap-1.5 text-sm">
                <span className="text-muted-foreground">Current price</span>
                <Input
                  type="text"
                  inputMode="decimal"
                  value={mgmtCurrentPrice}
                  onChange={(e) => setMgmtCurrentPrice(e.target.value)}
                />
              </label>
            </div>

            <div className="border-border border-t pt-5">
              <h3 className="text-sm font-semibold">Execution so far</h3>
              <p className="text-muted-foreground mt-0.5 text-xs">
                Select only the actions already taken.
              </p>
              <div className="mt-3 grid gap-2 sm:grid-cols-3">
                <label className="position-option border-border bg-background/45 has-[:checked]:border-primary has-[:checked]:bg-primary/5 flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2.5 text-sm">
                  <input
                    className="accent-primary size-4 shrink-0"
                    type="checkbox"
                    checked={shave2rTaken}
                    onChange={(e) => setShave2rTaken(e.target.checked)}
                  />
                  <span>2R shave taken</span>
                </label>
                <label className="position-option border-border bg-background/45 has-[:checked]:border-primary has-[:checked]:bg-primary/5 flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2.5 text-sm">
                  <input
                    className="accent-primary size-4 shrink-0"
                    type="checkbox"
                    checked={day3PartialTaken}
                    onChange={(e) => setDay3PartialTaken(e.target.checked)}
                  />
                  <span>Day-3 partial taken</span>
                </label>
                <label className="position-option border-border bg-background/45 has-[:checked]:border-primary has-[:checked]:bg-primary/5 flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2.5 text-sm">
                  <input
                    className="accent-primary size-4 shrink-0"
                    type="checkbox"
                    checked={consolidatedToBe}
                    onChange={(e) => setConsolidatedToBe(e.target.checked)}
                  />
                  <span>Consolidated to BE</span>
                </label>
              </div>
            </div>

            <details className="border-border bg-muted/20 group rounded-xl border">
              <summary className="marker:hidden flex cursor-pointer list-none items-center justify-between gap-4 px-4 py-3 text-sm font-medium">
                <span>
                  Market context & optional signals
                  <span className="text-muted-foreground ml-2 text-xs font-normal">
                    Moving averages, stops, and extensions
                  </span>
                </span>
                <span className="text-muted-foreground transition-transform duration-[160ms] ease-[var(--ease-out)] group-open:rotate-45">
                  +
                </span>
              </summary>
              <div className="border-border grid gap-3 border-t p-4 sm:grid-cols-3">
                <label className="flex flex-col gap-1.5 text-sm">
                  <span className="text-muted-foreground">MA10</span>
                  <Input
                    type="text"
                    inputMode="decimal"
                    value={ma10}
                    onChange={(e) => setMa10(e.target.value)}
                  />
                </label>
                <label className="flex flex-col gap-1.5 text-sm">
                  <span className="text-muted-foreground">MA50</span>
                  <Input
                    type="text"
                    inputMode="decimal"
                    value={ma50}
                    onChange={(e) => setMa50(e.target.value)}
                  />
                </label>
                <label className="flex flex-col gap-1.5 text-sm">
                  <span className="text-muted-foreground">ATR%</span>
                  <Input
                    type="text"
                    inputMode="decimal"
                    value={atrPct}
                    onChange={(e) => setAtrPct(e.target.value)}
                  />
                </label>
                <label className="flex flex-col gap-1.5 text-sm">
                  <span className="text-muted-foreground">Close below 10-MA</span>
                  <Input
                    type="date"
                    value={closeBelow10maDate}
                    onChange={(e) => setCloseBelow10maDate(e.target.value)}
                  />
                </label>
                <label className="flex flex-col gap-1.5 text-sm">
                  <span className="text-muted-foreground">ORL</span>
                  <Input
                    type="text"
                    inputMode="decimal"
                    value={orl}
                    onChange={(e) => setOrl(e.target.value)}
                  />
                </label>
                <label className="flex flex-col gap-1.5 text-sm">
                  <span className="text-muted-foreground">Prior day high</span>
                  <Input
                    type="text"
                    inputMode="decimal"
                    value={priorDayHigh}
                    onChange={(e) => setPriorDayHigh(e.target.value)}
                  />
                </label>
                <label className="flex flex-col gap-1.5 text-sm">
                  <span className="text-muted-foreground">Extension override</span>
                  <Input
                    type="text"
                    inputMode="decimal"
                    value={extensionOverride}
                    onChange={(e) => setExtensionOverride(e.target.value)}
                  />
                </label>
                <div className="grid gap-2 sm:col-span-2 sm:grid-cols-2">
                  <label className="position-option border-border bg-background/45 has-[:checked]:border-primary has-[:checked]:bg-primary/5 flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2.5 text-sm">
                    <input
                      className="accent-primary size-4 shrink-0"
                      type="checkbox"
                      checked={stops33Hit}
                      onChange={(e) => setStops33Hit(e.target.checked)}
                    />
                    <span>33% stop hit</span>
                  </label>
                  <label className="position-option border-border bg-background/45 has-[:checked]:border-primary has-[:checked]:bg-primary/5 flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2.5 text-sm">
                    <input
                      className="accent-primary size-4 shrink-0"
                      type="checkbox"
                      checked={stops66Hit}
                      onChange={(e) => setStops66Hit(e.target.checked)}
                    />
                    <span>66% stop hit</span>
                  </label>
                  <label className="position-option border-border bg-background/45 has-[:checked]:border-primary has-[:checked]:bg-primary/5 flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2.5 text-sm">
                    <input
                      className="accent-primary size-4 shrink-0"
                      type="checkbox"
                      checked={rescaleAlertTriggered}
                      onChange={(e) => setRescaleAlertTriggered(e.target.checked)}
                    />
                    <span>Rescale alert triggered</span>
                  </label>
                  <label className="position-option border-border bg-background/45 has-[:checked]:border-primary has-[:checked]:bg-primary/5 flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2.5 text-sm">
                    <input
                      className="accent-primary size-4 shrink-0"
                      type="checkbox"
                      checked={sidewaysConsolidation}
                      onChange={(e) => setSidewaysConsolidation(e.target.checked)}
                    />
                    <span>Sideways consolidation</span>
                  </label>
                </div>
              </div>
            </details>

            <div className="flex flex-wrap items-center gap-2 border-border border-t pt-5">
              <Button type="submit" disabled={planLoading}>
                {planLoading ? "Planning…" : "Compute plan"}
              </Button>
              <Button
                type="button"
                variant="outline"
                disabled={!result}
                onClick={useSizingResult}
              >
                Use sizing result
              </Button>
            </div>
          </form>

          {planError ? (
            <p
              role="alert"
              className="border-destructive/25 bg-destructive/5 text-destructive rounded-lg border px-3 py-2 text-sm"
            >
              {planError}
            </p>
          ) : null}

          {planResult ? (
            <div className="border-border bg-background/55 flex flex-col gap-4 rounded-xl border p-4">
              <div>
                <h3 className="text-sm font-semibold">Today’s plan</h3>
                <p className="text-muted-foreground mt-0.5 text-xs">
                  Review the stop book, then act on the highest-priority signal.
                </p>
              </div>
              <dl className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
                <div className="bg-muted/45 rounded-lg p-3">
                  <dt className="text-muted-foreground text-xs">Day index</dt>
                  <dd className="mt-1 font-semibold tabular-nums">
                    {planResult.day_index}
                  </dd>
                </div>
                <div className="bg-muted/45 rounded-lg p-3">
                  <dt className="text-muted-foreground text-xs">Phase</dt>
                  <dd className="mt-1 font-semibold capitalize">
                    {planResult.phase}
                  </dd>
                </div>
                <div className="bg-muted/45 rounded-lg p-3">
                  <dt className="text-muted-foreground text-xs">Unrealized R</dt>
                  <dd className="mt-1 font-semibold tabular-nums">
                    {planResult.unrealized_r == null
                      ? "—"
                      : planResult.unrealized_r.toLocaleString(undefined, {
                          maximumFractionDigits: 4,
                        })}
                  </dd>
                </div>
                <div className="bg-muted/45 rounded-lg p-3">
                  <dt className="text-muted-foreground text-xs">Stop mode</dt>
                  <dd className="mt-1 font-semibold">{planResult.stop_mode}</dd>
                </div>
                <div className="bg-muted/45 rounded-lg p-3">
                  <dt className="text-muted-foreground text-xs">Mental stop</dt>
                  <dd className="mt-1 font-semibold tabular-nums">
                    {planResult.mental_stop ?? "—"}
                  </dd>
                </div>
                <div className="bg-muted/45 rounded-lg p-3">
                  <dt className="text-muted-foreground text-xs">Net shares</dt>
                  <dd className="mt-1 font-semibold tabular-nums">
                    {planResult.net_shares}
                  </dd>
                </div>
              </dl>

              <div className="border-border overflow-x-auto rounded-lg border">
                <table className="w-full min-w-[24rem] text-left text-sm">
                  <thead className="bg-muted/45 border-border border-b text-xs">
                    <tr>
                      <th className="px-3 py-2 font-medium">Stop</th>
                      <th className="px-3 py-2 font-medium">Price</th>
                      <th className="px-3 py-2 font-medium">Shares</th>
                      <th className="px-3 py-2 font-medium">R</th>
                    </tr>
                  </thead>
                  <tbody>
                    {planResult.stop_book.map((level) => (
                      <tr
                        key={`${level.label}-${level.price}`}
                        className="border-border border-b last:border-b-0"
                      >
                        <td className="px-3 py-2 font-medium">{level.label}</td>
                        <td className="px-3 py-2 tabular-nums">
                          {level.price.toLocaleString(undefined, {
                            maximumFractionDigits: 4,
                          })}
                        </td>
                        <td className="px-3 py-2 tabular-nums">{level.shares}</td>
                        <td className="px-3 py-2 tabular-nums">{level.r_fraction}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {planResult.actions.length > 0 ? (
                <div>
                  <h4 className="text-sm font-semibold">Actions</h4>
                  <ul className="mt-2 flex flex-col gap-2 text-sm">
                    {planResult.actions.map((action) => (
                      <li
                        key={`${action.code}-${action.message}`}
                        className="border-border bg-muted/25 flex items-start gap-2 rounded-lg border p-3"
                      >
                        <span className="bg-secondary text-secondary-foreground shrink-0 rounded px-1.5 py-0.5 text-[0.65rem] font-semibold tracking-wide uppercase">
                          {action.severity}
                        </span>
                        <span>{action.message}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p className="text-muted-foreground text-sm">
                  No actions for this state.
                </p>
              )}
            </div>
          ) : null}
        </section>
      </div>
    </div>
  )
}
