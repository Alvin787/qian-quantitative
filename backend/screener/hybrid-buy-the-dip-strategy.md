# Hybrid Strategy: Buy the Pullback in Strength

**Personal style** (buy low → sell recovery) + **Jeff Sun process/risk math** + **narrow fundamental catalyst filter**

> Educational plan, not financial advice. Paper or minimum size until your own journal proves an edge.
>
> **Revision 2 — verified.** Every rule attributed to Jeff Sun below was checked line-by-line against the source article. Every rule *not* from him is tagged with what evidence supports it, and where the evidence is thin, that's stated. One rule from Revision 1 was removed because the evidence says it destroys the edge (see §1.2).
>
> **Revision 3 — calibrated to the actual account and fixed against adversarial review.** Five changes: **(1)** a risk-scaling ladder to 2%/trade and a 40%-of-equity single-position cap replace the vague "1% after the journal earns it" (§8.1), plus an explicit vs-SPY benchmark test (§2.2) — the goal in §2.0 is unreachable at 0.25–0.5% risk forever, and the ladder is the missing mechanism. **(2)** The pullback count now re-bases at Leader Watchlist qualification (§3.3, A6), fixing a contradiction where the best persistence filter disqualified every name it selected. **(3)** A written runner-through-earnings rule (§5.3) — with multi-week holds, every winner eventually meets a print, and the old plan had no rule for it. **(4)** Appendix C is filled in for the real account: Fidelity 401(k) BrokerageLink, cash basis — **PDT does not apply** (it's a margin-account rule), good-faith-violation rules do, and there is no tax drag. **(5)** The time stop moved from T+3–5 to **T+10 / T+30** (§8.3a): the old window contradicted the reference backtest's own 30-day time stop and truncated slow-starting winners; holds of 1–2 months are now the intended outcome for working trades.

---



## 1. Verification Summary (Read This First)



### 1.1 What checked out against Jeff's guide

[https://jfsrev.substack.com/p/my-trading-tools-process-routine?open=false#§chapter-2-charting-my-approach-using-tradingview](https://jfsrev.substack.com/p/my-trading-tools-process-routine?open=false#§chapter-2-charting-my-approach-using-tradingview)

All of these are confirmed verbatim or near-verbatim in the source, so you can rely on them:


| Claim used in this plan                                                                                         | Status                                 |
| --------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| He runs a **"Mean Reversion Screener For Pull Back Entry"** as one of his 14 post-market screeners              | ✅ Confirmed — Chapter 3                |
| **RVOL is a requirement for breakouts and flag consolidations, *not* for mean-reversion trades**                | ✅ Confirmed — his own FAQ, 12 Jun 2026 |
| Hard rule: no entry if **LoD distance already exceeds 60% of ATR**                                              | ✅ Confirmed — Chapter 6, hard rule #1  |
| Hard rule: no entry beyond **4× ATR% from the 50-MA**                                                           | ✅ Confirmed — hard rule #2             |
| Hard rule: **never enter against a declining 200-MA**                                                           | ✅ Confirmed — hard rule #7             |
| Hard rule: **max 3 new positions per session**; never chase even a day late                                     | ✅ Confirmed — hard rules #9, #10       |
| **3-Stop Strategy** caps loss at **−0.67R** instead of −1R; built for sub-40% win rates                         | ✅ Confirmed — Chapter 6                |
| **Price linearity** matters — avoid stocks that double in 3 months but yield a 10% win rate over 20–30 attempts | ✅ Confirmed — hard rule #16            |
| Biotech single names excluded for gap risk; shorts expressed as inverse-ETF longs                               | ✅ Confirmed — hard rules #3, #14       |
| Indexes: **6–7× ATR% from 50-MA** as the extreme zone                                                           | ✅ Confirmed — Chapter 2                |


**One correction to Revision 1's framing.** Jeff's fundamental screening does *not* live in his swing process. His quality-and-valuation screener ("High Velocity Quality Screener," weekly chart, 33 names in two months) is explicitly labeled **his personal long-term investment** process, separate from his swing execution. His CANSLIM screener is explicitly **not actionable** — it identifies which industry groups have earnings power. So when you bolt a fundamental gate onto a swing system, understand that you are adding something *he deliberately keeps out of it*. §5 rebuilds the gate so it earns its place.

### 1.2 The one thing that was wrong, and it mattered

Revision 1 told you to take a first partial at **+1.5R to +2R**. **Delete that rule.** It was the single largest defect in the plan.

The reasoning: your entire edge in this strategy lives in the **payoff ratio** (average win ÷ average loss). A fixed R-multiple profit target attacks precisely that number, and it selects against the trades that are *working*.

- A systematic trend-following study found that **across all combinations tested, every instance of partial profit taking reduced total return** versus not trimming.
- An Adaptrade optimization between a "scale out at target" system and a "scale out with trailing stop" system, held at matched 30% max drawdown, put the optimum at **zero allocation to the target version** — net profit rose from $82k to $129k with better profit factor and Sharpe.
- Bulkowski's worked examples show scaling out cutting a winner from $980 to $720 while *worsening* the loser from −$220 to −$330.
- Rough arithmetic on the pullback backtest in §1.3: trimming half at 1.75R when the average win is 2.55R costs about **0.2R per trade, ~20–25% of expectancy** — and that's optimistic, because a right-skewed win distribution means the mean is pulled up by a tail the trimmed half no longer rides.

**But doesn't Qullamaggie trim after a few days at a 25–30% win rate?** Yes, and the difference is the whole point. His trim is **time-based (3–5 days), not R-based.** A time trim exits trades that *haven't started working*. A 2R trim exits trades that *are* working. Opposite selection, opposite effect. §8 rebuilds the exits around this.

### 1.3 The framing error worth fixing in your head

You described this as buying low and selling the recovery — mean reversion. **What you are actually building is a trend-continuation system**, and that distinction changes what you should expect and how you should manage it.

Same testing engine, same 62 US large caps, same five years of daily bars, two strategies:


|                        | **Trend pullback** (what you're building) | **Oversold mean reversion** (what you *think* you're building) |
| ---------------------- | ----------------------------------------- | -------------------------------------------------------------- |
| Win rate               | 53.5%                                     | 56.8%                                                          |
| Avg win : avg loss     | +6.9% : −2.7%                             | +3.5% : −3.7%                                                  |
| **Payoff ratio**       | **2.55**                                  | **0.94**                                                       |
| Expectancy / trade     | +2.5%                                     | +0.38%                                                         |
| **Breakeven win rate** | **~28%**                                  | **~52%**                                                       |
| Cushion                | ~25 points                                | ~5 points                                                      |
| Avg hold               | ~7 days                                   | ~3 days                                                        |
| Trades                 | 1,199                                     | ~4,100                                                         |


The inversion is structural, not accidental. A **counter-trend** entry gets a near target (the mean is the destination) and a far stop (nothing supports you below). A **with-trend pullback** gets the mirror: a **near stop** (the rising MA is a clean invalidation line) and a **far target** (you're aligned with the trend and can ride it). Your tight stop isn't a constraint on this system — it's what *manufactures* the favorable payoff geometry.

Three consequences you need to internalize:

1. **Expect ~50–55% win rate, not 70%.** If you show up expecting Connors-style hit rates, you will abandon a correctly functioning system during a normal losing streak.
2. **The fat-left-tail worry doesn't apply to you.** That's a real pathology of oversold buying (one distribution study found 19 winners over 10% against 46 losers over 10%). Your risk is different — see #3.
3. **Your actual failure mode is directionless chop, not a bear market.** In a range, "pulled back to the MA" keeps firing, price doesn't continue, and you get swept out below the MA repeatedly. A bear market at least stops triggering your filter. §9 addresses this.

**Verdict on your original question:** Yes, buying dips to swing the recovery is a legitimate, evidence-supported strategy — arguably with a *better* risk-adjusted profile than chasing breakouts, and it fits your temperament. No, it is not "buy stocks that went down." It is **buy the first or second orderly pullback in a stock that is provably trending, with a stop at the point the trend is falsified.** And you must manage it like a trend system, not like a bounce trade.

### 1.4 Honest limits on the numbers above

- The 53.5%/2.55 figures come from **one practitioner engine, 62 names, 5 years** in a broadly bullish window. Its own authors flag bull-market beta, survivorship bias, no control baseline, close-price fills, and zero transaction costs — and volunteer that "a large share of the +2.5% per-trade expectancy is not pullback timing's doing but the market trending persistently's doing."
- All fills at the close. Real stops fill worse after an MA breaks, so **assume your average loss runs fatter than −2.7% and your payoff ratio lands below 2.55.**
- Treat every number here as a **prior to test against your own journal**, not a promise.

---



## 2. What This Strategy Is



### 2.0 The Goal

**The objective is to make the maximum amount of money this strategy is capable of producing — the largest ending account balance, not the best-looking win rate, the smoothest equity curve, or the most trades taken.** Every rule in this document exists because it serves that number, and any rule that stops serving it should be cut — **but only at the scheduled monthly review, in writing, with the journal evidence attached. Never intraday, and never during a week that tripped a circuit breaker.** Over a few hundred trades at a ~50% win rate you will hit a 7–8 trade losing streak while following every rule perfectly; that streak is not evidence against any rule, and "cut what stops serving the goal" read mid-drawdown is how systems die. Rule changes are a calm-month act.

Read the constraints in that light, because they are not caution — they are the mechanism. Maximum money means maximum **compounded** growth, and compounding is destroyed by drawdowns far more than it is helped by big single wins: a −50% month requires +100% to recover, so the risk caps in §8.5 exist to protect the compounding rate, not to make you timid. It also means the payoff ratio is the lever that actually moves the ending balance, which is precisely why the fixed profit target was deleted in §1.2 — capping winners feels like locking in money while quietly costing 20–25% of expectancy on every trade. And it means aggression has to be *selective* rather than constant: the fastest way to shrink the final number is to force trades in chop, so sitting out is an offensive act, not a defensive one.

Concretely, maximizing the ending balance in this system reduces to four things, in order of leverage: **(1)** keep the average loss ≤0.7R, **(2)** never cap the right tail, **(3)** press size only when the journal proves the edge and the regime is trending, and **(4)** stay in the game long enough for compounding to do the work. Anything that raises the ending balance is in scope — the §8.1 ladder scales risk per trade to a **2.0% ceiling** and position size to **40% of equity** as the evidence arrives, and strong tape gets traded aggressively. What's out of scope is any single decision that can end the account, because the strategy can only maximize money it still has. One 401(k)-specific reason that matters more here than in a taxable account: **money lost inside the 401(k) cannot be replaced beyond the annual contribution limit.** A blown-up taxable account can be refilled; this one can't.

### 2.1 The Method

**One sentence:** Buy the first or second orderly pullback in a liquid, provably trend-persistent stock, enter on a reclaim with a stop at trend invalidation, time-stop the trades that don't work, and let the ones that do run on a trailing MA without a price target.

**Three edge sources, and each does one job only:**


| Source                       | Job                                                                   | Explicitly NOT its job       |
| ---------------------------- | --------------------------------------------------------------------- | ---------------------------- |
| **Trend selection**          | Decide *which* names are eligible                                     | Timing                       |
| **Risk math** (Jeff)         | Keep the average loss small so the payoff ratio survives              | Prediction                   |
| **Catalyst/solvency filter** | Veto names that can gap to zero; prefer dips with no fundamental news | Overriding a stop, or timing |


The third one is the newest and weakest — §5 states plainly which parts of it have evidence and which don't.

### 2.2 The benchmark test (new in Rev 3 — the goal's honesty check)

§1.4 already concedes that "a large share of the +2.5% per-trade expectancy is... the market trending persistently's doing." Take that seriously and the max-money goal acquires an unavoidable test: **these dollars must grow faster in this system than they would sitting in an index fund inside the same 401(k), or the max-money move is to index them.** The old plan never measured this. Now it does.

**How to measure it with paycheck contributions flowing in** (a simple % return is distorted by deposits): use **unit accounting**. Start at NAV = $100/unit, units = equity ÷ 100. Each contribution buys new units at the current NAV; NAV itself only moves with trading results and market moves on holdings. NAV growth is your time-weighted return. Track SPY total return over the same window in the same journal.

**The rule:**

- At every **100-trade review** (or every 12 months, whichever comes first): if NAV growth trails SPY total return by **more than 3 percentage points annualized** *with clean rule compliance*, move **half** the account into the plan's index funds and keep trading the remainder. The trading sleeve earns its allocation back with two consecutive review periods at or above the benchmark.
- If compliance was *not* clean, the comparison is void — fix compliance first; you haven't tested the system yet.
- If the account was throttled to cash by the regime filter (§9.1) during a bear leg, note it: sitting out a −20% index drawdown **is** outperformance, and the comparison window should span the full cycle, not just the rebound.

This isn't defeatism — it's the same logic as the stop. The stop caps a losing trade; the benchmark caps a losing *strategy*. Both exist so the compounding continues somewhere.

---



## 3. Universe (Hard Filters)

- **Liquidity:** avg dollar volume high enough that your size is noise. Prefer **>$20–50M**; Jeff keeps a fixed list above **$1B** for mega caps. His own slippage once cost 6–7% of a year's equity. Hard filter, not a preference.
- **Trend stack (hard):** price above a **rising 50-MA** and a **rising 200-MA**. No exceptions for this style.
- **ADR% ceiling, not floor — this reverses Revision 1.** See §3.1.
- **Trend persistence over raw volatility.** See §3.2.
- **No biotech single names.** Confirmed hard rule; gap risk breaks stop math. Express biotech via IBB/XBI/LABU/LABD.
- **Earnings:** ≥5–6 sessions of leeway, no exceptions (§5.3).



### 3.1 Why the ADR% guidance flipped

Revision 1 told you to prefer high ADR% "so the bounce can be large." That imported a rule from a system with different mechanics, and for a **1-ATR-stop pullback entry it is actively harmful.**

- The pullback backtest's failure mode, in its authors' words: *"A stop hugging the MA gets swept by intraday noise or a gap on a high-beta stock with an 8–10% daily range, and then the trend continues — you're in the right trend but keep getting shaken out by noise."*
- Its per-name dispersion is brutal. Best: **MRK 70%, MSFT 69%, MU 68%, AVGO 67%**. Worst: **AAPL 21% (−1.0% per trade), COIN 25%, XOM 31%, ABBV 33%**.
- An independent volatility-filter sweep on a mean-reversion system found annualized return and Sharpe **declining rapidly once ATR(5) exceeds 3%**.

Counter-evidence, in fairness: academic work finds momentum returns are *higher* among high-idiosyncratic-volatility stocks (0.47%/mo lowest-beta bucket up to 0.99%/mo highest), and one RSI(2) study found ranking by normalized ATR *improved* Sharpe. **The resolution is that these measure different things.** Academic studies measure portfolio returns with no stops. You trade with a tight stop. High volatility appears to improve the raw signal while degrading tight-stop execution — and **with a ~1 ATR stop, the execution effect dominates.**

Note the trap: sizing your stop in ATR units auto-widens it in dollars on volatile names, but it does **not** protect you against gaps, and it doesn't help when the daily range is large relative to the pullback depth you're trying to buy.

**Rules:**

- Target **ADR% roughly 2–5%.** Enough range to pay for the stop, not so much that noise sweeps it.
- Above ~6% ADR%, either **pass** or widen the stop and cut size proportionally — while accepting that widening the stop compresses the payoff ratio that justifies the whole approach. This tension has no clean resolution in the evidence. Prefer passing.
- Jeff's own ADR% ≥3–4% floor and his leveraged-ETF preference belong to his **breakout** system, where entries are at range highs and RVOL confirms. Do not import them here. Leveraged ETFs are optional at most, only on the cleanest trends, sized down.



### 3.2 Trend persistence filter (the AAPL-21% fix)

The operative variable in that dispersion table is **not market cap** — MRK and AAPL are both mega caps and sit at opposite extremes. It's **trend persistence.** Mean reversion wants stable, rangebound names; pullback buying wants names that trend persistently in one direction. If you screen for momentum leaders and then apply bounce logic, your screen and your signal point in opposite directions.

Concrete proxies — require **at least two**:

- [ ] The last **two** pullbacks to the 20-MA both **held and recovered** (this is the single best filter — you're buying a behavior the stock has demonstrated)
- [ ] Price closed above the 20-MA on **≥70% of the last 50 sessions**
- [ ] Advance is visually **linear**, not a staircase of violent whipsaws (Jeff's confirmed hard rule #16)
- [ ] Prior up-leg came on a **volume expansion** (institutional footprint)

**Maintain a per-ticker scorecard.** After ~10 attempts on a name with a win rate under 35%, **deprioritize** it — trade it only when nothing cleaner is on the Focus List, at half size. (Rev 3 softened this from "blacklist": 10 attempts is a small sample — a genuinely 50% name shows ≤3/10 about one time in six — and at ≤2 tradeable pullbacks per trend cycle, hard-blacklisting on 10-trade noise throws away good names. The scorecard's real job is the *pattern across names*: if your losers cluster in one sector or one volatility band, that's the signal worth acting on.)

### 3.3 Pullback count — re-based in Rev 3 to stop contradicting §3.2

Pullback quality decays across a trend. The 4th or 5th pullback after a long run carries materially different risk from the 1st or 2nd, and this style **will always hand back the last trade or two at the end of every trend.**

**The Rev 2 contradiction, fixed.** Proxy #1 in §3.2 — the "single best filter" — requires the last **two** pullbacks to have held and recovered. But the old counting rule started the count at trend confirmation, so those two demonstration pullbacks *were* pullbacks #1 and #2 — meaning any name that passed the best filter could only ever be bought at half size (#3) or not at all (#4+). The filter and the count were selecting for opposite things, and the document silently resolved it in the worst direction.

**The fix — re-base the count at qualification:** the pullback count starts at **zero when a name qualifies (or re-qualifies) for the Leader Watchlist.** Pullbacks before qualification are the *evidence* — they feed the §3.2 proxies. Pullbacks after qualification are the *trades* — they feed the count. One demonstrated behavior, two separate jobs, no double-counting.

**Rule:** trade the **1st or 2nd** pullback after Leader Watchlist qualification at full size. 3rd at half size. 4th+ requires a fresh multi-week base or a new catalytic gap on volume (either of which also re-bases the count to zero). Tally the count in your notes for every name. The §3.3 decay logic still holds — a name that's been on the list through four pullbacks *has* aged as a trend, no matter where the count started.

---



## 4. The Two Lists

Skip Jeff's 100–150 name global watchlist. Two lists.

### A. Leader Watchlist (weekly build, light daily refresh)

- Trend stack intact: above rising 50-MA and rising 200-MA
- Passes **≥2 of the 4 persistence proxies** (§3.2)
- ADR% in the **2–5%** band
- Liquidity clears your size
- Passes the **solvency veto** (§5.1)
- Industry group not collapsing



### B. Focus List (the only names you may buy)

Leader names now pulled back and turning:

- Pullback to the **20-MA or 50-MA** zone, orderly, structure intact
- **Pullback count ≤2**, or sized down per §3.3
- A **written trigger**: reclaim of the 10/20-MA, prior day's high, or the 30-min opening-range high
- A stop that can sit **≤1 ATR** below entry at genuine invalidation

Most days: **0–3 names on Focus, zero executions.** That is the system working.

---



## 5. The Fundamental Filter (Rebuilt — Read the Evidence)

This is where Revision 1 was most speculative, so here is the honest split.

### 5.1 What has NO evidence at your holding horizon

**Quality and valuation screening does not predict returns over days to weeks.** A survivorship-bias-free study of S&P 500 value factors (1998–2013) found ranked portfolios and linear models produce "at best weak performance" and concluded the factors "are not useful for constructing portfolios." AQR's framing: valuation has real power over a decade, and CAPE has "very little utility for forecasting the S&P 500's return over the next month or year." A practitioner warning that lands directly on your style: *a value trap can drift sideways for weeks, killing a swing trade's time value.*

So P/E, ROIC, DCF fair value, and a Shkreli-style multi-tab model **do not belong in your entry decision.** Building one per ticker would burn hours and add no measurable edge at a days-to-weeks swing hold. If you enjoy the modeling, run it as a **separate long-term investing sleeve** — which is exactly how Jeff partitions it.

**Worse: the gate turns negative the moment it makes you hold through invalidation.** "The balance sheet is fine, so I'll give it room" is the exact thought that destroys this system, because the entire payoff geometry depends on honoring the stop. No controlled test exists showing a fundamental gate improves a technical pullback system in either direction — treat it as plausible-but-unproven and keep it small.

**What survives from Shkreli's approach is one thing only: a solvency veto.** Not a valuation. Not a price target. A yes/no on whether this company can gap to zero or dilute you 40% while you hold it.

**Solvency veto (60 seconds, binary):**

- [ ] Cash runway adequate — no imminent dilution or financing cliff
- [ ] No covenant breach or refinancing wall inside your holding window
- [ ] No going-concern language, no active fraud allegation, no delisting risk

Fail any → the name never reaches Leader Watchlist. That's the whole check. A stock above a rising 200-MA rarely fails it, which is the point: it's a cheap tail-risk filter, not an analysis project.

### 5.2 What DOES have evidence

**Earnings-based fundamentals work at your horizon; quality/value doesn't.** Different animal entirely:

- Earnings momentum — standardized unexpected earnings, announcement-window abnormal returns, analyst revisions — predicts returns, and price momentum and earnings momentum each add **incremental predictive power over the other.**
- The earnings-announcement component of momentum holds across the US, Europe, and Japan over three decades, doesn't load on factor momentum, and shows no reversal. **Caveat: short-term PEAD has faded**; the durable version aggregates announcement windows over a year.
- An independent systematization of Qullamaggie's episodic pivot found EPS change QoQ, EPS surprise magnitude, and *low* prior 30-day rate of change all improved the raw signal.

**The most useful and least intuitive finding — this is the one to actually use.** Da, Liu & Schaumburg showed that returns **unexplained by fundamentals** are the ones that revert. Isolating the non-fundamental component of a decline produced **four times** the risk-adjusted return of the standard reversal strategy (3-factor alpha 1.34%/month, t = 9.28; still 0.54%/month after ~80bp costs, t = 3.90).

Read that again, because it inverts what you assumed: **fundamental strength is not what makes a dip bounce. The absence of fundamental news is.** A dip on sector rotation, index flows, or no identifiable reason is a *better* buy than a dip on a genuine earnings downgrade — even if the downgraded company is still high quality.

**Practical version — the one-line news test:**

- [ ] Write, in one sentence, why it's down.
- [ ] **Prefer:** no company-specific fundamental news. Rotation, market beta, profit-taking, sympathy selling. ✅ **best case**
- [ ] **Acceptable:** a known, dated, priced catalyst
- [ ] **Reject:** negative earnings revisions, guidance cut, or a genuine estimate-cutting event — even in a quality name
- [ ] **Reject:** you cannot name the reason at all

That test takes a minute per name and is the highest-value piece of fundamental work in the plan.

### 5.3 The conflict your two components create

Your fundamental gate selects for earnings momentum. Earnings momentum lives **near earnings dates.** Meanwhile: *"a below-consensus report can drop a strong stock through every MA overnight, filling the stop far worse than expected and wiping out the near-stop structural advantage in one shot."* The near stop is the entire basis of your 2.55 payoff ratio, and an earnings gap is the one event that voids it.

**Non-negotiable at entry:** **≥5–6 sessions of earnings leeway.**

**The runner-through-earnings rule (new in Rev 3 — this was a hole).** The entry gate only protects the entry. With winners trailed for weeks to months (§8.3), **every successful runner will eventually hold into an earnings date** — earnings come every ~63 sessions, and the trades funding the entire payoff ratio are exactly the ones still open when one arrives. The old plan's answer ("that is a different trade with different sizing") wasn't a rule, and you can't retroactively resize a position you already hold. The decision is written now, so it never gets made live with a +4R position and a full head of conviction:

- **Mark the next confirmed earnings date on every position at entry**, and re-check it weekly (dates move).
- **By the close of the last session before the report:**
  - Open profit **< +2R → exit the entire position.** There isn't enough cushion to pay for a gap; the stop is inoperative through it (§8.2's math simply doesn't exist overnight).
  - Open profit **≥ +2R → exit fully, or keep at most half** — and the kept half must be small enough that a **3×ATR adverse gap costs ≤0.75% of equity**: `max shares kept = (0.0075 × equity) ÷ (3 × ATR)`. Whichever of "half" and that formula is smaller wins.
  - **Never hold a full-size position through a print. No conviction exceptions** — conviction is the thing this rule exists to overrule.
- Log every hold-through as its own setup type ("earnings hold"). After ~20 of them, your journal decides whether the kept half earns its gap risk; until then it's an experiment, not an edge.
- Same treatment for any scheduled binary specific to the name (FDA-adjacent events are already excluded via the biotech ban, but think analyst days with guidance, court rulings, contract awards with dates).

---



## 6. Screens (Few, Restricted)

**Daily/near-daily** — keep the raw list under ~60 names:

1. **Pullback-in-leader screen** — above rising 50-MA and rising 200-MA, within ~2–4% of the 20-MA or 50-MA, positive 3–6 month relative strength
2. **ADR% band filter** — **2–5%**, and reject anything above ~6% (this is a *ceiling*, per §3.1)
3. **Optional:** Jeff's Mean Reversion Screener For Pull Back Entry (confirmed to exist) as a cross-check

**Weekly:** re-verify the trend stack and persistence proxies; drop broken names; refresh the per-ticker scorecard.

**Never expand screens to manufacture trades.** Restrict until the list is manageable.

---



## 7. Entry Rules (Binary Gates)

Any failure = no trade. An A-rated setup still becomes a C-rated execution if you skip these.

1. **On Leader Watchlist** and past the solvency veto.
2. **Trend stack intact** — above rising 50-MA and rising **200-MA**. This gate carries the most robust evidence in the plan (§9), so it never bends.
3. **Pullback, not breakdown** — orderly retracement into MA support, not a waterfall on expanding down-volume.
4. **Dip is not news-driven** — passes the §5.2 one-line test.
5. **Pullback count ≤2** (or sized down per §3.3).
6. **Trigger fires as written.** Never buy mid-air because it looks cheap.
7. **LoD distance ≤ ~0.60 ATR** at entry — Jeff's confirmed hard rule. One trader audited a month of losses and found **90% would have been avoided** by this plus a 30-min-ORB entry.
8. **Stop ≤ ~1 ATR** at genuine invalidation. Wider = pass. This gate *creates* your payoff ratio.
9. **Earnings ≥5–6 sessions out.**
10. **Max 2–3 new positions per day.**
11. **Never chase**, not even a day late.

**On RVOL:** verified — Jeff requires RVOL for breakouts and flags, **not** for mean-reversion entries. So it isn't a gate for you. Keep it as a **soft preference**: volume drying up into the low, then expanding on the reclaim, is a better tape than a reclaim on nothing.

**On the 4× extension gate:** confirmed as his hard rule, and worth keeping as a sanity check, but note it will rarely bind for you — a genuine pullback relieves extension by definition. If a "dip" is still 4×+ extended from the 50-MA, it isn't a dip.

**Order:** alert → gates → buy → hard stop in immediately. A 1× stop you hesitate on becomes 2×, then 3×.

---



## 8. Risk & Exits (Rebuilt — This Is the Most Changed Section)



### 8.1 Sizing — the ladder that turns the edge into money (rewritten in Rev 3)

Rev 2 stalled at "0.25–0.5%, maybe 1% someday," which made the §2.0 goal arithmetically unreachable: at the plan's own target expectancy (~0.28R/trade) and realistic frequency (2–5 trades/month), 0.5% risk compounds at roughly 4–8%/year — index-like results for two hours of daily work. The edge doesn't get bigger; **the size has to, on a defined schedule, as the evidence arrives.** That schedule is the ladder.

**Two formulas, applied in order, every trade:**

1. **Risk-based shares:** `shares = (equity × risk%) ÷ (entry − stop)`
2. **Notional cap:** position value ≤ **40% of current equity** (≈$10,000 on $25k — the stated single-trade maximum, expressed as a percentage so it scales with contributions). If the risk formula wants a bigger position, cut shares to the cap and accept the lower risk. **Never widen the stop to "use up" the risk budget** — the tight stop is the edge, not a constraint on it.

Because of the cap, effective max risk on any trade = `40% × stop distance`. A 3%-stop name caps at 1.2% risk regardless of ladder stage; a 5%-stop name (rare, given the ≤1 ATR gate and the 2–5% ADR band) caps at 2%. This is intentional: it's what "willing to put $10k into one trade" means after it's been translated into a rule that can't end the account.

**The risk ladder.** Stage moves happen **only at the monthly review** (§2.0), never mid-week. Equity (and therefore risk dollars) is recomputed at the start of each month, contributions included.


| Stage           | Risk/trade              | Max open heat | Advance when (all required)                                                                         |
| --------------- | ----------------------- | ------------- | --------------------------------------------------------------------------------------------------- |
| **0 — Paper**   | —                       | —             | 15+ paper setups logged; routine runs end-to-end; you can tell pullback from breakdown in real time |
| **1 — Prove**   | **0.5%** ($125 on $25k) | 3%            | **30 live trades, zero rule violations, avg loss ≤0.7R** (compliance stats — measurable at N=30)    |
| **2 — Earn**    | **1.0%**                | 4.5%          | **100 total trades**, payoff ratio ≥1.8, positive expectancy, §2.2 benchmark met                    |
| **3 — Press**   | **1.5%**                | 6%            | **200 total trades**, survived a 5+ losing streak without a violation, still clearing §2.2          |
| **4 — Ceiling** | **2.0%**                | 6%            | Hard ceiling. There is no Stage 5.                                                                  |


**Demotions:** monthly circuit breaker (−8% equity in a month) → drop **one stage** until a green month. Two breaker months in a row → Stage 1 and a full journal audit before re-climbing.

**Why the ceiling is 2% and not higher, given your higher risk tolerance.** At a 45–55% win rate, a 7–10 trade losing streak is *routine* over a few hundred trades — not a tail event. At 2% risk with 0.7R average losses that streak costs ~10–14% of equity: recoverable, and the monthly breaker catches it. At 4–5% risk the same ordinary streak costs 25–35%, and §2.0 already did the arithmetic on what that does to compounding — plus the 401(k) asymmetry: capital lost here can't be replaced beyond the annual contribution limit. Your risk tolerance is expressed through **how fast the ladder climbs and the 40% position cap**, not through a bigger per-trade number. Stage 4 is 4–8× the old plan's risk; the ladder just refuses to pay it out ahead of the evidence.

### 8.2 The stop

- Placed at **genuine trend invalidation** — below the swing low or decisively below the MA you bought — and **within ~1 ATR** of entry.
- **Keep it tight, and know why this is the opposite of standard mean-reversion advice.** Connors and Alvarez famously found that on mean-reversion systems, *"in every single case, the use of stops lowered the performance. Even the 50% stop had a lower performance than no stop."* Cesar Alvarez replicated it independently. **That finding does not apply to you**, and the reason is the crux of this whole document: in a counter-trend entry, price moving against you *improves* the signal, so there's something to wait for. In a with-trend pullback, a decisive break of the rising MA **falsifies the premise.** The trend is no longer intact. There is nothing to wait for.
- **3-stop layering (optional, from Jeff):** exit ⅓ at 33% of stop distance, ⅓ at 66%, ⅓ at full stop → expected loss ≈ **−0.67R**. The trade's stop level never moves; only exit *sizing* is layered. He built this explicitly for sub-40% win rates, and it also softens gap damage. It's the one loss-side refinement worth the complexity.



### 8.3 Exits — no fixed profit target

**The rule from Revision 1 is deleted. There is no +1.5R or +2R trim.**

**a) Time stop (this replaces the R-target trim) — rewritten in Rev 3 for the longer holding horizon.** The old T+3–T+5 window contradicted the plan's own reference backtest: the engine that produced the 53.5%/2.55 anchor numbers gave its pullback trades **30 days** (the 5-day time stop belonged to the *mean-reversion* system, the one this plan explicitly isn't). Pullback entries routinely chop near the MA for a week before the trend resumes, so demanding ~1R inside three sessions was a fast-start filter with no evidence behind it — the same class of right-tail truncation §1.2 deleted, just applied to slow starters instead of fast winners. New schedule, with working trades allowed to run **1–2 months**:

- **T+10:** cushion **< +0.5R → exit.** One action, not "exit or halve" — under stress, every either/or gets resolved in the position's favor, so the rule doesn't offer one.
- **T+30:** cushion **< +1R → exit.** Aligned with the reference backtest's own time stop. A trade that's gone nowhere in six weeks is dead capital in a system whose §2.0 goal is compounding rate.
- **Winners have no time limit.** The trail (b) is the only exit for a working trade. A 1–2 month hold riding the 20-MA is the *intended outcome*, not an exception.
- For every time-stopped trade, **log the T+30 / trail-exit counterfactual** — where it would have finished. That data, not this document, tunes the windows (Appendix D #4).

**b) Winners: no target. Trail them — with exact mechanics, because this rule produces 100% of the system's profit.** Trailing is the correct exit for trend-continuation, because the runner-extension distribution dominates expected value. Rev 3 makes the **20-SMA the default trail** — it's the line consistent with the 1–2 month holds this system now intends; the 10-SMA shakes out too many multi-week runners. Switch a position to the **10-SMA only when its leg has gone parabolic** (extension ≥5× ATR% from the 50-MA, the 2σ zone from (c)), where giving it back to the 20 would surrender too much. Don't outsmart these lines. Mechanics, so there's nothing to decide live:

- The trail is evaluated **once per day, on the daily close.** A close below the trailing MA = **sell at the next open.** No pre-market re-deciding, no "it's recovering" — the close decided.
- Between evaluations, the live broker stop is the **disaster stop**: it starts at the entry stop and each morning is raised to the higher of (i) the most recent genuine swing low, or (ii) the trailing MA value minus 0.5× ATR. It only ever ratchets **up**.
- Intraday touches of the MA are noise by definition here. Only the close counts.

**c) The only discretionary trim — genuine 3σ extension.** theStrat Lab's study across ~~2,700 tickers and ~1.9M candles found extension above the 50-SMA is bell-curve distributed: **~~2.5× ATR = 1σ, ~5× = 2σ, 7.5–8× = 3σ (rarest 0.3%)**. So trimming ⅓ at **7–10× ATR% from the 50-MA** is trimming into statistically extreme territory — not into a normal 2R move. That is defensible; a 2R target is not.

**d) Do not fully exit into strength.** Trading Time Machine's 25-year survivorship-corrected Nasdaq-100 test (2,250 parameter combos) found extended stocks **underperform random over the next 5 days** but **outperform dramatically over 30–150 days** (50-SMA + 7.5× entries: profit factor 3.46 vs 1.74 random at 120-day holds). Extension marks *persistent momentum*, not imminent reversal. Trim partials; never close the runner into strength.

**e) Stop to breakeven — genuinely unresolved, so don't mandate it.** Jeff moves to breakeven at T+3. But independent testing found that *"setting the maximum-loss stop to the break even price dramatically reduces profit"* because it forces exits on trades that would have been profitable. Qullamaggie and the systematic evidence disagree here and I won't pretend otherwise. **Default: trail under actual structure rather than snapping to breakeven, and log both counterfactuals in your journal for 30 trades so your own data resolves it.** Do move the stop up aggressively past **+4R** — a parabolic gain should never return to a loss.

