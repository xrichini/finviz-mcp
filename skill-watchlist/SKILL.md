---
name: watchlist
description: Build a weekly US equity watchlist by combining Finviz sector/screener data with trading-skills technical scoring and PMCC option analysis. Use when user says "watchlist", "semaine", "weekly scan", "tickers à surveiller", or asks for trade ideas for the coming week. Requires finviz MCP and trading-skills MCP to be active.
---

# Weekly Watchlist Builder

Generates a structured watchlist every weekend in 6 steps:
macro regime → top sectors → candidate pool → conviction scoring → earnings filter → options setup.

## Quick start

Say: `/watchlist` or "lance le workflow watchlist"

Claude runs all steps automatically and delivers a formatted report.

---

## STEP 0 — Market Regime (SPY / QQQ / IWM)

Run first — determines the trade style for the entire session:

```
trading-skills:technical_indicators(symbol="SPY,QQQ,IWM", period="1mo", indicators="rsi,sma,macd,adx")
```

Interpret and set **REGIME** (used in Step 6 to pick trade style):

| Condition | Regime | Trade style |
|---|---|---|
| SPY above SMA50, RSI 50–70 | 🟢 BULL | PMCC, bull call spreads, stock longs |
| SPY above SMA50, RSI > 70 | 🟡 EXTENDED | Smaller size, favor spreads over naked longs, tighter stops |
| SPY below SMA50, RSI < 50 | 🔴 CAUTION | Bear call spreads, cash-secured puts on strong names only, no PMCC |
| SPY below SMA200 | 🚨 BEAR | Watchlist only — no new directional entries |

→ State the regime clearly at the top of the output report.

---

## STEP 1 — Sector Rotation Matrix

Run both in parallel:
```
finviz_get_sector_performance(period="Performance (Week)", top_n=11)
finviz_get_sector_performance(period="Performance (Quarter)", top_n=11)
```

Build a 2×2 matrix per sector:

| | Strong Quarter | Weak Quarter |
|---|---|---|
| **Strong Week** | ✅ CONFIRMED momentum → target | 🔄 ROTATION emerging → small size |
| **Weak Week** | ⚠️ DISTRIBUTION risk → avoid | ❌ OUT OF FAVOR → skip |

→ Select **top 3 sectors** (✅ CONFIRMED only, or 1 × 🔄 if < 3 confirmed).
→ Explicitly list sectors to AVOID.

---

## STEP 2 — Screener: Candidate Pool

For each of the top 3 sectors, run in parallel:
```
finviz_screen_new_highs(sector=S, min_market_cap="+Mid (over $2bln)", min_avg_volume="Over 500K", limit=25)
finviz_screen_optionable_bullish(sector=S, min_market_cap="+Mid (over $2bln)", limit=25)
finviz_screen_by_signal(signal="Channel Up", sector=S, min_market_cap="+Mid (over $2bln)", limit=20)
```
Plus once market-wide:
```
finviz_screen_by_signal(signal="Recent Insider Buying", min_market_cap="+Mid (over $2bln)", limit=20)
finviz_get_market_insiders(option="top week buys", limit=20)
```

→ Deduplicate across all screens. Track which screen(s) each ticker appeared in — used for conviction scoring in Step 3.

---

## STEP 3 — Conviction Score

For each deduplicated ticker, compute a **conviction score** (max 18 pts):

| Signal | Points |
|---|---|
| 52-week new high | +2 |
| Optionable bullish screen | +2 |
| Channel Up pattern | +1 |
| Recent insider buying (ticker-level finviz screen) | +3 |
| Top week buys (market-wide, same ticker) | +3 |
| Perf week > +5% | +1 |

→ Keep tickers with **conviction ≥ 4 pts** for Step 4 (typically 15–25 candidates).
→ Apply bull scoring next; conviction will be boosted further.

---

## STEP 4 — Technical Scoring (trading-skills)

Pass all conviction ≥ 4 candidates (max 25 tickers):
```
trading-skills:scan_bullish(symbols="T1,T2,...", period="3mo", top_n=15)
```

Add to conviction score:
- Bull score ≥ 6.0 → +2 pts
- Bull score ≥ 7.0 → +2 pts (cumulative: +4)
- Bull score ≥ 8.0 → +2 pts more (cumulative: +6)

→ Keep tickers with **final conviction ≥ 6 pts** AND **bull score ≥ 6.0**.
→ Typically 8–12 candidates remain.

---

## STEP 5 — Earnings Intelligence Filter

