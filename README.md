# Market Bottom Signal Dashboard

Automates 3 of Carlson's 5 indicators for free. The other 2 don't have a free
API and are listed as a manual-check table inside the dashboard itself.

## What's automated vs. not

| # | Metric | Status | Data source |
|---|---|---|---|
| 1 | Breadth (% S&P 500 > 200-DMA) | ✅ Fully automated, reliable | yfinance + Wikipedia constituent list |
| 2 | Tech forward P/E | ✅ Automated, but a 15-name basket proxy, not the real weighted sector index | yfinance `.info` |
| 3 | Sentiment (Fear & Greed) | ✅ Automated, but a substitute for the real DSI Carlson used | CNN's unofficial JSON endpoint |
| 4 | SPY put volume | ⚠️ Automated but a weak proxy — only sums nearby listed expirations, not the true CBOE/OCC market-wide daily total | yfinance option chain |
| 5 | Hedge fund PB flows | ❌ Not automatable free | Goldman only shares this with Prime Brokerage clients — check financial news coverage manually |
| — | EPS revision % | ⚠️ Needs weeks of accumulated history before it means anything (it's a *change over time*, not a snapshot) | Derived from #2 once `data/history.csv` has enough rows |
| — | Geopolitical shock context | ❌ Not a repeating metric | Judgment call per event, not automatable |

**A note on testing:** I built this from documented library/API behavior, but
my sandbox can't reach financial-data or Wikipedia domains, so I haven't been
able to run it live. Test it once locally before relying on it — see below.

## Setup (all free)

1. **Create a GitHub repo** and push this folder to it.
2. **Turn on GitHub Actions** — it's on by default; the workflow in
   `.github/workflows/daily_fetch.yml` runs automatically on weekdays after
   the US market close, and appends one row to `data/history.csv` each time.
   You can also trigger it manually from the repo's *Actions* tab
   (`workflow_dispatch`) to get your first data point immediately instead of
   waiting for the next scheduled run.
3. **Deploy the dashboard** at [share.streamlit.io](https://share.streamlit.io)
   (Streamlit Community Cloud, free tier) — point it at `app.py` in your repo.
   It reads `data/history.csv` for the trend charts and does a live pull for
   the "latest snapshot" numbers at the top.
4. **Test locally first (recommended):**
   ```bash
   pip install -r requirements.txt
   python run_daily.py        # should create data/history.csv
   streamlit run app.py       # opens the dashboard in your browser
   ```

## Weekly manual check (5–10 minutes)

The dashboard shows this as a table too, but for reference, the two things
worth eyeballing that can't be pulled automatically:

- **Hedge fund flows**: search "Goldman Sachs Prime Brokerage weekly flows"
  in Bloomberg/Reuters coverage — GS publishes commentary on this even though
  the raw data is client-only.
- **True DSI**: [trade-futures.com](https://www.trade-futures.com) (paid) if
  you want the exact series Carlson cited, rather than the free Fear & Greed
  substitute already in the dashboard.

## Honest limitations to keep in mind

- The put volume number is **not** comparable to the "8 million contracts"
  threshold from the video — it's a much narrower proxy. Watch its trend, not
  its absolute level, or replace it with the free daily CBOE put/call ratio
  ([cboe.com market statistics](https://www.cboe.com/us/options/market_statistics/daily/)).
- The tech P/E basket is 15 large-caps, unweighted — it'll move similarly to
  the real sector P/E but won't match it exactly.
- None of this validates Carlson's *thresholds* (8M puts, <20% breadth, etc.)
  as genuinely predictive — it just automates tracking the same shape of data
  he used. The thresholds are still someone's judgment call, not a law of
  markets.