**f) Adds:** only to winners, only at a fresh valid setup, never to losers. Once your book is past T+3, Jeff's stated priority is adding to proven positions over opening new names.

### 8.4 Expectancy, honestly


|                    | Reference pullback backtest | Your realistic target |
| ------------------ | --------------------------- | --------------------- |
| Win rate           | 53.5%                       | **45–55%**            |
| Payoff ratio       | 2.55                        | **1.8–2.5**           |
| Avg loss           | −1R (−0.67R with 3-stop)    | **≤0.7R**             |
| Breakeven win rate | ~28%                        | ~30–35%               |


**A ~50% win rate is a success, not a problem.** Your two obsessions are average loss and payoff ratio — nothing else moves the needle. And expect the reference numbers to degrade: real fills are worse than close-price fills.

### 8.5 Portfolio-level risk (per-trade risk alone is not enough)

Per-trade risk controls one trade. These control the account. Without them, six "safe" 0.5% positions in the same sector is a 3% single-factor bet, and this style clusters hard — pullbacks in leaders tend to happen *simultaneously*, because they're all responding to the same market pullback.


| Limit                              | Value                                                           | Why                                                                                                           |
| ---------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Max concurrent positions**       | **5** (4 at Stage 1)                                            | The 40% notional cap and a cash account make 6 unreachable anyway; 5 is what you can actually manage stops on |
| **Max total open heat**            | **By ladder stage: 3% → 4.5% → 6%** (§8.1)                      | The number that actually caps a bad day — it scales with proven edge, same as per-trade risk                  |
| **Max total notional**             | **≤90% of equity**                                              | Cash account: no margin, and a settlement buffer so a fresh setup is never blocked by unsettled funds         |
| **Max per sector / theme**         | **2 positions**, or half the current heat cap                   | Correlation is the hidden risk in this style                                                                  |
| **Daily stop-out circuit breaker** | **−2R in a day → stop trading, no new entries**                 | Prevents the revenge spiral                                                                                   |
| **Weekly circuit breaker**         | **−4R in a week → half size until a green week**                | Drawdown control that doesn't require willpower                                                               |
| **Monthly circuit breaker**        | **−8% equity → drop one ladder stage** and re-audit the journal | Jeff's own drawdown protocol: cut size, keep executing A-setups only                                          |


