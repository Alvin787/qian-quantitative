import { useCallback, useEffect, useState } from "react"
import { Loader2, RefreshCw } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  fetchDiarySnapshot,
  fetchNarrative,
  putNarrative,
  type BreadthBlock,
  type CnbcBrief,
  type DiarySnapshot,
  type EtfRow,
} from "@/lib/diary-api"
import { cn } from "@/lib/utils"
import { fetchFunnel, type WatchlistName } from "@/lib/watchlists-api"

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong."
}

function formatPct(value: number) {
  const sign = value > 0 ? "+" : ""
  return `${sign}${value.toFixed(2)}%`
}

function formatNet(value: number) {
  const sign = value > 0 ? "+" : ""
  return `${sign}${value}`
}

function PctFromLowBar({ value }: { value: number }) {
  const clamped = Math.max(0, Math.min(100, value))
  return (
    <div className="flex min-w-[8rem] items-center gap-2">
      <div className="bg-muted h-2 flex-1 overflow-hidden rounded-full">
        <div
          className="bg-foreground/70 h-full rounded-full"
          style={{ width: `${clamped}%` }}
        />
      </div>
      <span className="text-muted-foreground w-14 text-right text-xs tabular-nums">
        {value.toFixed(1)}%
      </span>
    </div>
  )
}

