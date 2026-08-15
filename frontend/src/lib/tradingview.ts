const EXCHANGE_ALIASES: Record<string, string> = {
  NMS: "NASDAQ",
  NAS: "NASDAQ",
  NYQ: "NYSE",
  ASE: "AMEX",
}

export function tradingViewUrl(
  ticker: string,
  exchange?: string | null
): string | null {
  const symbolTicker = ticker.trim().toUpperCase()
  if (!symbolTicker) return null

  const rawExchange = (exchange ?? "").trim().toUpperCase()
  const mapped = EXCHANGE_ALIASES[rawExchange] ?? rawExchange
  const symbol = mapped ? `${mapped}-${symbolTicker}` : symbolTicker

  return `https://www.tradingview.com/symbols/${encodeURIComponent(symbol)}/`
}
