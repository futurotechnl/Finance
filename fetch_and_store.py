"""
MarketDash v3 — Data Fetcher
Fetches OHLCV + computes indicators → pushes to Supabase
Run once per day after market close (e.g. 23:00 Lisbon time)
"""

import json, time, math, datetime, urllib.request, urllib.parse, urllib.error

# ── CONFIG ────────────────────────────────────────────────────────────────────
SUPABASE_URL = "https://ivdyyryyxhtlzoltykfq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml2ZHl5cnl5eGh0bHpvbHR5a2ZxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkzNjg1MjUsImV4cCI6MjA5NDk0NDUyNX0.62mYOuYgSLxIhMXN2sDyA_yMR5P_pp3VXz3LWeKbzV8"

# US tickers only (non-US don't have Yahoo Finance data in this format)
US_TICKERS = [
    'QCOM','BRK-B','AI','OKLO','REK','TLT','SRTY','QQQ','GLD','SMR',
    'BMNR','GOOGL','GDXU','XHB','MSFT','AAPL','NVDA','TSLA','BABA'
]

# ── HTTP HELPERS ──────────────────────────────────────────────────────────────
def http_get(url, headers=None, timeout=15):
    req = urllib.request.Request(url, headers=headers or {})
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8'), r.status
    except Exception as e:
        return None, str(e)

def supabase_upsert(table, rows):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    data = json.dumps(rows).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('apikey', SUPABASE_KEY)
    req.add_header('Authorization', f'Bearer {SUPABASE_KEY}')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Prefer', 'resolution=merge-duplicates')
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  Supabase error {e.code}: {body[:200]}")
        return e.code

# ── YAHOO FINANCE ─────────────────────────────────────────────────────────────
def get_yahoo_crumb():
    """Get Yahoo Finance crumb token for authenticated requests"""
    print("Getting Yahoo Finance crumb...")
    # Step 1: get cookie
    http_get("https://fc.yahoo.com")
    time.sleep(1)
    # Step 2: get crumb
    text, status = http_get("https://query1.finance.yahoo.com/v1/test/getcrumb")
    if text and len(text) > 2 and '<' not in text:
        print(f"  Crumb: {text.strip()}")
        return text.strip()
    # Fallback crumb fetch
    text, status = http_get("https://query2.finance.yahoo.com/v1/test/getcrumb")
    if text and len(text) > 2 and '<' not in text:
        return text.strip()
    print("  Warning: could not get crumb, proceeding without")
    return ""

def fetch_yahoo_ohlcv(ticker, crumb=""):
    """Fetch 1 year of daily OHLCV from Yahoo Finance"""
    now = int(time.time())
    period1 = now - 400 * 86400
    period2 = now - 86400  # yesterday
    sym = ticker.replace('BRK-B', 'BRK-B')  # Yahoo uses BRK-B
    crumb_param = f"&crumb={urllib.parse.quote(crumb)}" if crumb else ""
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}"
           f"?interval=1d&period1={period1}&period2={period2}{crumb_param}")
    text, status = http_get(url)
    if not text:
        # Try query2
        url2 = url.replace('query1', 'query2')
        text, status = http_get(url2)
    if not text:
        return None
    try:
        d = json.loads(text)
        result = d.get('chart', {}).get('result', [None])[0]
        if not result:
            return None
        timestamps = result.get('timestamp', [])
        quote = result.get('indicators', {}).get('quote', [{}])[0]
        adjclose_list = result.get('indicators', {}).get('adjclose', [{}])
        adjclose = adjclose_list[0].get('adjclose', []) if adjclose_list else []
        bars = []
        for i, ts in enumerate(timestamps):
            c = (adjclose[i] if i < len(adjclose) and adjclose[i] else
                 quote.get('close', [])[i] if i < len(quote.get('close', [])) else None)
            if c is None or c <= 0:
                continue
            bars.append({
                'date': datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d'),
                'open':   round(quote.get('open',  [])[i] or c, 4) if i < len(quote.get('open',[])) else c,
                'high':   round(quote.get('high',  [])[i] or c, 4) if i < len(quote.get('high',[])) else c,
                'low':    round(quote.get('low',   [])[i] or c, 4) if i < len(quote.get('low', [])) else c,
                'close':  round(c, 4),
                'volume': int(quote.get('volume', [])[i] or 0)     if i < len(quote.get('volume',[])) else 0,
            })
        return bars if len(bars) >= 30 else None
    except Exception as e:
        print(f"  Parse error for {ticker}: {e}")
        return None

