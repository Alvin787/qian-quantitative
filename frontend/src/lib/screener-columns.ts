import type { ResultValue } from "@/lib/screener-api"

export type StatusTone = "positive" | "negative" | "neutral"

export const DEFAULT_VISIBLE_COLUMNS_BY_STRATEGY: Record<string, string[]> = {
  reversal: [
    "ticker",
    "pass_all",
    "close",
    "adr_pct",
    "near_20_pct",
    "rs_3m_pp",
    "rs_6m_pp",
    "extension_x",
    "avg_dollar_vol_m",
    "days_to_earnings",
    "industry",
  ],
  breakout: [
    "ticker",
    "industry",
    "screen_count",
    "screen_family_count",
    "source_screens",
  ],
}

/** Returns the strategy's default column list, or null when the strategy has none (caller shows all available columns). */
export function defaultVisibleColumns(strategyId: string): string[] | null {
  return DEFAULT_VISIBLE_COLUMNS_BY_STRATEGY[strategyId] ?? null
}

const COLUMN_LABELS: Record<string, string> = {
  ticker: "Ticker",
  pass_all: "Pass",
  fail_reasons: "Fail reasons",
  warnings: "Warnings",
  close: "Close",
  adr_pct: "ADR %",
  adr_ok: "ADR OK",
  rising_50: "Rising 50",
  rising_200: "Rising 200",
  above_stack: "Above stack",
  near_20_pct: "Near 20 %",
  near_50_pct: "Near 50 %",
  pullback_ok: "Pullback OK",
  rs_3m_pp: "RS 3m",
  rs_6m_pp: "RS 6m",
  rs_ok: "RS OK",
  p1_pullbacks: "P1 pullbacks",
  p1_episodes: "P1 episodes",
  p2_persist: "P2 persistence",
  persist_70: "Persistence",
  p3_linear: "P3 linearity",
  extension_x: "Extension",
  p4_volexp: "P4 volume",
  avg_dollar_vol_m: "Avg $ vol (M)",
  days_to_earnings: "Days to earnings",
  earnings_date: "Earnings date",
  industry: "Industry",
  screen_count: "Screens",
  screen_family_count: "Families",
  source_screens: "Source screens",
  linear_r2: "Linear R²",
  volexp_ratio: "Vol expansion",
  pullback_depth_adr: "Pullback (ADR)",
  proxies_passed: "Proxies passed",
  proxies_ok: "Proxies OK",
  waterfall_flag: "Waterfall",
  liq_ok: "Liquidity OK",
  ext_ok: "Extension OK",
  earn_ok: "Earnings OK",
  sma20: "SMA 20",
  sma50: "SMA 50",
  sma200: "SMA 200",
  biotech: "Biotech",
}

const COLUMN_DESCRIPTIONS: Record<string, string> = {
  pass_all:
    "Cleared every automated gate. Still confirm the chart and news before trading.",
  fail_reasons: "The gates this ticker failed and the values that caused each failure.",
  warnings: "Non-blocking risks that deserve a manual chart or news check.",
  close: "Latest daily close—the reference price used by the other checks.",
  adr_pct:
    "Average daily range over 20 days. The 2–5% target seeks useful movement without excessive volatility.",
  adr_ok: "Whether ADR is inside the strategy's 2–5% target range.",
  rising_50: "Whether the 50-day average is rising, confirming the intermediate uptrend.",
  rising_200: "Whether the 200-day average is rising, confirming the long-term uptrend.",
  above_stack: "Whether price is above both the rising 50- and 200-day averages.",
  near_20_pct:
    "Distance from the 20-day average. Within 4% suggests a pullback near support.",
  near_50_pct:
    "Distance from the 50-day average. Within 4% suggests a pullback near support.",
  pullback_ok: "Whether price is within 4% of the 20- or 50-day average.",
  rs_3m_pp:
    "3-month return minus SPY's, in percentage points. Positive means market outperformance.",
  rs_6m_pp:
    "6-month return minus SPY's, showing whether market leadership has persisted.",
  rs_ok: "Whether the ticker beat SPY over both 3 and 6 months.",
  p1_pullbacks: "Whether recent pullbacks to the 20-day average held and recovered.",
  p1_episodes: "Number of qualifying pullback-and-recovery episodes recently detected.",
  p2_persist: "Whether price stayed above the 20-day average often enough to show support.",
  persist_70:
    "Share of the last 50 sessions above the 20-day average. 70%+ signals trend persistence.",
  p3_linear: "Whether the 6-month uptrend is steady rather than erratic.",
  linear_r2:
    "Consistency of the 6-month price trend. Nearer 1 is smoother; 0.70+ is preferred.",
  p4_volexp: "Whether the prior advance had stronger volume on up days.",
  volexp_ratio:
    "Up-day versus down-day volume during the prior advance. Above 1.2 suggests accumulation.",
  proxies_passed: "Persistence signals passed. At least 2 of 4 are required.",
  proxies_ok: "Whether at least 2 of the 4 persistence signals passed.",
  waterfall_flag: "Flags a decline that may be too deep or forceful to be a routine dip.",
  pullback_depth_adr:
    "Pullback depth measured in average daily ranges. Above 2.5 can signal a waterfall.",
  avg_dollar_vol_m:
    "Average daily traded value in millions. $20M+ helps limit entry and exit slippage.",
  liq_ok: "Whether average daily dollar volume clears the $20M liquidity floor.",
  extension_x:
    "Distance above the 50-day average measured in ATR%. Above 4x is considered stretched.",
  ext_ok: "Whether extension above the 50-day average is no more than 4× ATR%.",
  earnings_date: "Next expected earnings date; verify manually when unconfirmed.",
  days_to_earnings:
    "Trading sessions until earnings. Fewer than 6 adds significant event risk.",
  earn_ok: "Whether at least 6 trading sessions remain before earnings.",
  sma20: "20-day simple moving average, used as near-term trend support.",
  sma50: "50-day simple moving average, used for trend and extension checks.",
  sma200: "200-day simple moving average, used to confirm the primary trend.",
  industry: "Industry classification, used to identify sector-specific risks.",
  screen_count:
    "How many breakout screens surfaced this ticker. More screens means more overlapping setups.",
  screen_family_count:
    "Independent screen families that surfaced this ticker, not nested momentum horizons.",
  source_screens: "The breakout screens this ticker appeared in.",
  biotech: "Biotech names are excluded because binary trial and FDA events can overwhelm the setup.",
}

