# Hybrid Daily Checklist

**Companion to `hybrid-buy-the-dip-strategy.md`.** Run top to bottom. Deliberately few parts.

Legend: **[G]** = binary gate, one failure kills the trade.

> **Changed in Rev 2 — three rules you must unlearn:**
> 1. **No fixed profit target.** The "+1.5R to +2R first trim" is deleted. It cost ~20–25% of expectancy. Time-stop the stagnant trades; let winners run on a trailing MA.
> 2. **ADR% is now a ceiling (2–5%), not a floor.** A 1-ATR stop on an 8–10% daily-range name gets swept by noise while the trend continues.
> 3. **This is a trend system, not a bounce trade.** Expect ~50% win rate with big winners — not 70% with small ones.
>
> **Changed in Rev 3 — five more:**
> 1. **Time stop is now T+10 (<0.5R → exit) and T+30 (<1R → exit).** The old T+3–5 cull contradicted the reference backtest's own 30-day window. Winners have **no time limit** — 1–2 month holds are the intended outcome.
> 2. **No full position ever holds through an earnings print.** <+2R the day before → exit fully. ≥+2R → exit or keep ≤half, sized so a 3×ATR gap costs ≤0.75% of equity.
> 3. **Sizing is a ladder** (0.5% → 1% → 1.5% → 2% at 30/100/200-trade gates) with a **40%-of-equity position cap** (~$10k today). Stage moves only at the monthly review.
> 4. **Pullback count starts at zero when a name joins the Leader Watchlist** — pre-qualification pullbacks are evidence for the proxies, not trades against the count.
> 5. **PDT doesn't apply** (cash 401(k) account). Instead: redeploy exit proceeds **next session, never same-day** (good-faith violation rule).

**Settings this checklist assumes** (full spec in Appendix A of the strategy doc): daily chart · **simple** MAs (10/20/50/200) on close · **ATR(14)** · **ADR% = 20-day average of (high÷low−1)** · "rising" = 50-SMA above its value 10 sessions ago, 200-SMA above its value 20 sessions ago · extension = (% above 50-SMA) ÷ ADR% · LoD distance = (entry − session low) ÷ ATR(14) · long only, US stocks and ETFs · Fidelity BrokerageLink cash account.

---

## PART A — POST-CLOSE (30–45 min)

### A1. Screens (~10 min)

- [ ] Pullback-in-leader screen: above **rising 50-MA** and **rising 200-MA**, within ~2–4% of the 20/50-MA, positive 3–6 month relative strength
- [ ] ADR% band filter: **2–5%**. Reject above ~6%
- [ ] Optional cross-check: Jeff's Mean Reversion Screener For Pull Back Entry

**Health check:** under **60** raw names. If more, tighten — never expand.

### A2. Leader Watchlist (names you may eventually buy)

- [ ] Trend stack intact: above rising 50-MA **and** rising 200-MA
- [ ] **≥2 of 4 persistence proxies:**
  - [ ] Last **two** pullbacks to the 20-MA both held and recovered ← *best single filter*
  - [ ] Closed above the 20-MA on **≥70% of last 50 sessions**
  - [ ] Advance is **linear**, not violent chop
  - [ ] Prior up-leg came on volume expansion
- [ ] ADR% in band; liquidity clears your size
- [ ] **Solvency veto passed** (A3)
- [ ] **Delete** anything whose trend stack or structure broke

### A3. Two-minute fundamental check (per new candidate)

**Solvency veto — binary, ~60 seconds:**

- [ ] Cash runway adequate; no imminent dilution or financing cliff
- [ ] No covenant breach or refinancing wall in your holding window
- [ ] No going-concern language, fraud allegation, or delisting risk

**One-line news test** — *why is it down?* ______________________

- [ ] ✅ **Best:** no company-specific news (rotation, market beta, profit-taking)
- [ ] ⚠️ **OK:** known, dated, already-priced catalyst
- [ ] ❌ **Reject:** negative earnings revision or guidance cut — *even in a quality name*
- [ ] ❌ **Reject:** you can't name the reason

> Counterintuitive but peer-reviewed: fundamental *strength* doesn't make a dip bounce. The **absence of fundamental news** does. Skip the deep valuation model — it has no measurable edge at a swing hold, and it tempts you to hold through your stop.