# ── TECHNICAL INDICATORS ──────────────────────────────────────────────────────
def ema(values, period):
    k = 2 / (period + 1)
    result = []
    for v in values:
        if not result:
            result.append(v)
        else:
            result.append(v * k + result[-1] * (1 - k))
    return result

def compute_indicators(bars):
    closes = [b['close'] for b in bars]
    highs  = [b['high']  for b in bars]
    lows   = [b['low']   for b in bars]
    n = len(closes)

    # MACD (12, 26, 9)
    ema12 = ema(closes, 12)
    ema26 = ema(closes, 26)
    macd_line = [ema12[i] - ema26[i] for i in range(n)]
    signal_line = ema(macd_line, 9)
    histogram = [macd_line[i] - signal_line[i] for i in range(n)]
    macd_val  = macd_line[-1]
    macd_sig  = signal_line[-1]
    macd_hist = histogram[-1]
    crossover = 'none'
    if macd_line[-2] < signal_line[-2] and macd_line[-1] > signal_line[-1]:
        crossover = 'bullish'
    elif macd_line[-2] > signal_line[-2] and macd_line[-1] < signal_line[-1]:
        crossover = 'bearish'

    # Histogram std dev (last 50)
    hists = histogram[-50:]
    mn = sum(hists) / len(hists)
    hist_std = math.sqrt(sum((h - mn)**2 for h in hists) / len(hists))

    # SMA 20, 50, 200
    def sma(vals, p):
        return sum(vals[-p:]) / p if len(vals) >= p else None
    ma20  = sma(closes, 20)
    ma50  = sma(closes, 50)
    ma200 = sma(closes, 200)

    # RSI 14 (Wilder smoothing)
    gains, losses = [], []
    for i in range(1, n):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    if len(gains) >= 14:
        avg_gain = sum(gains[:14]) / 14
        avg_loss = sum(losses[:14]) / 14
        for i in range(14, len(gains)):
            avg_gain = (avg_gain * 13 + gains[i]) / 14
            avg_loss = (avg_loss * 13 + losses[i]) / 14
        rsi14 = 100 - (100 / (1 + avg_gain / avg_loss)) if avg_loss > 0 else 100
    else:
        rsi14 = None

    # Bollinger Bands (20, 2)
    bb_upper = bb_middle = bb_lower = bb_pct_b = bb_width = bb_width_mean = None
    if n >= 20:
        last20 = closes[-20:]
        bb_middle = sum(last20) / 20
        std = math.sqrt(sum((c - bb_middle)**2 for c in last20) / 20)
        bb_upper = bb_middle + 2 * std
        bb_lower = bb_middle - 2 * std
        bb_width = bb_upper - bb_lower
        bb_pct_b = (closes[-1] - bb_lower) / bb_width if bb_width > 0 else 0.5
        # Mean width over last 20 bars
        widths = []
        for j in range(max(0, n-40), n-19):
            chunk = closes[j:j+20]
            m = sum(chunk)/20
            s = math.sqrt(sum((c-m)**2 for c in chunk)/20)
            widths.append(s*4)
        bb_width_mean = sum(widths)/len(widths) if widths else bb_width

    # ATR 14
    atr14 = atr_mean = None
    atr_trend = 'flat'
    if n >= 15:
        trs = []
        for i in range(1, n):
            tr = max(highs[i]-lows[i],
                     abs(highs[i]-closes[i-1]),
                     abs(lows[i]-closes[i-1]))
            trs.append(tr)
        # Wilder smoothing
        atr_vals = [sum(trs[:14])/14]
        for tr in trs[14:]:
            atr_vals.append((atr_vals[-1]*13 + tr)/14)
        atr14 = atr_vals[-1]
        recent = atr_vals[-20:]
        atr_mean = sum(recent)/len(recent)
        if len(atr_vals) >= 6:
            early = sum(atr_vals[-6:-3])/3
            late  = sum(atr_vals[-3:])/3
            atr_trend = 'rising' if late > early*1.05 else ('falling' if late < early*0.95 else 'flat')

    # ADX 14
    adx14 = di_plus = di_minus = None
    if n >= 28:
        plus_dm, minus_dm, trs2 = [], [], []
        for i in range(1, n):
            up   = highs[i]  - highs[i-1]
            down = lows[i-1] - lows[i]
            plus_dm.append(up   if up > down and up > 0   else 0)
            minus_dm.append(down if down > up and down > 0 else 0)
            tr = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
            trs2.append(tr)
        def wilder(vals, p):
            res = [sum(vals[:p])]
            for v in vals[p:]: res.append(res[-1] - res[-1]/p + v)
            return res
        sm_tr  = wilder(trs2, 14)
        sm_pdm = wilder(plus_dm, 14)
        sm_ndm = wilder(minus_dm, 14)
        di_p = [100*sm_pdm[i]/sm_tr[i] if sm_tr[i] else 0 for i in range(len(sm_tr))]
        di_n = [100*sm_ndm[i]/sm_tr[i] if sm_tr[i] else 0 for i in range(len(sm_tr))]
        dx   = [100*abs(di_p[i]-di_n[i])/(di_p[i]+di_n[i]) if (di_p[i]+di_n[i]) else 0 for i in range(len(di_p))]
        adx_vals = wilder(dx, 14)
        adx14    = adx_vals[-1]
        di_plus  = di_p[-1]
        di_minus = di_n[-1]

    def r(v, d=4):
        return round(v, d) if v is not None else None

    return {
        'macd_val':      r(macd_val),
        'macd_sig':      r(macd_sig),
        'macd_hist':     r(macd_hist),
        'macd_crossover': crossover,
        'hist_stddev':   r(hist_std),
        'ma20':          r(ma20),
        'ma50':          r(ma50),
        'ma200':         r(ma200),
        'rsi14':         r(rsi14, 2),
        'bb_upper':      r(bb_upper),
        'bb_middle':     r(bb_middle),
        'bb_lower':      r(bb_lower),
        'bb_pct_b':      r(bb_pct_b, 4),
        'bb_width':      r(bb_width),
        'bb_width_mean': r(bb_width_mean),
        'atr14':         r(atr14),
        'atr_mean':      r(atr_mean),
        'atr_trend':     atr_trend,
        'adx14':         r(adx14, 2),
        'di_plus':       r(di_plus, 2),
        'di_minus':      r(di_minus, 2),
    }

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("MarketDash v3 — Data Fetcher")
    print(f"Run at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    crumb = get_yahoo_crumb()
    time.sleep(2)

    ok_count = 0
    fail_count = 0

    for ticker in US_TICKERS:
        print(f"\n[{ticker}] Fetching...")

        bars = fetch_yahoo_ohlcv(ticker, crumb)

        if not bars:
            print(f"  ✗ No data for {ticker}")
            fail_count += 1
            time.sleep(1)
            continue

        print(f"  ✓ {len(bars)} bars fetched")

        # Store OHLCV rows
        ohlcv_rows = [{'ticker': ticker, **b} for b in bars]
        status = supabase_upsert('ohlcv', ohlcv_rows)
        print(f"  OHLCV → Supabase: HTTP {status}")

        # Compute + store indicators
        ind = compute_indicators(bars)
        ind['ticker'] = ticker
        ind['updated_at'] = datetime.datetime.utcnow().isoformat()
        status2 = supabase_upsert('indicators', [ind])
        print(f"  Indicators → Supabase: HTTP {status2}")

        ok_count += 1
        time.sleep(1.5)  # be polite to Yahoo Finance

    print("\n" + "=" * 60)
    print(f"Done: {ok_count} succeeded, {fail_count} failed")
    print("=" * 60)

if __name__ == '__main__':
    main()