const POSITIVE_STRINGS = new Set([
  "pass",
  "passed",
  "ok",
  "true",
  "yes",
  "y",
])
const NEGATIVE_STRINGS = new Set([
  "fail",
  "failed",
  "false",
  "no",
  "n",
])
const NEUTRAL_STRINGS = new Set([
  "unknown",
  "not_checked",
  "not checked",
  "skipped",
  "n/a",
  "na",
  "—",
  "-",
])

export type StatusBadgeValue = {
  tone: StatusTone
  label: string
}

export function columnLabel(column: string) {
  return (
    COLUMN_LABELS[column] ??
    column.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase())
  )
}

export function columnDescription(column: string) {
  return COLUMN_DESCRIPTIONS[column]
}

export function humanizeToken(value: string) {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

/** Map pass/fail, yes/no, and related gate values to a badge; null if plain text. */
export function statusBadgeFor(
  value: ResultValue,
  column?: string
): StatusBadgeValue | null {
  if (value === null || value === undefined || value === "") {
    if (column === "pass_all" || column?.endsWith("_ok") || column === "earn_ok") {
      return { tone: "neutral", label: "—" }
    }
    return null
  }

  if (typeof value === "boolean") {
    if (column === "pass_all") {
      return value
        ? { tone: "positive", label: "Pass" }
        : { tone: "negative", label: "Fail" }
    }
    return value
      ? { tone: "positive", label: "Yes" }
      : { tone: "negative", label: "No" }
  }

  if (typeof value !== "string") return null

  const trimmed = value.trim()
  if (!trimmed) return null
  const normalized = trimmed.toLowerCase()

  if (POSITIVE_STRINGS.has(normalized)) {
    return {
      tone: "positive",
      label: column === "pass_all" ? "Pass" : humanizeToken(trimmed),
    }
  }
  if (NEGATIVE_STRINGS.has(normalized)) {
    return {
      tone: "negative",
      label: column === "pass_all" ? "Fail" : humanizeToken(trimmed),
    }
  }
  if (NEUTRAL_STRINGS.has(normalized)) {
    return { tone: "neutral", label: humanizeToken(trimmed) }
  }

  return null
}

export function formatValue(value: ResultValue) {
  if (value === null || value === undefined || value === "") return "—"
  if (typeof value === "boolean") return value ? "Yes" : "No"
  if (typeof value === "number") {
    if (!Number.isFinite(value)) return "—"
    if (Number.isInteger(value)) return value.toLocaleString()
    return value.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })
  }
  return String(value)
}

export function compareValues(a: ResultValue, b: ResultValue) {
  const aMissing = a === null || a === undefined || a === ""
  const bMissing = b === null || b === undefined || b === ""
  if (aMissing && bMissing) return 0
  if (aMissing) return 1
  if (bMissing) return -1

  if (typeof a === "number" && typeof b === "number") return a - b
  if (typeof a === "boolean" && typeof b === "boolean") {
    return Number(a) - Number(b)
  }
  return String(a).localeCompare(String(b), undefined, { numeric: true })
}
