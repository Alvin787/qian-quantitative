# Master Trading Strategy Plan

**Momentum swing trading of range breakouts — distilled from Jeff Sun's (@jfsrev) "Complete Trader's Guide" and its linked resources**

Built for a full-time trader who can watch the US open. Every rule below traces to the source article, its sublinks (qullamaggie.net method summary, Kyna Kosling's risk-management write-up, his TradingView scripts), or the two independent backtests of his heuristics. Where a number is his exact published number, it's stated as such.

> This is an educational synthesis, not financial advice. Jeff's results (multi-hundred-percent years) came from 15 years of skill-building; the same rules executed poorly lose money. Trade small until your own journal proves the edge.

---

## 1. The Core Philosophy (What the Whole System Reduces To)

The strategy is **buying range expansions of high-momentum, high-volatility stocks immediately after a period of price contraction, confirmed by abnormal volume, with tiny defined risk — then holding winners for weeks while cutting losers at a fraction of 1R.**

The edge does **not** come from the setup. It comes from the math around it:

- **Win rate is low and that's fine.** Jeff's max monthly win rate in 2024 was ~31.6%. He cites paths like "27% win rate → +114% annualized." The system is designed to be wrong most of the time.
- **Losses are engineered to average ≈ -0.67R** (the 3-Stop Strategy, Section 8), not -1R.
- **Winners are engineered to be huge** — his 2024 included a 51R trade, 4 trades over 20R, 11 over 10R. One winner covers a 13-trade losing streak.
- **Tightness is the multiplier.** Halving your stop distance doubles the R of the same move. Executing only tight, optimal entries has a parabolic effect on returns — this is the single biggest difference between a +30% and a +500% trader on the same ideas.
- **Fixed % risk to equity** makes losing streaks shallow and winning streaks compound parabolically.

Guiding maxims to internalize: *Think in 100 trades. Always seek reasons NOT to trade. The best loser is the long-term winner. If you don't sell into strength, you'll sell into weakness. Never lose two weeks' gains in a day. Missing trades won't make you go broke; chasing them will.*

---

## 2. Tools (All Free or Near-Free)

| Tool | Purpose |
|---|---|
| **TradingView** | Charting, alerts, live RVOL screeners, watchlists |
| ↳ *Swing Data* (by jfsrev) | On-chart table: ADR%, RVOL, Projected Volume, LoD distance vs ATR, Float %, Avg $ Volume, Market Cap — every entry gate in one glance |
| ↳ *ATR% multiple from 50-MA* (by jfsrev) | Extension gauge: (% above 50-SMA) ÷ ATR%. Governs entries (≤4x) and profit-taking (7–10x) |
| ↳ *VARS – Volatility Adjusted Relative Strength* (by jfsrev) | RS vs SPY normalized by each stock's ATR. **Entry qualification only, never exits** |
| ↳ *Simple Volume with Pocket Pivots* (by finallynitin) | De-noised volume: pocket pivots (accumulation), dry-up, projected volume/RVOL |
| ↳ *EPS & Sales* (Fred6724), *Industry Group Strength* (amphtrading) | Secondary template: fundamentals + group RS |
| **Finviz** (free) | Post-market screening (some filters only Finviz has: IPO age, short float, institutional transactions) |
| **Barchart** | Daily NH/NL (52-week new highs minus new lows) |
| Position-sizing spreadsheet | Computes shares from % risk, plus the 33%/66% stop levels (Section 8) |

Charting: daily chart is the decision timeframe; 30-minute/5-minute for execution. Keep templates clean — price, 10/20/50/200-MA, the indicators above.

---

## 3. Universe: What You're Allowed to Trade

Only stocks that can pay for the risk you take:

- **ADR% ≥ ~3–4%** (Average Daily Range). His study of top-100 yearly performers: 97% had ADR% >2%, 89% >3%, 70% >4%. High ADR% = the move can be large relative to your stop.
- **Liquidity:** average dollar volume high enough that your size is trivial. He tracks leveraged ETFs only above **$100M avg $ volume** and keeps a fixed "liquid mega cap" list of names above **$1B avg $ volume**. Slippage and spreads once cost him 6–7% of a year's equity — treat liquidity as a hard filter, not a preference.
- **Sweet-spot ingredients for the biggest movers:** smaller market cap + low float + high short float ("rocket fuel" — his study of top 100% gainers 2018–2024).
- **Leveraged ETFs are a first-class instrument**, not a gimmick: higher ADR% on liquid underlyings, positive daily compounding on trends (his example: ARM +90% vs 2x ARMG +220%), and they let you halve capital outlay for the same exposure. Maintain his curated list (~30 liquid ones).
- **Hard exclusions:** biotech single names (overnight gap risk destroys stop math — express biotech views only via IBB/XBI or LABU/LABD). No shorting stock directly — bearish ideas are expressed as **longs on inverse ETFs** so every position is a long.

---

## 4. The Screening Stack (Post-Market, Daily)

Screens generate a **generic watchlist — never trades.** Restrict screens, never expand them; a good strong-mover screen returns **fewer than 60 names**.

**Base filter on all Finviz momentum screens:** Market cap Small+ (>$300M) · Avg volume >300K · Current volume >100K.

Daily core screens:

1. **1-Week Mover:** performance week ≥ +20%, weekly volatility >4%
2. **1-Month Mover:** ≥ +30% (toggle to +50% when a hot market floods results), monthly volatility >5%
3. **3-Month Mover:** ≥ +50%, monthly volatility >5%
4. **6-Month Mover:** ≥ +100%, monthly volatility >5%
   *(In TradingView, replace the volatility filters with the native ADR% filter. Run both platforms — results differ slightly.)*
5. **High ADR% "hottest stock" screen** — the high-volatility leadership scan
6. **Parabolic short screen** (daily): small cap+, price ≥50% above its 5-day SMA → candidates for inverse/mean-reversion awareness

Weekly screens: **IPO screen** (recent IPOs building first bases — Finviz only), **high short float screen** (Finviz only), **liquid ETF screen**.

Slower/contextual screens: **CANSLIM-inspired screener** — latest quarterly **EPS and sales both +25% YoY**, price above 50-MA, monthly volatility >3%, price ≥~70% above 52-week low, sorted by industry group, tuned to ~20 names. This is **not actionable** — it feeds a dedicated fundamental-leaders watchlist and tells you which industry groups have earnings power. Plus a mean-reversion pullback screen and a post-earnings-gap (PEG/PEAD) screen for drift plays.

---

## 5. The Funnel: Watchlist → Stalk List → Focus List

This pipeline is the actual job. Screening ~15 min; watchlist management is where alpha lives.

**Global watchlist (~100–150 names).** Anything from the screens with real momentum credentials but not ready. Most actionable trades surface on screens *days or weeks before* their actionable day. Review daily: add new qualifiers, **delete anything whose price action gets disrupted/loose**. If daily review is too heavy, split into three rotating sub-lists. Keep a "back watchlist" of interesting-but-failed names to recalibrate your screens.

**Stalk list.** Names building the right structure but failing ≥1 requirement. Common reasons a name stays here:

- **Earnings within 5 days** (only trade with ≥6 days of earnings leeway — enough time to build a cushion or exit before the report)
- Price still **loose** — contraction not tight enough yet
- **10/20-MA haven't caught up** to price yet
- **Declining 200-MA overhead** (exception: upgrade anyway if there's ≥3× ADR% of room to the declining 200-MA)
- Below the 10/20-MA but tracking closely — set an alert at the recapture level

**Focus list (the only names you may buy — target: a handful, all "A-rated").** A stalk name is promoted when ALL of the following hold:

1. **Relative strength FIRST, setup second.** VARS above zero and building/persistent vs SPY. The stock should be a leader in a leading industry group — when in doubt, pick only the single strongest name in the group (his WULF-within-WGMI example: +120% in 2 months).
2. **Prior catalytic move on big volume** (the "leg one" that proves institutional demand — often earnings/news driven).
3. **High ADR%** intact.
4. **Volatility contraction (VCP):** price tightening above the rising 10/20-MA, range compressing, ideally volume drying up (dry-up is a bonus, not mandatory). *"Before a dancer leaps, he crouches."* **Never** buy a stock whose recent price action is loose or erratic.
5. **Recent price linearity** — clean, orderly advances. Avoid names that double in 3 months but whip so violently they'd give you a 10% win rate over 30 attempts.
6. **A defined pivot** (range high / breakout level) where an alert is set.

Every focus name gets: a **price alert at the pivot**, a pre-planned stop level, and a pre-computed position size. That's the whole point — decisions are made post-market, execution is mechanical.

**Gap-up exception:** a stalk-list name that gaps above its pivot can be traded same-day *if* it's still tight relative to its low-of-day (LoD) — the gap did the breakout for you and the risk is small.

---

## 6. Situational Awareness (Trade Size Follows Market Health)

Run this read daily (~10 min). It doesn't generate trades; it throttles your aggression.

- **Breadth:** MMTW (% of stocks above 20-MA) — **>50% with index 10-MA above 20-MA = bullish bias.** Confirm with 52-week **Net New Highs − New Lows** (Barchart or TradingView NH/NL scripts).
- **Equal-weight vs cap-weight:** RSP/SPY and QQQE/QQQ ratios weakening = early warning of narrow, fragile markets. IWM often leads.
- **Top-down drill:** market → sub-market (size/style ETFs) → 11 SPDR sectors (rank by % off 52-week lows/highs) → industry groups (use tradable-ETF groupings). Five sectors historically carry most breakout success: **XLK, XLY, XLI, XLE, XLV.** Rallies you trust should come with a growing count of industry groups making fresh 1-month RS highs.
- **Index extension via ATR% multiple from 50-MA:** be **reluctant to add new risk when SPY is ~4x extended** — his stated rule (via the Kyna Kosling write-up) is that SPY historically pulls back from ~5x; he employs 6–7x as the extreme zone for indexes. The same gauge flags capitulation lows on the downside — this is exactly how he shorted late March 2025 and bought April 7, 2025.
- **The simplest tell of all (Qullamaggie's):** are your recent breakouts working or failing? If you're in tune, you're never sidelined at the wrong time; if nothing is working, the market is telling you to shrink.
- **Calendar:** know OpEx (3rd Friday), quarter-end rebalancing, Russell reconstitution (4th Friday of June), MSCI (May/Nov), and never initiate right before major economic data or earnings.

Accountability exercise: **annotate every trade — win or loss — on the index chart.** Clusters of losses will map to bad market conditions, not bad setups.

---

## 7. Entry Execution (The Hard Rules)

An A-rated setup can still be a C-rated execution. Reassess risk/reward at the moment of trigger. These are binary gates — any single failure = no trade:

1. **LoD rule:** do NOT enter if price is already **>60% of one ATR above its low of day**. (Entry price − LoD) ÷ ATR ≤ 0.60. The spring must still be coiled; this one rule deletes most unnecessary stop-outs.
2. **Extension rule:** do NOT enter beyond **4× ATR% from the 50-MA** (allow up to 5× for sub-$500M micro caps). Backtests confirm: entries at high extension underperform *random* over the next 5 days.
3. **RVOL confirmation:** demand abnormal relative volume — roughly **≥40% of the 50-day average volume traded within the first 30 minutes** is a substantial liquidity event (he relaxes this to ~20% in specific cases; use Projected Volume with a 50% haircut if unsure what qualifies). Exceptions: mega-cap liquid names and liquid ETFs don't need an RVOL gate, and mean-reversion pullback entries aren't RVOL-gated the way breakouts are. Price always fades without RVOL. Think "surfing an ocean wave, not drifting a river."
4. **Timing:** default trigger is the **30-minute opening range high (M30 ORH / Re-ORH)** — wait 30 minutes after the open unless RVOL is extreme from the bell.
5. **Stop distance:** stop goes at the LoD (or structural low), and must be **within 1 ATR of entry**. If the stop is wider than that, the entry is wrong — wait or pass.
6. **No entries** into immediate overhead gap resistance, against a declining 200-MA, or right before major econ data / earnings.
7. **Max 3 new positions per session.** Roll risk forward only as the market confirms prior day's entries.
8. **Never chase — even one day late.** If you missed the optimal entry, the trade is gone; it will set up again (or another will).
9. The more consecutive up-days the market has strung together, and any large gap-up open, the more cautious you get about adding new risk.
10. Once a portfolio has survived beyond T+3 (see Section 9), **prefer adding to proven winners over opening new names** — adds sit above your breakeven stop and are funded by the market.

**Order mechanics:** price alert fires → check gates → buy stop / market order per plan → hard stop goes in immediately on fill. No hesitation on stops, ever: a 1× stop hesitated on becomes 2×, then 3×.

---

## 8. Position Sizing & the 3-Stop Strategy

**Risk per trade: fixed % of equity — 0.5% to 1.0%** (know that 1% is aggressive when trading high-ADR% names; capital allocation per position scales inversely with ADR%). Shares = (equity × risk%) ÷ (entry − stop).

**The 3-Stop Strategy** (his signature loss-control mechanism — built for sub-40% win rates):

- Split the position into **three equal tranches**. The *trade's* stop level never changes — only exit sizing is layered.
- Tranche 1 exits if price retraces **33%** of the entry→stop distance.
- Tranche 2 exits at **66%** of the distance.
- Tranche 3 exits at the full stop.
- Expected loss on a full stop-out: (⅓×0.33R)+(⅓×0.66R)+(⅓×1R) ≈ **-0.67R** instead of -1R (realized: −0.6 to −0.8R). Over hundreds of trades, this alone lifts profit factor materially — and softens gap-down damage.
- Key observation from his journal: positions that never touch layer 1 or 2 within T+3 are typically the strong runners (often 5R+). The stat that matters long-term is your **average R loss** — manage it obsessively.
- Re-entry after a stop-out is allowed (at a fresh valid trigger) with sizing adjusted so the *combined* attempt still risks ≤1R total.

---

## 9. Trade Management: The T+3 Framework

T = execution day; +1/+2/+3 are trading days after (no weekends/holidays).

**Days 0–2:**
- If the trade reaches **+2R → sell 33%** into strength.
- If it reaches **10× ATR% from the 50-MA on entry day → sell another 33%** into that strength.
- Otherwise: do nothing. Give it the time axis, not just the price axis.

**Day 3 (T+3):**
- Still in the trade? Take the first 33% partial now if not yet taken.
- **Move the hard stop to breakeven.** (Move it earlier if the trade exceeds +4R — a parabolic gain should never return to a loss.)
- If it's flat/heavy but hasn't stopped you: no cushion to hold overnight is itself information — his answer is that the position must earn its overnight hold.

**Day 4 onward — the runner (final third or two-thirds):**
- Trail with the **10-day MA as a mental stop** (a 10-MA sell rule can keep you in a trend for 5 months). Don't outsmart the 10- and 20-MA — they're the "magic lines" of trending stocks.
- On a **close below the 10-MA:** keep the hard stop at breakeven, let the next session trade 5 minutes, then raise the hard stop to that day's **5-minute opening-range low**. If it survives the day, reset and repeat daily until stopped. This surrenders minimal unrealized profit while giving the trend every chance.
- Sell another 33% into strength if it stretches to **8–10× ATR% from the 50-MA** after day 4.

**Standing principles:** always sell *some* into strength — but not too aggressively (backtests show extended leaders keep trending for months; partial, never full, exits into strength). Never lose two weeks' gains in a single day. Add to winners at fresh valid setups (flag breakouts), never to losers. Performance growth comes from managing existing trades well, not finding more trades.

---

## 10. Journaling: The Feedback Loop That Builds the Edge

Non-negotiable. Trading is a big-data game you run on yourself; the largest performance gains come from analyzing you, not the market.

Track per trade: date, ticker, setup type, market condition tag, entry, stop, size, LoD-distance at entry, RVOL at entry, ATR% extension at entry, exits with reasons, R result, and screenshots (entry day + exit day). Then monitor:

- **Win rate, average R win, average R loss** (target: avg loss ≤0.7R), **profit factor**
- **R distribution / P&L histogram** — the whole system rests on the right tail
- **Average holding period of winners vs losers** (losers should be shorter — cut faster)
- Rule-violation tags: every loss gets audited against Section 7 gates. (One trader found 90% of a month's losses would've been avoided by just two gates: 30-min ORB entry + LoD <60% rule.)
- Equity curve vs SPY; every trade annotated on the index chart
- **Monthly review** (non-negotiable) + quarterly deep-dive: which setups, market regimes, and rule-breaks drive your numbers. Even flat YTD, your *process* stats may show you've improved — measure it.

Benchmarks of what's possible with this exact math: ~6% monthly compounding ≈ +100%/yr; documented low-win-rate/high-R years like 27% win rate → +114%.

Drawdown protocol: he survived 3 consecutive losing months in 2022 — cut size hard, keep executing A-setups only, rebuild with progressive exposure. Reducing activity alone doesn't fix a drawdown; better selection does. "When fishermen cannot go to sea, they repair nets" — flat markets are for screen calibration, journal study, and backtesting.

---

## 11. Daily Routine (Full-Time, US Market Hours)

**Post-close the prior evening (60–90 min) — the real work:**
1. Run the 6 daily screens (Finviz + TradingView) → tag new names into the global watchlist
2. Prune watchlist (delete disrupted charts) → promote/demote stalk list → build tomorrow's **focus list** (A-rated only)
3. For each focus name: pivot alert, stop level, position size, earnings check
4. Situational awareness read (Section 6): breadth, ratios, sectors/groups, index ATR extension
5. Review open positions: T+3 status, stop adjustments queued for tomorrow, partial-profit levels
6. Journal today's executions while fresh

**Pre-market (30–45 min before open):**
1. Re-set/confirm all price alerts (this ritual builds feel for where the market is)
2. Scan pre-market gappers vs focus/stalk lists (gap-up exception candidates; gap-risk checks on holdings)
3. Economic calendar + earnings calendar — no entries in front of releases
4. Check index futures vs yesterday's extension read; set the day's aggression level (how many of the 3 allowed entries you'll actually use)
5. Physical training before the open if possible — his strong recommendation for mental clarity

**The open (9:30–10:00):**
- Watch, don't trade (unless extreme RVOL from the bell). Monitor live RVOL screeners (focus-list-based + gapper-based) and your alert stream.
- At ~10:00, evaluate M30 ORH triggers against the Section 7 gates. Execute max 3, stops in on fill.

**Rest of session:** manage existing positions only (partials into strength, ORL stop mechanics). Avoid new market orders in the sleepy midday. No revenge trades, no boredom trades — if there's no fat pitch, the day's work was already done last night.

---

## 12. What the Independent Backtests Say (Why to Trust the Numbers)

The article links third-party tests of its own core heuristic — rare and worth weighting:

- **theStrat Lab (May 2026, ~2,700 tickers, ~1.9M candles):** extension above the 50-SMA is bell-curve distributed — ~2.5× ATR = 1σ (normal), ~5× = 2σ (stretched), **7.5–8× = 3σ (rarest 0.3%)**. His "trim into 7–10×" zone is genuinely extreme territory; his "don't enter past 4×" sits at the edge of normal.
- **Trading Time Machine (June 2026, 25 years of Nasdaq-100, survivorship-corrected, 2,250 parameter combos):** buying high extension **underperforms random over the next 5 days** (validates the no-chase entry rule) — but extended stocks **outperform dramatically over 30–150 days** (e.g., 50-SMA+7.5× entries: profit factor 3.46 vs 1.74 random at 120-day holds). Extension marks *persistent momentum*, not imminent reversal.
- **Net lesson encoded in this plan:** never chase extension at entry; trim *partials* into 7–10× strength; but let the runner trail on the 10-MA rather than fully exiting — the trend usually isn't done.

---

## 13. Implementation Ramp (First 12 Weeks)

- **Weeks 1–2 — Infrastructure.** Install the 4 indicators, build all screens on both platforms, build watchlist structure, sizing spreadsheet, journal template. Paper-run the full daily routine end-to-end.
- **Weeks 3–6 — Live at minimum size (0.25% risk).** Goal is NOT profit; it's zero rule violations. Every trade audited against the Section 7 gates. Build the focus-list muscle: most days the right answer is no trade.
- **Weeks 7–12 — 0.5% risk if compliance is clean.** Start monthly reviews. Only scale toward 1% risk when your own journal shows: avg loss ≤0.7R, at least one 3R+ winner captured to full 10-MA exit, and no chase entries for a month.
- **Ongoing:** trade A-rated setups only; in bad tape, expect long idle stretches — that's the system working. Three years of committed, journaled reps is his stated apprenticeship horizon.

---

## 14. Glossary (Quick Reference)

- **ADR% / ATR:** Average Daily Range % / Average True Range — volatility measures
- **RVOL:** volume vs its average at the same time of day (typically 50-day basis)
- **LoD / ORH / ORL:** low of day / opening-range high / opening-range low
- **M30 Re-ORH:** reclaim of the 30-minute opening range high
- **X× ATR% from 50-MA:** (% above 50-SMA) ÷ ATR% — volatility-normalized extension
- **VARS:** Volatility-Adjusted Relative Strength — per-bar (stock Δ ÷ stock ATR) − (SPY Δ ÷ SPY ATR), summed over a lookback
- **VCP:** volatility contraction pattern — tightening price/volume before expansion
- **R:** initial risk (entry − stop). All results measured in R-multiples
- **T+3:** execution day plus 3 trading days — the management framework window
- **PEG / PEAD:** post-earnings gap / post-earnings announcement drift
- **Pocket pivot:** up-day volume exceeding the largest down-day volume of the prior 10 days

---

## 15. Recommended Deepening (From the Article)

Books he names: *Japanese Candlestick Charting Techniques* (Steve Nison) and *Phantom of the Pits* (free online — source of "the best loser is the long-term winner"), plus his "three core structural books" thread. Traders he endorses studying: Qullamaggie (the strategy's closest ancestor — breakouts, 10/20-MA trailing, sell-into-strength), BrianLeeTrades, LoneStockTrader, Stockbee's YouTube library, and Stanley Druckenmiller interviews for top-down thinking.

## Sources

- [The Complete Trader's Guide — Jeff Sun (main article)](https://jfsrev.substack.com/p/my-trading-tools-process-routine)
- [Jeff Sun's Method and Flow — qullamaggie.net (2023)](https://qullamaggie.net/jeff-suns-method-and-flow/)
- [Risk and Position Management With Jeff Sun — The Trading Resource Hub](https://tradingresourcehub.substack.com/p/risk-and-position-management-jeff-sun)
- [Martin Luk +283% USIC 2024 Key Lessons — The Trading Resource Hub](https://tradingresourcehub.substack.com/p/martin-luk-283-usic-2024-key-lessons)
- [Backtesting Jeff Sun's 50 SMA ATR Extension Heuristic — theStrat Lab](https://thestratlab.substack.com/p/backtesting-jeff-suns-50-sma-atr)
- [Does ATR Extension Predict a Reversal? — Trading Time Machine](https://backtest.substack.com/p/does-atr-extension-predict-a-reversal)
- TradingView scripts: [Swing Data](https://www.tradingview.com/v/uloAa2EI/) · [ATR% multiple from 50-MA](https://www.tradingview.com/script/oimVgV7e-ATR-multiple-from-50-MA/) · [VARS](https://www.tradingview.com/script/nbgyYwu1-Volatility-Adjusted-Relative-Strength-VARS-Histogram-Option/) · [Simple Volume with Pocket Pivots](https://www.tradingview.com/script/JkB0iCFp-Simple-Volume-with-Pocket-Pivots/)

**Known gaps:** Chapter 17 of the article is paywalled; his "hard rule #15" and exact personal VARS settings are X-subscriber-only; a few mechanics (re-entry sizing table, some chart examples) live in tweet images that can't be text-verified. Nothing in those gaps changes the core system above.
