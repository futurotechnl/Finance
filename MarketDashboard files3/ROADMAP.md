# MarketDash — Project Roadmap & Build Log

## Current Build: v1.0
**File:** `market_dashboard_v1.html`
**Date:** May 2026
**Status:** ✅ Saved to GitHub

---

## What's Built (v1.0)

| Feature | Detail | Status |
|---|---|---|
| Live quotes | Finnhub API · All 36 tickers · 60s auto-refresh | ✅ Done |
| Vol traffic lights | Daily vol + intraday vol vs watchlist mean | ✅ Done |
| Vol signal colours | Bright green / Green / Bright red / Red / Grey | ✅ Done |
| Vol flash alerts | 3+ consecutive days of Bright signal → pulse + ⚡ badge | ✅ Done |
| MACD(12,26,9) | Polygon.io historical OHLC · 380-day lookback | ✅ Done |
| MACD vs MA 20/50/200 | Distance measured in histogram std dev (σ) units | ✅ Done |
| MACD signal tiers | Bright / Normal / Light green & red + Grey | ✅ Done |
| MACD flash alerts | 3+ consecutive days of Bright MACD signal | ✅ Done |
| Screener | 20-stock static DB · Filters · Sortable table · Sparklines | ✅ Done |
| Ticker detail modal | Vol signal + all 3 MACD MA signals in one popup | ✅ Done |
| Persistent storage | localStorage · Watchlist · Alerts · MACD cache · Vol means | ✅ Done |
| Shared ticker list | One watchlist across all three dashboards | ✅ Done |
| Batch MACD fetch | 4 tickers/min · Progress bar · Countdown · Daily cache | ✅ Done |
| Intl tickers (HK/DE/FR) | Live quote only — no MACD (Polygon free tier is US only) | ⚠️ Partial |

---

## Tickers Watchlist (36)

**US Stocks:** QCOM · BRK-B · AI · BAESY · OKLO · REK · SMR · BMNR · GOOGL · XHB · MSFT · AAPL · NVDA · TSLA

**US ETFs:** TLT · SRTY · QQQ · GLD · GDXU

**Crypto:** BTC-USD · ETH-USD

**HK Listed:** 0700.HK · 9988.HK · 1810.HK · 9899.HK

**Intl ADRs/OTC:** TCEHY · XIACY · FINMY · BAESY · BIDU · NTES · TME · IQ

**European:** RHM.DE · HO.PA · ATO.PA

---

## API Keys

| API | Purpose | Tier |
|---|---|---|
| Finnhub | Live quotes — all tickers | Free (60 req/min) |
| Polygon.io | Historical OHLC — US tickers only | Free (5 req/min) |
| Yahoo Finance | Planned — full intl historical OHLC via DB | Pending backend |

---

## Alert Rules Defined

### Vol Alerts (all tickers)
| Condition | Signal |
|---|---|
| Daily vol > 2× mean AND closed up | Bright green |
| Daily vol > 1× mean AND closed up | Green |
| Daily vol > 2× mean AND closed down | Bright red |
| Daily vol > 1× mean AND closed down | Red |
| Daily vol within 0.7×–1.3× mean | Grey |
| Bright signal sustained 3+ consecutive days | ⚡ Flash alert |

### MACD Alerts (US tickers — Polygon.io)
| Condition | Signal |
|---|---|
| MACD > MA by ≥ 2σ + bullish crossover | Bright green |
| MACD > MA by 1–2σ | Green |
| MACD > MA by 0.5–1σ | Light green |
| MACD < MA by ≥ 2σ + bearish crossover | Bright red |
| MACD < MA by 1–2σ | Red |
| MACD < MA by 0.5–1σ | Light red |
| MACD within ±0.5σ of MA | Grey |
| Bright signal sustained 3+ consecutive days | ⚡ Flash alert |

---

## Build Next — Priority Queue

### 1. 📊 More Technical Indicators
**File:** `market_dashboard_v2.html` ✅ In progress

| Indicator | Status |
|---|---|
| RSI(14) — momentum × zone combined | ✅ Done (v2) |
| Bollinger Bands (20,2) — %B + bandwidth/squeeze | ✅ Done (v3) |
| ATR(14) — vol regime rising/falling vs 20d mean | ✅ Done (v3) |
| ADX(14) — trend strength × DI+/DI− direction | ✅ Done (v3) |
| technicalindicators.js CDN library integrated | ✅ Done (v3) |
| Stochastic Oscillator — %K/%D crossover | 🔜 Next (v4) |
| OBV — On Balance Volume trend | 🔜 Next (v4) |
| StochRSI — more sensitive RSI variant | 🔜 Planned |

### 2. 🔔 More Alert Rules
**File will be:** `market_dashboard_v2.html` (alongside indicators)
- Specific price level alerts per ticker (e.g. OKLO above $80)
- MA crossover alerts (50MA crosses 200MA — golden/death cross)
- RSI overbought/oversold per ticker
- User-defined custom rules UI

### 3. 🗄️ Supabase Database Backend
**File will be:** `market_dashboard_v3.html` + Supabase project
- Free Postgres database (Supabase free tier)
- Nightly Yahoo Finance OHLC fetch via Supabase Edge Function (server-side — bypasses CORS)
- Stores full OHLC history for ALL tickers including HK/DE/FR/Crypto
- Dashboard reads from DB instead of direct API calls
- Unlocks full MACD + RSI + Bollinger for intl tickers
- localStorage replaced by Supabase for cross-device persistence

### 4. 🌐 GitHub Pages Live URL
- Walk through enabling GitHub Pages on the repo
- Permanent URL: `username.github.io/market-dashboard/market_dashboard_v1.html`
- Shareable, bookmarkable, works on any device
- Auto-updates when new versions are pushed

### 5. 💼 Portfolio Tracker
**File will be:** `market_dashboard_v4.html`
- Add position sizes and entry prices per ticker
- Real-time P&L calculated from Finnhub live quotes
- Allocation % pie chart
- Portfolio-level vol and MACD signal summary
- Gain/loss sorted view
- Total portfolio value and daily move

---

## Version History

| Version | File | Date | Key changes |
|---|---|---|---|
| v1.0 | `market_dashboard_v1.html` | May 2026 | Initial combined build: Screener + Vol + MACD |
| v2.0 | `market_dashboard_v2.html` | May 2026 | RSI(14) added · New horizontal multi-indicator grid layout · Expandable rightward · Bollinger placeholder |
| v3.0 | `market_dashboard_v3.html` | May 2026 | technicalindicators.js CDN library · Bollinger Bands(20,2) · ATR(14) · ADX(14) · 9-column indicator grid · Flash alerts across all 7 indicators |

---

## Notes

- **Vol means** recalculate monthly (or on demand via Recalc button)
- **MACD cache** resets daily — Polygon fetched once per day per US ticker
- **localStorage key prefix:** `mktdash_v1_` — change prefix on breaking changes
- **Non-US tickers** need Supabase backend (item 3) for full technical indicators
- **Flash log** persists indefinitely — clear manually via UI
- All files named `market_dashboard_vN.html` for clean version history in GitHub