### A4. Focus List prep (per name — a handful max)

- [ ] Pullback into the **20-MA or 50-MA** zone, structure intact
- [ ] **Pullback count** = ____ — counted **since the name joined the Leader Watchlist** (1st/2nd = full size · 3rd = half · 4th+ = pass). Pre-listing pullbacks fed the proxies; they don't count here
- [ ] Trigger written down: ________________ (10/20-MA reclaim · prior day high · 30-min ORH)
- [ ] Alert set at trigger
- [ ] Invalidation / stop level = $______ → must sit **≤1 ATR** below entry
- [ ] Shares pre-computed (Part C)
- [ ] Earnings **≥5–6 sessions** away — no exceptions · **next earnings date noted:** ______

### A5. Regime throttle (~5 min)

- [ ] **[G]** Index above a **rising 200-MA**? Below a declining one → **no dip buying at all**
- [ ] **Chop check — two keys required:** ① last 5–10 entries: 3+ straight failures? ② market state: flat index 20/50-MA, or leaders failing their reclaims? **Both ① and ② → half size or sit out.** A streak alone is chance (~every 8 trades at 50%); the tape confirms it or it doesn't count
- [ ] Index extension: cautious near 4×, extreme at **6–7×** ATR% from 50-MA
- [ ] Flush day → wait for the **turn**, not the first red candle
- [ ] Tomorrow's max entries: **0 / 1 / 2 / 3** → ____

### A6. Open positions + journal

- [ ] **T+10** with cushion <**0.5R** → queue exit at open (no halving — one action)
- [ ] **T+30** with cushion <**1R** → queue exit at open
- [ ] **Earnings within 1 session on any holding?** Run the §5.3 rule: <+2R → exit fully · ≥+2R → exit or keep ≤half, kept shares ≤ (0.0075 × equity) ÷ (3 × ATR). **Never a full position through a print**
- [ ] Trail check on daily close: close below trailing MA (**20-MA default** · 10-MA only if parabolic, ≥5× extended) → **sell at next open**, no re-deciding
- [ ] Disaster stops raised to max(last swing low, trailing MA − 0.5×ATR) — up only
- [ ] Log: entry, stop, R, ADR%, LoD distance, pullback count, persistence proxies, one-line reason it was down, next earnings date, exit reason, R result, NAV units
- [ ] Time-stopped a trade? Log its **T+30/trail counterfactual** when it resolves

---

## PART B — PRE-MARKET (10–15 min)

- [ ] Confirm alerts
- [ ] Gap check on Focus names and holdings
- [ ] Econ + earnings calendar — no surprise binaries; **re-verify earnings dates on all holdings (dates move)**
- [ ] Any queued exits from A6 (time stop, trail break, pre-earnings) → execute at the open
- [ ] Confirm today's max-entry number

---

## PART C — EXECUTION

**Session clock (ET):** 9:30–10:00 watch only, no entries · **10:00–11:30 the execution window** · 11:30–15:00 manage opens only · 15:00–16:00 exits and stop moves only.

*Can't watch the open? Use the daily-close variant: evaluate gates ~15:45, trigger = close back above the 10/20-SMA, and drop the LoD gate. Log it as a separate setup type.*

### C1. Wait for the trigger

- [ ] Do **not** buy because it's cheap
- [ ] Buy only when the **written reclaim** fires

### C2. Gates (any single failure = no trade)

- [ ] **[G]** On Leader Watchlist, solvency veto passed
- [ ] **[G]** Above **rising 50-MA and rising 200-MA** ← *most robust rule in the plan*
- [ ] **[G]** Pullback structure, not a waterfall breakdown
- [ ] **[G]** Dip passes the one-line news test
- [ ] **[G]** Pullback count ≤2, or sized down
- [ ] **[G]** Trigger fired as planned
- [ ] **[G]** **LoD distance ≤0.60 ATR** ← *one trader's audit: 90% of a month's losses avoided by this + 30-min ORB*
- [ ] **[G]** Stop **≤1 ATR** at genuine invalidation. Wider = pass
- [ ] **[G]** Earnings ≥5–6 sessions out
- [ ] **[G]** Max **2–3** new positions today
- [ ] **[G]** No chase — if it left without you, it's gone