**Heat, defined:** open heat = Σ (current shares × (entry basis − current stop)), counting only risk still live. Once a stop is trailed above entry, that position contributes zero heat and frees capacity. This is what makes trailing stops compounding-friendly. *(Rev 3 fixed a sign error in this formula — it previously read stop − entry.)*

**Cash-account mechanics (Fidelity BrokerageLink):** PDT does **not** apply — that's a margin-account rule. What applies instead is settlement: sale proceeds settle **T+1**, and a **good-faith violation** occurs if you buy with unsettled proceeds and then sell *that new position* before the funding sale settles. Three GFVs in 12 months = 90 days of settled-cash-only. Practical rule: entering a new position the day after an exit is always safe; entering the *same day* as an exit is fine only if you won't be stopped out of it same-day — which you can't promise. **So: capital freed by an exit is redeployed no earlier than the next session.** With ≤90% notional and 4–5 positions this rarely binds.

**Correlation note:** leveraged ETFs, sector ETFs, and their underlyings count as the *same* position for these limits. Two semis names in a semis drawdown is one bet.

---



## 9. Market Regime Throttle



### 9.1 The 200-MA filter — the most robust rule in this document

This finding replicates across sources and is worth more than any setup refinement:

- Buying 5% index dips **above** the 200-SMA gives usable short and medium holds with a smoother curve. **Below it**, "performance deteriorates badly, and many hold periods stay negative unless you hold long enough to grind back" — ugly across 1–40 day holds, not recovering until **~35+ days**. The author's conclusion: *"If you're under the 200-day SMA, 'buying the 5% dip' is not the same trade anymore."*
- **Average daily volatility above the 200-MA is 1.05%; below it, 2.1%.** It roughly doubles. That single number is why your ATR-based stops behave differently in the two regimes.
- On RSI(2), adding the 200-MA filter raised average gain per trade from 0.9% to 0.95% and cut max drawdown from 34% to 31% — while cutting CAGR from 9% to 6.8% and time invested from 28% to 18%. Better trade quality, less opportunity. A real tradeoff, not a free lunch.
- **Slope matters as much as level.** Across 120 years, when the 200-SMA was already *declining* before a break below, "the decline was sustained in every serious case (2000, 2008, 2022)"; when still *rising*, breaks "almost always resolved within days to weeks."
- Refinement worth noting: 200-day rising + price below the 50-day produced ~24.3% annualized, rising to ~26.4% if the 50-day is also rising and ~29.5% with price still above the 200-day. That's close to a quantitative endorsement of your entry premise — index-level and blog-published, so weight accordingly.

