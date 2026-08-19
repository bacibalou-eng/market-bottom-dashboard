"""
Data fetchers for the market-bottom signal dashboard.

Each function returns a plain dict of {metric_name: value} plus a 'notes'
field describing data quality / caveats. Dependency-light: yfinance +
requests + pandas. See README.md for what's fully automated vs. approximated
vs. impossible to automate for free.
"""

import datetime as dt
import time

import pandas as pd
import requests
import yfinance as yf

# ---------------------------------------------------------------------------
# 1. BREADTH: % of S&P 500 stocks trading above their 200-day moving average
#    Fully automatable, free. This is the most reliable metric in this file.
# ---------------------------------------------------------------------------


def get_sp500_tickers() -> list:
    """Scrape the current S&P 500 constituent list from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    df = tables[0]
    tickers = df["Symbol"].str.replace(".", "-", regex=False).tolist()
    return tickers


def compute_breadth() -> dict:
    tickers = get_sp500_tickers()
    data = yf.download(
        tickers,
        period="300d",
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        threads=True,
        progress=False,
    )

    above, counted = 0, 0
    for t in tickers:
        try:
            closes = data[t]["Close"].dropna()
            if len(closes) < 200:
                continue
            ma200 = closes.rolling(200).mean().iloc[-1]
            last = closes.iloc[-1]
            counted += 1
            if last > ma200:
                above += 1
        except Exception:
            continue

    pct = round(100 * above / counted, 1) if counted else None
    return {
        "breadth_pct_above_200dma": pct,
        "breadth_tickers_counted": counted,
        "breadth_notes": "Fully automated, free (yfinance + Wikipedia constituent list).",
    }


# ---------------------------------------------------------------------------
# 2. PUT VOLUME PROXY: SPY put option volume summed across nearby expirations
#    APPROXIMATION -- see notes. Real CBOE/OCC aggregate figures are paid.
# ---------------------------------------------------------------------------


def compute_put_volume_proxy() -> dict:
    spy = yf.Ticker("SPY")
    total_put_volume = 0
    expirations_used = 0
    try:
        for exp in spy.options[:6]:
            chain = spy.option_chain(exp)
            total_put_volume += chain.puts["volume"].fillna(0).sum()
            expirations_used += 1
            time.sleep(0.2)
    except Exception as e:
        return {"put_volume_proxy": None, "put_volume_notes": f"Fetch failed: {e}"}

    return {
        "put_volume_proxy": int(total_put_volume),
        "expirations_used": expirations_used,
        "put_volume_notes": (
            "APPROXIMATION ONLY. Carlson's '8M contracts' figure is a CBOE/OCC "
            "market-wide daily aggregate (paid feeds: CBOE DataShop, Tradier, "
            "ORATS, Polygon.io). This proxy sums only the nearest listed "
            "expirations via yfinance's live chain snapshot and will read "
            "structurally lower -- track its own trend/z-score over time, not "
            "the raw 8M threshold. Free daily CBOE put/call ratio (a cleaner "
            "substitute) is linked in README."
        ),
    }


# ---------------------------------------------------------------------------
# 3. SENTIMENT: CNN Fear & Greed Index (unofficial endpoint) as a DSI proxy
# ---------------------------------------------------------------------------


def compute_fear_greed() -> dict:
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        score = data["fear_and_greed"]["score"]
        rating = data["fear_and_greed"]["rating"]
    except Exception as e:
        return {"fear_greed_score": None, "fear_greed_notes": f"Fetch failed: {e}"}

    return {
        "fear_greed_score": round(score, 1),
        "fear_greed_rating": rating,
        "fear_greed_notes": (
            "Unofficial CNN endpoint (may break without notice) used as a free "
            "substitute for Jake Bernstein's DSI, which Carlson actually cited. "
            "Directionally similar (extreme fear = low score) but not the same "
            "underlying series."
        ),
    }


# ---------------------------------------------------------------------------
# 4. TECH VALUATION: forward P/E across a basket of large tech constituents
# ---------------------------------------------------------------------------

TECH_BASKET = [
    "AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "CRM", "ADBE", "AMD",
    "CSCO", "ACN", "IBM", "TXN", "QCOM", "INTU", "NOW",
]


def compute_tech_valuation() -> dict:
    fwd_pes, fwd_eps_sum, count = [], 0.0, 0
    for t in TECH_BASKET:
        try:
            info = yf.Ticker(t).info
            pe = info.get("forwardPE")
            eps = info.get("forwardEps")
            if pe and pe > 0:
                fwd_pes.append(pe)
            if eps:
                fwd_eps_sum += eps
                count += 1
        except Exception:
            continue

    avg_fwd_pe = round(sum(fwd_pes) / len(fwd_pes), 1) if fwd_pes else None
    return {
        "tech_basket_avg_forward_pe": avg_fwd_pe,
        "tech_basket_forward_eps_sum": round(fwd_eps_sum, 2) if count else None,
        "tech_basket_size": len(TECH_BASKET),
        "tech_valuation_notes": (
            "Simple (unweighted) average forward P/E across a fixed 15-name "
            "large-cap tech basket -- not free-float weighted like a real "
            "sector index. EPS *revision %* requires comparing this snapshot "
            "to a prior one, so it only becomes meaningful after this pipeline "
            "has logged a few weeks of history. For the real S&P Tech sector "
            "aggregate P/E, check the free weekly Yardeni Research chart book "
            "linked in README."
        ),
    }


def fetch_all() -> dict:
    result = {"date": dt.date.today().isoformat()}
    result.update(compute_breadth())
    result.update(compute_put_volume_proxy())
    result.update(compute_fear_greed())
    result.update(compute_tech_valuation())
    return result