function MmtwSparkline({
  points,
}: {
  points: BreadthBlock["mmtw_history"]
}) {
  if (points.length === 0) {
    return (
      <p className="text-muted-foreground text-xs">No $MMTW history.</p>
    )
  }

  const values = points.map((p) => p.last)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const span = max - min || 1
  const w = 160
  const h = 40
  const pad = 2
  const coords = values
    .map((v, i) => {
      const x =
        values.length === 1
          ? w / 2
          : pad + (i / (values.length - 1)) * (w - pad * 2)
      const y = h - pad - ((v - min) / span) * (h - pad * 2)
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(" ")

  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      className="text-foreground h-10 w-40"
      role="img"
      aria-label="$MMTW 5-day sparkline"
    >
      <polyline
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        points={coords}
      />
    </svg>
  )
}

function BreadthSection({
  breadth,
  sectionError,
}: {
  breadth: BreadthBlock | null
  sectionError?: string | null
}) {
  if (!breadth) {
    return (
      <section className="flex flex-col gap-2">
        <h2 className="display-tight text-base font-semibold">
          Short Term Breadth
        </h2>
        {sectionError ? (
          <p role="alert" className="text-destructive text-sm">
            {sectionError}
          </p>
        ) : (
          <p className="text-muted-foreground text-sm">No breadth data.</p>
        )}
      </section>
    )
  }

  const netLabel =
    breadth.finviz_net == null ? "—" : formatNet(breadth.finviz_net)

  return (
    <section className="flex flex-col gap-3">
      <h2 className="display-tight text-base font-semibold">
        Short Term Breadth
      </h2>
      {sectionError ? (
        <p role="alert" className="text-destructive text-sm">
          {sectionError}
        </p>
      ) : null}

      <div className="flex flex-wrap items-end gap-6">
        <div className="flex flex-col gap-1">
          <p className="text-muted-foreground text-xs">
            $MMTW · {breadth.sources.mmtw}
          </p>
          <div className="flex items-center gap-3">
            <span className="text-2xl font-semibold tabular-nums tracking-tight">
              {breadth.mmtw_last == null ? "—" : breadth.mmtw_last.toFixed(2)}
            </span>
            {breadth.mmtw_bullish_bias === true ? (
              <span className="border-border bg-muted/60 rounded-md border px-2 py-0.5 text-xs">
                &gt;50% bias
              </span>
            ) : null}
          </div>
          <p className="text-muted-foreground text-xs">
            bullish bias when &gt; 50%
          </p>
          <MmtwSparkline points={breadth.mmtw_history} />
        </div>

        <div className="flex flex-col gap-1">
          <p className="text-muted-foreground text-xs">
            NH / NL · {breadth.sources.finviz_nhnl}
          </p>
          <p className="text-sm tabular-nums">
            {breadth.finviz_new_highs ?? "—"} vs{" "}
            {breadth.finviz_new_lows ?? "—"} (net {netLabel})
          </p>
          <p className="text-muted-foreground text-xs">
            Finviz universe proxy — not official exchange NH/NL
          </p>
        </div>

        <div className="flex flex-col gap-1">
          <p className="text-muted-foreground text-xs">
            $NYHL / $NAHL · {breadth.sources.nyhl_nahl}
          </p>
          <p className="text-sm tabular-nums">
            $NYHL{" "}
            {breadth.nyhl == null ? "—" : breadth.nyhl.toFixed(2)}
            {" · "}$NAHL{" "}
            {breadth.nahl == null ? "—" : breadth.nahl.toFixed(2)}
          </p>
        </div>
      </div>
    </section>
  )
}

function CnbcSection({
  cnbc,
  sectionStatus,
  sectionError,
}: {
  cnbc: CnbcBrief | null
  sectionStatus?: string
  sectionError?: string | null
}) {
  return (
    <section className="flex flex-col gap-2">
      <h2 className="display-tight text-base font-semibold">
        CNBC 5 Things
      </h2>
      {sectionStatus === "error" ? (
        <p role="alert" className="text-destructive text-sm">
          {sectionError || "CNBC 5 Things unavailable."}
        </p>
      ) : null}
      {cnbc ? (
        <div className="flex flex-col gap-1">
          <a
            href={cnbc.url}
            target="_blank"
            rel="noreferrer"
            className="text-sm font-medium underline-offset-2 hover:underline"
          >
            {cnbc.title}
          </a>
          {cnbc.excerpt ? (
            <p className="text-muted-foreground text-sm">{cnbc.excerpt}</p>
          ) : null}
        </div>
      ) : sectionStatus !== "error" ? (
        <p className="text-muted-foreground text-sm">No CNBC brief.</p>
      ) : null}
    </section>
  )
}

function NarrativeEditor({ asOfDate }: { asOfDate: string }) {
  const [body, setBody] = useState("")
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [savedAt, setSavedAt] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    void (async () => {
      try {
        const narrative = await fetchNarrative(asOfDate, controller.signal)
        if (controller.signal.aborted) return
        setBody(narrative?.body ?? "")
        setSavedAt(narrative?.updated_at ?? null)
      } catch (err) {
        if (controller.signal.aborted) return
        setError(errorMessage(err))
        setBody("")
        setSavedAt(null)
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    })()
    return () => controller.abort()
  }, [asOfDate])

  const onSave = async () => {
    setSaving(true)
    setError(null)
    try {
      const saved = await putNarrative(asOfDate, body)
      setSavedAt(saved.updated_at)
      setBody(saved.body)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="flex flex-col gap-2">
      <h2 className="display-tight text-base font-semibold">Narrative</h2>
      <p className="text-muted-foreground text-xs">For {asOfDate}</p>
      {error ? (
        <p role="alert" className="text-destructive text-sm">
          {error}
        </p>
      ) : null}
      <textarea
        className="border-border bg-background/80 min-h-[8rem] w-full rounded-xl border px-3 py-2 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
        value={body}
        onChange={(e) => setBody(e.target.value)}
        disabled={loading || saving}
        placeholder={loading ? "Loading…" : "Write today's narrative…"}
        aria-label={`Narrative for ${asOfDate}`}
      />
      <div className="flex flex-wrap items-center gap-3">
        <Button
          type="button"
          size="sm"
          onClick={() => void onSave()}
          disabled={loading || saving}
        >
          {saving ? (
            <Loader2 className="size-4 animate-spin" aria-hidden />
          ) : null}
          Save
        </Button>
        {savedAt ? (
          <p className="text-muted-foreground text-xs">Saved {savedAt}</p>
        ) : null}
      </div>
    </section>
  )
}

function FunnelStrip({ reloadId }: { reloadId: number }) {
  const [names, setNames] = useState<WatchlistName[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    void (async () => {
      try {
        const funnel = await fetchFunnel(controller.signal)
        if (controller.signal.aborted) return
        setNames(funnel.names)
        setError(null)
      } catch (err) {
        if (controller.signal.aborted) return
        setError(errorMessage(err))
      }
    })()
    return () => controller.abort()
  }, [reloadId])

  const focus = (names ?? []).filter((name) => name.list === "focus")
  const stalk = (names ?? []).filter((name) => name.list === "stalk")

  const copyTickers = (visible: WatchlistName[]) => {
    void navigator.clipboard.writeText(visible.map((n) => n.ticker).join(","))
  }

  const formatName = (name: WatchlistName) =>
    name.group ? `${name.ticker} (${name.group})` : name.ticker

  return (
    <section className="flex flex-col gap-2">
      <h2 className="display-tight text-base font-semibold">Focus / Stalk</h2>
      {error ? (
        <p role="alert" className="text-destructive text-sm">
          {error}
        </p>
      ) : null}
      {names !== null && focus.length === 0 && stalk.length === 0 ? (
        <p className="text-muted-foreground text-sm">
          No focus or stalk names. Manage them on Watchlists.
        </p>
      ) : null}
      {focus.length > 0 || stalk.length > 0 ? (
        <p className="text-sm">
          {[...focus, ...stalk].map((name, index) => (
            <span key={`${name.list}-${name.ticker}`}>
              {index > 0 ? " · " : ""}
              {formatName(name)}
            </span>
          ))}
        </p>
      ) : null}
      <div className="flex flex-wrap items-center gap-3">
        <Button
          type="button"
          size="sm"
          onClick={() => copyTickers(focus)}
        >
          Copy focus
        </Button>
        <Button
          type="button"
          size="sm"
          onClick={() => copyTickers(stalk)}
        >
          Copy stalk
        </Button>
      </div>
    </section>
  )
}

