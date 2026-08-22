import { humanizeToken } from "@/lib/screener-columns"
import type { Readiness } from "@/lib/watchlists-api"

export const READINESS_ORDER: Readiness[] = [
  "chart_review_ready",
  "stalk_ready",
  "watch",
  "earnings_blocked",
  "data_incomplete",
  "disrupted",
  "excluded",
  "unscored",
  "unknown",
]

const SCREEN_LABELS: Record<string, { short: string; full: string }> = {
  canslim_calibrated: {
    short: "CANSLIM",
    full: "CANSLIM-inspired calibrated",
  },
  high_adr_hottest: {
    short: "Hottest",
    full: "High ADR% hottest stocks",
  },
  high_adr_short_squeeze: {
    short: "Squeeze",
    full: "High ADR% short squeeze",
  },
  extended_base_above_sma200: {
    short: "Base >200",
    full: "Extended base above SMA200",
  },
  extended_base_below_sma200: {
    short: "Base <200",
    full: "Extended base below SMA200",
  },
  strongest_mover_1w: {
    short: "1W",
    full: "Strongest mover, 1 week +20%",
  },
  strongest_mover_1w_tight: {
    short: "1W +30%",
    full: "Strongest mover, 1 week +30%",
  },
  strongest_mover_1m: {
    short: "1M",
    full: "Strongest mover, 1 month",
  },
  strongest_mover_1m_strong_market: {
    short: "1M +50%",
    full: "Strongest mover, 1 month +50%",
  },
  strongest_mover_3m: {
    short: "3M",
    full: "Strongest mover, 3 months",
  },
  strongest_mover_6m: {
    short: "6M",
    full: "Strongest mover, 6 months",
  },
  ipo_this_year: {
    short: "IPO",
    full: "IPO within the last year",
  },
  high_short_float: {
    short: "Short float",
    full: "High short float",
  },
  liquid_leveraged_etf: {
    short: "Lev ETF",
    full: "Liquid leveraged / inverse ETF",
  },
}

const FAIL_REASON_LABELS: Record<string, string> = {
  adr: "ADR",
  ext: "Extension",
  rs: "RS",
  below_10: "Below 10",
  below_20: "Below 20",
  flat_10: "Flat 10",
  flat_20: "Flat 20",
  declining_200: "Declining 200",
}

export function screenShortLabel(id: string) {
  return SCREEN_LABELS[id]?.short ?? humanizeToken(id)
}

export function screenFullLabel(id: string) {
  return SCREEN_LABELS[id]?.full ?? humanizeToken(id)
}

export function failReasonLabel(token: string) {
  return FAIL_REASON_LABELS[token] ?? humanizeToken(token)
}

export function listLabel(list: string) {
  return humanizeToken(list)
}