**Rule: no dip buying below a declining 200-MA, in the index or the stock.** This also matches Jeff's confirmed hard rule #7.

### 9.2 The chop detector (your actual enemy)

*"A trend strategy's real enemy isn't a bear market but a directionless chop."* A bear market stops triggering your filter. A range triggers it constantly and fails every time — AAPL's 21% win rate is the live example. **The 200-MA filter does not solve this**, which is why you need a second read:

- [ ] Are my **last 5–10 pullback entries** working or failing? (Qullamaggie's simplest tell, echoed by Jeff.)
- [ ] Is the index oscillating around a **flat** 20/50-MA rather than trending along a rising one?
- [ ] Are leaders holding their pullbacks, or reclaiming and immediately failing?

**Rev 3 changed how these combine — the throttle requires two keys, not one.** Cut to half size or sit out only when a **personal streak (3+ consecutive failures) AND at least one market-state check** (flat index MAs, or leaders failing their reclaims) agree. A streak alone is not chop: at a ~50% win rate, three straight losses occur by pure chance every ~8 trades, and a payoff-ratio system earns its whole year in a handful of trades that cluster right when a pullback regime resolves upward — de-sizing on personal streaks alone systematically has you at half size for exactly those trades. The market-state checks are the *signal*; your streak is only the prompt to go look at them. (This matters even more at your trade frequency: "last 5–10 entries" looks back one to three months, and a regime that old may already be over.)

### 9.3 Standard throttles

- Breadth healthy and indexes not extremely extended → normal size. Jeff's index extreme zone is **6–7× ATR% from the 50-MA** (confirmed), with reluctance to add risk around 4×.
- Capitulation flush days generate the best setups for this style — but **wait for the turn**, don't buy the first red candle of a crash.
- **Momentum winners carry their own left tail.** Daniel & Moskowitz measured monthly skewness of **−0.82** for the top winner decile (vs +0.09 for losers) and **−4.70** for the long-short portfolio. Crashes are partly forecastable — they occur in *panic states*, after market declines and when volatility is high — and they *"take place slowly, over the span of multiple months."* So screening for strong leaders imports a tail risk that arrives as a **persistent regime**, not a single gap. Which means §9.2 is your defense, and it works: you have time to notice.
- Never initiate into major binary events unless deliberately sized for it.

---



## 10. Jeff's Rules: Take / Adapt / Leave

**Take unchanged (all verified):**

- Process funnel: screen → watch → focus → mechanical execution, with decisions made post-market
- Fixed % risk to equity; 3-stop layering to −0.67R
- LoD ≤60% ATR gate
- Max 3 new positions/session; never chase
- No entry against a declining 200-MA; no biotech single names
- Price linearity requirement (hard rule #16)
- Earnings leeway; no entry before major data
- Journal + non-negotiable monthly review
- "Always seek reasons NOT to trade"

**Adapt:**

- **ADR%:** his floor (≥3–4%) becomes your **band (2–5%)** — §3.1
- **RVOL:** his hard gate becomes your soft preference — he confirms it doesn't apply to mean-reversion entries
- **Trigger:** range-high breakout becomes **MA reclaim / prior-day-high / 30-min ORH**
- **4× extension:** keep as a sanity check; it rarely binds on genuine dips
- **T+3 breakeven stop:** his T+3 decision point becomes the **T+10 / T+30 time-stop schedule** (§8.3a) — his horizon was days, this system's is weeks to two months; trail structure instead of snapping to breakeven until your own data settles it (§8.3e)

**Leave:**

- Pure range-breakout hunting as the only setup
- The 100–150 name global watchlist bureaucracy
- Leveraged ETFs as a default instrument (raises ADR% in the direction that hurts you)
- His long-term quality/valuation screener — that's his *investing* sleeve, and mixing it into swing decisions is how you end up holding through a stop

**Add (yours, evidence-tagged):**

- **Trend persistence filter + per-ticker scorecard** (§3.2) — *well supported by the dispersion data; the single highest-leverage addition*
- **Pullback count ≤2** (§3.3) — *moderately supported*
- **Solvency veto** (§5.1) — *tail-risk protection, no return evidence claimed*
- **"Dip has no fundamental news" test** (§5.2) — *peer-reviewed (Da/Liu/Schaumburg); the best fundamental idea in the plan*
- **Chop detector** (§9.2) — *well supported as the primary failure mode*
- **Time stop replacing the R-target trim** (§8.3a) — *well supported*

---



## 11. The Ramp (milestone-based — Rev 3 deleted the calendar)

Rev 2's "10-week ramp" demanded 30+ trades by week 9 from a system whose own funnel says "most days: zero executions" — roughly 4 trades a week from a strategy that produces 2–6 a month. That mismatch had one likely resolution: loosening gates to feed the schedule. So the schedule is gone. **Gates are trade counts and compliance, never weeks.** At realistic frequency, Stage 1 alone takes 5–10 months. That is the honest price, and the paycheck contributions mean the account is growing while you pay it.

The ramp *is* the §8.1 ladder — one table, no duplicate. What each stage is **for**:

- **Stage 0 (paper):** prove the *routine* — screens, lists, journal, sizing sheet, 15+ paper setups with every gate value logged even on skips.
- **Stage 1 (0.5%):** prove *compliance*. The goal is zero rule violations, not profit. The only stats that mean anything at N=30 are compliance stats: violations, average loss, chase entries. **Win rate and payoff ratio at N=30 are noise** — the 95% interval on a 30-trade win rate is roughly ±18 points, and the payoff ratio hinges on whether one or two outlier winners landed in the window. Don't let 30 lucky or unlucky trades resize the account.
- **Stage 2+ (1.0% and up):** prove *performance*, at N=100 and N=200 where the numbers start to mean something, against the §2.2 benchmark.

**Verification log — non-negotiable.** For every trade record: entry, stop, R, ADR%, LoD distance at entry, pullback count, persistence proxies passed, one-line reason it was down, **next earnings date**, exit reason, R result, **NAV units** (§2.2). After every 30 trades compute the five numbers: win rate, payoff ratio, average loss, per-ticker win rate, **NAV growth vs SPY**. **At N≥100, these numbers from your own data override every number in this document.**

Also log the counterfactual on three unresolved questions: (1) breakeven stop vs. structural trail, (2) the untrimmed result on any trade you trimmed, (3) **the T+30/trail-exit result on any trade the T+10 time stop culled.** That's how §8.3a and §8.3e get settled with evidence instead of opinion.

---



## 12. Maxims

- **This is a trend system, not a bounce trade.** Manage it as one.
- Buy weakness **inside strength** — the trend stack is not negotiable.
- **The best dip is the one with no news behind it.** Fundamental strength doesn't make a dip bounce; the absence of fundamental *news* does.
- Fundamentals decide *eligibility and survival*; price decides *timing*; **only the stop decides exit**.
- **Never cap a winner with a fixed target.** The payoff ratio is the entire edge.
- Tight stops don't limit this system — they *create* it.
- Chop, not bear markets, is what bleeds you. Watch your last 5 trades — then check the tape before you shrink.
- Think in 100 trades. Missing is free; chasing is expensive. The best loser is the long-term winner.
- **Size is the payout of evidence, not of confidence.** The ladder climbs on trade counts, never on a good week.
- **Beat the index or become it.** The benchmark test (§2.2) is a stop-loss on the strategy itself.
- **No full position ever holds through an earnings print.** The gap is the one event the stop can't survive.

---



## Appendix A — Exact Parameters (No Ambiguity)

Every number in this plan resolves to a specific setting here. If a rule and this table disagree, this table wins.

### A1. Indicators


| Item                   | Exact spec                                                                                                                        |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Decision timeframe** | **Daily** chart. Intraday (5-min / 30-min) is for execution only                                                                  |
| **Moving averages**    | **Simple** (SMA), on **closing** price: 10, 20, 50, 200                                                                           |
| **"Rising" MA**        | 50-SMA: today > **10 sessions ago**. 200-SMA: today > **20 sessions ago** (a 10-session test on a 200-day line flickers at turns) |
| **ATR**                | **ATR(14)**, daily, Wilder smoothing — the standard TradingView default                                                           |
| **ADR%**               | **20-day** average of `(daily high ÷ daily low − 1) × 100`. *Not* the same as ATR% — Jeff's Swing Data script computes it         |
| **Extension**          | `(% price is above the 50-SMA) ÷ ADR%` = the "×" multiple                                                                         |
| **LoD distance**       | `(entry price − session low at that moment) ÷ ATR(14)`. Gate is ≤0.60                                                             |
| **Relative strength**  | Stock's 3-month and 6-month % change vs SPY's. Both positive = pass. VARS optional                                                |
| **Avg dollar volume**  | 50-day average of `close × volume`                                                                                                |




### A2. Trigger definitions (pick one per name, write it down before the session)


| Trigger            | Fires when                                                                                    |
| ------------------ | --------------------------------------------------------------------------------------------- |
| **MA reclaim**     | Price trades above the 10- or 20-SMA after having closed below it, *and* holds for 5+ minutes |
| **Prior day high** | Price trades above the previous session's high                                                |
| **30-min ORH**     | Price trades above the high of the 9:30–10:00 ET range                                        |


Default to the **30-min ORH** if unsure — it's the most evidence-supported (§7, gate 7) and it forces you to skip the open's noise.

### A3. Session timing (US market hours, ET)

- **9:30–10:00** — watch only. No entries, regardless of how good it looks.
- **10:00–11:30** — the execution window. Evaluate triggers against the §7 gates.
- **11:30–15:00** — manage open positions only. No new entries in the midday drift.
- **15:00–16:00** — exits and stop adjustments only.
- **Post-close** — the real work (Part A of the checklist).



### A4. Order mechanics

- **Entry:** buy-stop order placed just above the trigger level, or a market order on confirmation. Never a limit order below the market "hoping" for a better fill — that's how you get filled only on the losers.
- **Stop:** **stop-market**, live in the broker, entered immediately on fill. Not mental, not stop-limit — a stop-limit can leave you unfilled in exactly the gap it exists to protect against.
- **Trailing:** the MA trail is evaluated **on daily closes** — a close below the trailing MA means **sell at the next open**, mechanically. Each morning the resting disaster stop is raised to the higher of the last genuine swing low or (trailing MA − 0.5×ATR); it only ratchets up (§8.3b). Don't use an automated percentage trail.
- **Redeployment (cash account):** capital freed by an exit is deployed **no earlier than the next session** — avoids good-faith violations by construction (§8.5).



### A5. Instrument scope

- **US-listed common stock and ETFs, long only.** Bearish views are expressed as longs on inverse ETFs (Jeff's hard rule #14).
- **Excluded:** biotech single names, OTC/pink sheets, anything under $5, anything under the liquidity floor, and stocks with earnings inside 5–6 sessions.
- **Leveraged ETFs:** permitted but discouraged (§3.1) — they push ADR% the wrong way for a tight-stop system. If used, count them against sector limits and size down.



### A6. Trend confirmation and pullback counting (re-based in Rev 3)

- **Trend confirmed** when price closes above a **rising 50-SMA** with a **rising 200-SMA** beneath it, after a prior up-leg on volume expansion.
- **The count starts at zero on the day the name qualifies for the Leader Watchlist.** Pullbacks before that date don't count against the limit — they are the evidence the §3.2 persistence proxies consume.
- **Pullback #1** = the first touch of the 20- or 50-SMA after qualification.
- The count **increments** on each subsequent touch, and **re-bases to zero** when the stock builds a fresh multi-week base or delivers a new catalytic gap on volume.
- If the trend stack breaks (close below a flat/declining 50-SMA), the name leaves the Leader Watchlist and the count re-bases to zero on re-qualification.

---



## Appendix B — Glossary

- **R** — the initial risk on a trade, in dollars per share: `entry − stop`. All results are expressed in multiples of it. A "+2R" trade made twice what it risked.
- **Payoff ratio** — average winning trade ÷ average losing trade, in R. **The single most important number in this system.**
- **Expectancy** — `(win% × avg win) − (loss% × avg loss)`, in R per trade.
- **Breakeven win rate** — the win rate at which expectancy hits zero, given your payoff ratio: `1 ÷ (1 + payoff)`.
- **ATR** — Average True Range. Absolute volatility in dollars.
- **ADR%** — Average Daily Range percent. Volatility as a percentage.
- **LoD / HoD** — low / high of the current session.
- **ORH / ORL** — opening-range high / low, here the 9:30–10:00 ET range.
- **RVOL** — relative volume versus the average at the same time of day, 50-day basis.
- **T+N** — N *trading* days after the execution day. Weekends and holidays don't count. This plan's time stops sit at **T+10** and **T+30** (§8.3a).
- **Notional cap** — maximum position value: 40% of current equity (§8.1). Binds before risk% does on tight-stop names.
- **Disaster stop** — the resting broker stop while a winner trails its MA: raised each morning, never lowered (§8.3b).
- **GFV** — good-faith violation: selling a position that was bought with not-yet-settled proceeds in a cash account (§8.5).
- **NAV / units** — unit accounting that makes returns comparable to SPY despite paycheck contributions (§2.2).
- **3-Stop Strategy** — Jeff's loss-layering method: exit thirds at 33%, 66%, and 100% of the distance to the stop, producing an expected loss of ≈−0.67R instead of −1R. The stop *level* never moves; only the exit sizing is staged.
- **Open heat** — total live risk across all open positions, as a % of equity.
- **Pullback count** — how many times a stock has retraced to its 20/50-SMA since trend confirmation. See A6.
- **Trend stack** — price above a rising 50-SMA above a rising 200-SMA.
- **Persistence proxies** — the four §3.2 tests measuring whether a stock actually respects its own trend.
- **Chop** — a directionless range that repeatedly triggers pullback entries and fails them. The primary failure mode of this system.
- **VCP** — volatility contraction pattern. Tightening range before expansion.
- **PEAD** — post-earnings announcement drift.

---



## Appendix C — Your Context (Filled In, Rev 3)

These are the personal inputs the rules depend on, now resolved against the actual account.

```
Account equity              $25,000 — grows with every paycheck (401k contributions).
                            Recompute equity and risk $ at the start of each month.
Broker                      Fidelity 401(k) BrokerageLink
Cash or margin              Cash (retirement accounts have no margin)
PDT                         DOES NOT APPLY — PDT is a margin-account rule. What binds
                            instead: T+1 settlement and good-faith violations (§8.5).
                            Rule of thumb: redeploy exit proceeds next session, never
                            same-day. 3 GFVs in 12 months = 90 days settled-cash-only.
Can you watch 9:30-11:30 ET? Y → intraday variant is primary: LoD ≤0.60 ATR gate live,
                            30-min ORH is the default trigger, A3 session clock applies
Risk per trade (current)    0.5% — Stage 1 of the §8.1 ladder ($125/trade today).
                            Ceiling: 2.0% at Stage 4. Advance only at monthly review.
Max single position         40% of equity (≈$10,000 today — scales with the account)
Max concurrent positions    4 (Stage 1) → 5 from Stage 2
Max open heat               3% (Stage 1) → 4.5% → 6% per the ladder
Max total notional          90% of equity (settlement buffer)
Idle cash                   Stays in the BrokerageLink core money-market position —
                            it earns while you wait. Sitting out is paid, not idle.
Taxes                       None inside the 401(k): no short-term capital gains drag —
                            a genuine structural edge for a high-turnover style.
                            The flip side (§2.0): losses can't be replaced beyond the
                            annual contribution limit. Blow-up protection matters MORE
                            here, not less.
Data / charting             TradingView Free tier
Screener                    Finviz Free tier
Journal                     Google Sheet — must carry the §11 columns, including
                            next-earnings-date and NAV units (§2.2)
```

**Fallback if life changes and you can't watch the open:** use a **daily-close trigger** (price closes back above the 10/20-SMA) with entry on the close or next open, and replace the LoD ≤0.60 ATR gate (it's an intraday measure) with two daily proxies: day's range ≤1.5× ATR **and** close in the upper 40% of the day's range. Log it as a separate setup type — the proxies are untested substitutes and your journal has to validate them.

---



## Appendix D — Open Questions and Known Gaps

Stated plainly so nobody mistakes an unknown for a rule.

1. **Breakeven stop vs. structural trail** (§8.3e) — Jeff and the systematic evidence genuinely disagree. Log both counterfactuals for 30 trades.
2. **High-ADR names: pass, or widen the stop and cut size?** (§3.1) — no clean resolution in the evidence. Current default is *pass*.
3. **Whether the fundamental filter adds anything at all** (§5) — no controlled test exists in either direction. It is currently justified as tail-risk protection plus the news test, not as a return enhancer.
4. **Optimal time-stop windows** — Rev 3's T+10 (<0.5R) / T+30 (<1R) are anchored to the reference backtest's 30-day stop but the T+10 cull is still a judgment call. Log the T+30/trail counterfactual on every time-stopped trade; that data tunes both windows.
5. **Exact screener syntax** — §6 and A1 define the logic, not the platform-specific filter strings. Build them once in TradingView/Finviz and record the saved-screen URLs here.
6. **No backtest of this exact rule set exists.** Every number in §1.3 and §8.4 comes from adjacent studies. This is the largest gap and the reason for the paper-trading phase.
7. **The earnings-hold half position** (§5.3) — keeping ≤half of a ≥+2R winner through a print is a written rule but an untested one. It's an experiment until ~20 logged earnings holds say otherwise; the conservative alternative (always exit fully) is always available.
8. **The 2.0% ladder ceiling** (§8.1) — derived from streak arithmetic and the 401(k) refill asymmetry, not from a test. If your realized average loss holds ≤0.6R and payoff ≥2.2 at N≥200, revisiting the ceiling at a monthly review is legitimate; doing it mid-streak is not.

---



## Sources / Lineage

**Primary:**

- [Jeff Sun — The Complete Trader's Guide](https://jfsrev.substack.com/p/my-trading-tools-process-routine) — every attributed rule verified against this text
- Your distilled version: `master-trading-strategy.md` · Execution companion: `hybrid-daily-checklist.md`

**Payoff geometry (§1.3):**

- [Trend pullback backtest — 1,199 trades](https://momoview.com/blog/en/posts/trend-pullback-buying-with-trend-vs-counter-trend-payoff-ratio-five-year-backtest-1199-trades/)
- [Oversold mean-reversion backtest — ~4,100 trades](https://momoview.com/blog/en/posts/mean-reversion-oversold-bounce-why-higher-win-rate-thinner-safety-margin-five-year-backtest-4100-trades/)

**Against fixed profit targets (§1.2, §8.3):**

- [Enlightened Stock Trading — partial profits in trend following](https://enlightenedstocktrading.substack.com/p/is-taking-partial-profits-in-trend)
- [Adaptrade — scale-out vs trailing at matched drawdown](https://www.adaptrade.com/BreakoutFutures/Newsletters/Newsletter0309.htm)
- [Bulkowski — scaling out arithmetic](https://thepatternsite.com/ScalingOut.html)

**Stops and mean reversion (§8.2):**

- [Connors — "Stops Hurt"](https://tradingmarkets.com/trading-tip/stops-hurt-1597528) · [Cesar Alvarez replication](https://bettersystemtrader.com/003-cesar-alvarez/)

**Volatility and ADR% (§3.1):**

- [Quantitativo — mean reversion and the volatility curve](https://www.quantitativo.com/p/trading-the-mean-reversion-curve)
- [Arena, Haggard & Yan (2008) — momentum and idiosyncratic volatility](https://epublications.marquette.edu/cgi/viewcontent.cgi?article=1001&context=fin_fac)
- [Price Action Lab — mean-reversion optimization space](https://www.priceactionlab.com/Blog/2025/01/the-huge-optimization-space-of-mean-reversion/)

**200-MA regime (§9.1):**

- [Algorithmic Guys — buying 5% dips above vs below the 200-SMA](https://algorithmicguys.substack.com/p/should-we-buy-or-sell-5-dips-in-the)
- [QuantifiedStrategies — 200-day MA volatility regimes](https://www.quantifiedstrategies.com/200-day-moving-average/) · [RSI-2](https://www.quantifiedstrategies.com/rsi-2-strategy/)
- [Elliott Gue — the 200-day line in the sand](https://freemarketspeculator.substack.com/p/the-200-day-line-in-the-sand)

**Fundamentals (§5):**

- [Da, Liu & Schaumburg — reversals unexplained by fundamentals](https://academicweb.nd.edu/~zda/Reversal.pdf) *(4× risk-adjusted improvement)*
- [SSRN 2407303 — S&P 500 value factors, survivorship-free](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2407303)
- [CFA Institute — Chan, Jegadeesh & Lakonishok on momentum strategies](https://rpc.cfainstitute.org/research/cfa-digest/1997/08/momentum-strategies-digest-summary)
- [IBKR Quant — factor vs stock components of momentum](https://www.interactivebrokers.com/campus/ibkr-quant-news/the-many-facets-of-stock-momentum-distinguishing-factor-and-stock-components/)

**Skew and tails (§1.3, §9.3):**

- [Daniel & Moskowitz (2016), JFE — momentum crashes](https://www.kentdaniel.net/papers/published/jfe_16.pdf)
- [Price Action Lab — skewness across strategy types](https://www.priceactionlab.com/Blog/2023/03/skewness-holy-grail-trading/)
- [QuantifiedStrategies — negatively skewed strategies](https://www.quantifiedstrategies.com/negatively-skewed-trading-strategies/)

**Extension studies (§8.3c–d):**

- [theStrat Lab — backtesting the 50-SMA ATR extension heuristic](https://thestratlab.substack.com/p/backtesting-jeff-suns-50-sma-atr)
- [Trading Time Machine — does ATR extension predict a reversal?](https://backtest.substack.com/p/does-atr-extension-predict-a-reversal)

**Comparison basis (§10):**

- [Qullamaggie — 3 timeless setups](https://qullamaggie.net/3-timeless-setups-that-have-made-me-tens-of-millions/) · [Niv Goren — modeling the episodic pivot](https://stonkscapital.substack.com/p/modeling-kullamagi-part-3-episodic)

**Known limits:** the most directly relevant pullback statistics come from a practitioner blog with a proprietary engine over a bullish 5-year window, not peer-reviewed work — its authors disclose bull-market beta, survivorship bias, close-price fills, and zero costs. Mean-reversion backtests are notorious for over-optimization; a single filter change in the Price Action Lab study swung max drawdown to ~72%. Chapter 17 of Jeff's guide is paywalled and his hard rule #15 is subscriber-only. **Assume every backtested edge here is inflated until your own journal confirms it.**