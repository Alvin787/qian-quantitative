MARKET_SYMBOLS: list[str] = ["RSP", "QQQE", "IWM"]
MARKET_RATIO_PAIRS: list[tuple[str, str]] = [("RSP", "SPY"), ("QQQE", "QQQ")]
SUBMARKET_SYMBOLS: list[str] = ["IJS", "IJT", "IJJ", "IJK", "IVE", "IVW"]
SECTOR_SYMBOLS: list[str] = [
    "XLRE", "XLU", "XLV", "XLF", "XLP", "XLB", "XLE", "XLI", "XLY", "XLC", "XLK"
]
PRIORITY_SECTORS: frozenset[str] = frozenset({"XLE", "XLI", "XLY", "XLK", "XLV"})
BENCHMARK_SYMBOL: str = "SPY"