*Soft preference (not a gate):* volume dried up into the low, then expanded on the reclaim. Jeff confirms RVOL gates **breakouts and flags, not mean-reversion entries** — so don't treat it as binary here.

### C3. Portfolio limits (check BEFORE sizing)

- [ ] **[G]** Open positions ≤ **5** (4 at Stage 1)
- [ ] **[G]** Total open heat + this trade ≤ **stage cap** (3% / 4.5% / 6% — §8.1 ladder)
- [ ] **[G]** Total notional + this trade ≤ **90%** of equity (cash account buffer)
- [ ] **[G]** Not funded by **today's** sale proceeds → redeploy next session (GFV rule)
- [ ] **[G]** ≤2 positions in this sector/theme (ETFs count as their underlying)
- [ ] **[G]** Not down **−2R** today → if you are, **stop trading**
- [ ] **[G]** Not down **−4R** this week → if you are, **half size**

### C4. Sizing (two formulas, smaller one wins)

```
Equity                $__________  (recomputed monthly, contributions included)
Ladder stage          1 / 2 / 3 / 4   →  Risk % = 0.5 / 1.0 / 1.5 / 2.0
Risk $                $__________   = equity × risk%
Entry                 $__________
Stop                  $__________
R per share           $__________   = entry − stop
Shares (risk)         ___________   = risk$ ÷ R per share
Shares (cap)          ___________   = (0.40 × equity) ÷ entry
SHARES                ___________   = the SMALLER of the two
                      → if the cap bound, accept the lower risk. NEVER widen
                        the stop to spend the risk budget.

Open heat before      ______%       Open heat after: ______%  (≤ stage cap)
Notional after        ______%       (≤90% of equity)
```

Optional 3-stop layering — **trade stop never moves, only exit sizing:**

```
⅓ out at 33% of the way to stop
⅓ out at 66%
⅓ out at full stop
→ expected full loss ≈ −0.67R
```

### C5. On fill

- [ ] **Hard stop in immediately.** A 1× stop you hesitate on becomes 2×, then 3×
- [ ] Mark the trailing MA (**20 default** · 10 only for parabolic legs) — **no price target**
- [ ] Note the time-stop dates — T+10: ______ · T+30: ______
- [ ] Note the next earnings date: ______ (§5.3 rule will fire the session before)
- [ ] Log all gate values

### C6. Rest of day

- [ ] Manage opens only
- [ ] No boredom trades, no revenge trades

---

## PART D — AFTER THE BUY

**Time stops (Rev 3 — the old T+3–5 cull is deleted; it truncated slow starters).**