function EtfTable({
  title,
  rows,
  showTrend = false,
  ratios,
  sectionError,
}: {
  title: string
  rows: EtfRow[]
  showTrend?: boolean
  ratios?: EtfRow[]
  sectionError?: string | null
}) {
  return (
    <section className="flex flex-col gap-2">
      <h2 className="display-tight text-base font-semibold">{title}</h2>
      {sectionError ? (
        <p role="alert" className="text-destructive text-sm">
          {sectionError}
        </p>
      ) : null}
      <div className="border-border bg-card/40 overflow-x-auto rounded-xl border shadow-xs">
        <table className="w-full min-w-[36rem] text-left text-sm">
          <thead className="bg-muted/40 border-border border-b">
            <tr>
              <th className="px-3 py-2 font-medium">Symbol</th>
              {showTrend ? (
                <th className="px-3 py-2 font-medium">Short Term Trend</th>
              ) : null}
              <th className="px-3 py-2 font-medium">% From 52w Low</th>
              <th className="px-3 py-2 font-medium">Daily %</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td
                  colSpan={showTrend ? 4 : 3}
                  className="text-muted-foreground px-3 py-6"
                >
                  No rows.
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr
                  key={row.symbol}
                  className="border-border border-b last:border-b-0"
                >
                  <td className="px-3 py-2 font-medium tabular-nums">
                    {row.symbol}
                    {row.priority ? "*" : ""}
                  </td>
                  {showTrend ? (
                    <td className="text-muted-foreground px-3 py-2">
                      {row.short_term_trend}
                    </td>
                  ) : null}
                  <td className="px-3 py-2">
                    <PctFromLowBar value={row.pct_from_52w_low} />
                  </td>
                  <td
                    className={cn(
                      "px-3 py-2 tabular-nums",
                      row.daily_change_pct > 0 && "text-emerald-600",
                      row.daily_change_pct < 0 && "text-destructive"
                    )}
                  >
                    {formatPct(row.daily_change_pct)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {ratios && ratios.length > 0 ? (
        <p className="text-muted-foreground text-xs tabular-nums">
          Ratios:{" "}
          {ratios.map((row, index) => {
            const label = row.ratio_to
              ? `${row.symbol}/${row.ratio_to}`
              : row.symbol
            const value =
              row.ratio_value == null ? "—" : row.ratio_value.toFixed(4)
            return (
              <span key={`${row.symbol}-${row.ratio_to ?? index}`}>
                {index > 0 ? " · " : ""}
                {label} {value}
              </span>
            )
          })}
        </p>
      ) : null}
    </section>
  )
}

export function DiaryPanel() {
  const [snapshot, setSnapshot] = useState<DiarySnapshot | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadId, setReloadId] = useState(0)

  const load = useCallback(async (signal?: AbortSignal) => {
    setLoading(true)
    try {
      const data = await fetchDiarySnapshot(signal)
      if (signal?.aborted) return
      setSnapshot(data)
      setError(null)
    } catch (err) {
      if (signal?.aborted) return
      setError(errorMessage(err))
    } finally {
      if (!signal?.aborted) setLoading(false)
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    void load(controller.signal)
    return () => controller.abort()
  }, [load])

  return (
    <div className="mx-auto flex w-full max-w-[110rem] flex-col gap-5 px-4 py-5 sm:px-6 lg:px-8">
      <div className="flex flex-wrap items-center gap-3">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => {
            void load()
            setReloadId((id) => id + 1)
          }}
          disabled={loading}
        >
          <RefreshCw
            className={cn(loading && "animate-spin")}
            aria-hidden
          />
          Refresh
        </Button>
        {snapshot ? (
          <p className="text-muted-foreground text-xs">
            As of {snapshot.as_of_date}
          </p>
        ) : null}
      </div>

      {error ? (
        <p role="alert" className="text-destructive text-sm">
          {error}
        </p>
      ) : null}

      {loading && !snapshot ? (
        <p className="text-muted-foreground flex items-center gap-2 text-sm">
          <Loader2 className="size-4 animate-spin" aria-hidden />
          Loading diary snapshot…
        </p>
      ) : null}

      {snapshot ? (
        <NarrativeEditor asOfDate={snapshot.as_of_date} />
      ) : null}
      <FunnelStrip reloadId={reloadId} />
      {snapshot ? (
        <>
          <BreadthSection
            breadth={snapshot.breadth}
            sectionError={snapshot.sections.breadth?.error}
          />
          <EtfTable
            title="Market Level"
            rows={snapshot.market}
            showTrend
            ratios={snapshot.market_ratios}
            sectionError={snapshot.sections.market?.error}
          />
          <EtfTable
            title="Sub-Market Level"
            rows={snapshot.submarket}
            sectionError={snapshot.sections.submarket?.error}
          />
          <EtfTable
            title="Sectoral Level"
            rows={snapshot.sectors}
            sectionError={snapshot.sections.sectors?.error}
          />
          <CnbcSection
            cnbc={snapshot.cnbc}
            sectionStatus={snapshot.sections.cnbc?.status}
            sectionError={snapshot.sections.cnbc?.error}
          />
        </>
      ) : null}
    </div>
  )
}