For all remaining candidates, check earnings from `scan_bullish` output (`next_earnings` field):

| Earnings timing | Action |
|---|---|
| **≤ 5 days away** | ❌ EXCLUDE from watchlist — too binary |
| **6–14 days away** | ⚠️ FLAG "Wait for print" — hold off entry, monitor post-earnings |
| **15–30 days away** | 📌 FLAG "IV elevated" — premium selling opportunity (CSP, short spreads), note IV% |
| **> 30 days away** | ✅ CLEAN entry — preferred candidates |

→ After exclusions, **top 8–10 tickers** proceed to options scan.

---

## STEP 6 — Options Viability (PMCC scan)

```
trading-skills:scan_pmcc(symbols="T1,...", leaps_delta=0.80, short_delta=0.20)
```

Add to conviction score:
- PMCC score ≥ 8 → +2 pts
- Short spread ≤ 10% → +1 pt (tight/liquid)

Discard PMCC if short bid/ask spread > 25% → label as **"stock play only"** or **"LEAPS only"**.

Apply Regime filter from Step 0:
- 🟢 BULL → PMCC, bull call spread, stock long all valid
- 🟡 EXTENDED → prefer spreads (defined risk), reduce LEAPS size
- 🔴 CAUTION → CSP on strong names only, no PMCC
- 🚨 BEAR → list tickers for monitoring only, no entries

---

## STEP 7 — Deep Dive (top 3–5 only)

For the final shortlist, sorted by conviction score descending:
```
finviz_get_ticker_full_info(ticker)
```

Flag immediately if any of:
- Insider selling **at or above current price** in past 30 days → ⚠️ INSIDER SELL
- Analyst downgrade in past 14 days → ⚠️ DOWNGRADE
- Dilution event (secondary offering, convertible) in past 30 days → ⚠️ DILUTION
- Short float > 20% → 📌 SQUEEZE WATCH (can be bullish catalyst)
- Analyst upgrade in past 14 days → ✅ UPGRADE BOOST (+2 conviction)

---

## Output Format

```
## 📅 WATCHLIST — [Date]

### 📊 Market Regime: [🟢/🟡/🔴/🚨] [BULL / EXTENDED / CAUTION / BEAR]
SPY RSI [X] | SMA50 [above/below] | QQQ [status] | IWM [status]
→ Trade style this week: [PMCC / Spreads / CSP only / Monitor only]

### 🌍 Sector Rotation
✅ Confirmed: [Sector A], [Sector B]
🔄 Emerging: [Sector C] (small size)
❌ Avoid: [Sector D], [Sector E]

### 🏆 Final Watchlist — [N] tickers

| Rank | Ticker | Société | Sector | Price | Conv. | Bull | PMCC | Earnings | Setup | Flags |
|------|--------|---------|--------|-------|-------|------|------|----------|-------|-------|
| 1 | GLW | Corning | Tech | $148 | 14/18 | 6.5 | 9/10 | Apr 28 📌IV | PMCC | — |
| 2 | VRT | Vertiv | Tech | $261 | 12/18 | 6.5 | 8/10 | Apr 29 📌IV | PMCC | — |
| 3 | FSLY | Fastly | Tech | $33 | 10/18 | 7.0 | 8/10 | May 6 ✅ | Stock/LEAPS | spread illiq. |

### 💡 Top 3 Trade Ideas
[For each: Setup type | Entry | Strikes + Expiry | Capital req. | Max profit | Thesis 2 lines]

### ⚠️ Risques & signaux d'alerte
[Insider sells, dilution, macro shift, sector distribution signals]

### 🗑️ Exclus
[Tickers close to cut + reason: earnings < 5d / illiquid / conviction < 6]
```

---

## Runtime Parameters

| Parameter | Default | Override |
|---|---|---|
| Min market cap | +Mid ($2B+) | "inclure small caps" → "+Small" |
| Min avg volume | Over 500K | "plus liquide" → "Over 1M" |
| Sectors | Auto top 3 | "focus tech et healthcare" |
| Bull score min | 6.0 | "sois plus sélectif" → 7.0 |
| Conviction min | 6 pts | "moins strict" → 4 pts |
| Max tickers output | 8 | "top 5 seulement" |
| Earnings window exclude | ≤ 5 days | "exclure < 14 jours" |

---

## Related files

- [ENHANCEMENTS.md](ENHANCEMENTS.md) — Roadmap: persistence JSON, perf tracker, Unusual Whales, backtesting