- **T+10:** cushion < **+0.5R** → exit at next open. One action, no halving.
- **T+30:** cushion < **+1R** → exit at next open. (Matches the reference backtest's own 30-day window.)
- **Winners have no time limit.** A 1–2 month hold on the trail is the intended outcome. Log the T+30/trail counterfactual on every time-stopped trade.

**Winners: no target. Trail the 20-MA** (default — it's the line for multi-week holds). Switch to the **10-MA only when the leg is parabolic** (≥5× ATR% from the 50-MA). Evaluated on the **daily close only**; a close below = sell at next open, mechanically. Disaster stop rides at max(last swing low, trailing MA − 0.5×ATR), raised each morning, never lowered.

**Earnings (no exceptions, §5.3):** by the close before any print — open profit **< +2R → exit fully** · **≥ +2R → exit fully or keep ≤half**, kept shares ≤ (0.0075 × equity) ÷ (3 × ATR). Log holds as their own setup type. **A full position never holds through a print.**

**Only discretionary trim:** ⅓ at **7–10× ATR% from the 50-MA.** That's 3σ (rarest 0.3% of readings) — genuinely extreme, unlike a 2R move. Never fully exit into strength: extended leaders outperform over 30–150 days.

**Stop to breakeven:** unresolved in the evidence — Jeff does it at T+3, systematic testing says it cuts profit sharply. **Default to trailing actual structure**, and log both counterfactuals for 30 trades so your own data decides. Do tighten aggressively past **+4R**.

**Adds:** only to winners, only at a fresh valid setup. Never to losers. Adds obey the same 40% notional cap on the total position.

---

## THRESHOLD QUICK REFERENCE

| Gate | Value | Change history |
|---|---|---|
| Trend stack | above **rising 50-MA + rising 200-MA** | Rev 2, hard |
| "Rising" definition | 50-MA vs 10 sessions ago · 200-MA vs **20** sessions ago | **Rev 3 (200 was 10)** |
| ADR% | **2–5%** (ceiling, reject >6%) | Rev 2 (was a floor) |
| Persistence proxies | **≥2 of 4** | Rev 2 |
| Pullback count | **≤2** full size, 3rd half, 4th+ pass — **counted from Leader Watchlist qualification** | **Rev 3 re-based the count** |
| Pullback zone | 20-MA or 50-MA, orderly | Rev 2 |
| LoD distance at entry | **≤0.60 ATR** | unchanged (Jeff, verified) |
| Stop distance | **≤1 ATR** at invalidation | unchanged |
| Earnings leeway at entry | **≥5–6 sessions**, no exceptions | Rev 2 |
| **Earnings while holding** | day before print: **<+2R exit · ≥+2R keep ≤half**, gap-sized | **Rev 3 — new rule** |
| New positions / day | ≤2–3 | unchanged |
| **Risk / trade** | **ladder: 0.5% → 1% → 1.5% → 2%** at 30/100/200-trade gates | **Rev 3 (was 0.25–0.5%)** |
| **Position size cap** | **40% of equity** (~$10k today) — smaller of the two formulas wins | **Rev 3 — new** |
| First profit target | **NONE** | Rev 2 (deleted +1.5–2R) |
| **Time stop** | **T+10 <0.5R → exit · T+30 <1R → exit** · winners no limit | **Rev 3 (was T+3–5)** |
| Runner exit | trail **20-MA default** (10-MA parabolic only), daily close, sell next open | **Rev 3 (was 10-MA default)** |
| Only trim zone | 7–10× ATR% from 50-MA (3σ) | Rev 2 |
| RVOL | soft preference, not a gate | Rev 2 (verified) |
| Target avg loss | ≤0.7R | unchanged |
| Target payoff ratio | **≥1.8** | Rev 2 |
| Expected win rate | **45–55%** | Rev 2 |
| Screen sanity | <60 raw names | unchanged |
| Max concurrent positions | **5** (4 at Stage 1) | **Rev 3 (was 6)** |
| Max total open heat | **by stage: 3% / 4.5% / 6%** | **Rev 3 (was flat 3%)** |
| **Max total notional** | **≤90% of equity**, redeploy exits next session (GFV) | **Rev 3 — new (cash acct)** |
| Max per sector/theme | **2 positions** | Rev 2 |
| Daily circuit breaker | **−2R → stop trading** | Rev 2 |
| Weekly circuit breaker | **−4R → half size** | Rev 2 |
| Monthly circuit breaker | **−8% → drop one ladder stage** | **Rev 3 (was: back to 0.25%)** |
| **Chop throttle** | streak **AND** market-state confirmation, else full size | **Rev 3 (was streak alone)** |
| **Benchmark test** | NAV vs SPY at every 100 trades / 12 months; lag >3pts → halve sleeve | **Rev 3 — new** |

---

## THE FUNNEL

```
Screens              <60
Leader Watchlist     small, trend + solvency cleared
Focus List           a handful
Executed             0–3   ← most days ZERO
```

---

## THE FIVE NUMBERS THAT DECIDE EVERYTHING

Compute after every 30 trades — but know what each sample size can say. At N=30 only **compliance** numbers are real (violations, average loss); win rate is ±18 points of noise and the payoff ratio hinges on one or two outliers. **Sizing decisions wait for N=100.** At N≥100, your own data overrides every number in these documents.

```
Win rate            ______%   (45–55% is success, not failure)
Payoff ratio        ______    (target ≥1.8 — this IS the edge)
Average loss        ______R   (target ≤0.7R)
Per-ticker win rate ______    (under 35% after 10 tries → deprioritize, half size)
NAV vs SPY          ______    (lag >3pts annualized at 100 trades → halve the sleeve)
```

**Maxims:** This is a trend system, not a bounce trade. Buy weakness inside strength. The best dip has no news behind it. Never cap a winner. Chop bleeds you, not bear markets. Missing is free; chasing is expensive. Size is the payout of evidence, not confidence. No full position through a print. Beat the index or become it.
