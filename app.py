import pandas as pd
import streamlit as st

from fetchers import fetch_all

st.set_page_config(page_title="Market Bottom Signal Dashboard", layout="wide")
st.title("Market Bottom Signal Dashboard")
st.caption(
    "Automated approximation of a multi-factor 'capitulation bottom' framework "
    "(sentiment, breadth, valuation). Free data sources only — read the caveat "
    "under each metric before trusting the number."
)

HISTORY_PATH = "data/history.csv"


@st.cache_data(ttl=6 * 60 * 60)  # refresh at most every 6 hours
def load_history():
    try:
        return pd.read_csv(HISTORY_PATH, parse_dates=["date"])
    except FileNotFoundError:
        return pd.DataFrame()


@st.cache_data(ttl=6 * 60 * 60)
def live_snapshot():
    return fetch_all()


history = load_history()
live = live_snapshot()


def signal_badge(value, threshold, direction):
    if value is None:
        return "no data"
    triggered = value < threshold if direction == "below" else value > threshold
    return "🟢 triggered" if triggered else "⚪ not yet"


st.subheader("Latest snapshot")
cols = st.columns(4)

with cols[0]:
    st.metric("Breadth: % > 200-DMA", f"{live.get('breadth_pct_above_200dma')}%")
    st.caption(signal_badge(live.get("breadth_pct_above_200dma"), 20, "below") + " (< 20%)")

with cols[1]:
    st.metric("Put volume (proxy)", live.get("put_volume_proxy"))
    st.caption("Not comparable to CBOE's 8M-contract figure — see notes below.")

with cols[2]:
    st.metric("Fear & Greed score", live.get("fear_greed_score"), live.get("fear_greed_rating"))
    st.caption(signal_badge(live.get("fear_greed_score"), 25, "below") + " (< 25 = extreme fear)")

with cols[3]:
    st.metric("Tech basket fwd P/E", live.get("tech_basket_avg_forward_pe"))
    st.caption("15-name large-cap tech basket, unweighted average.")

st.divider()

st.subheader("History")
if not history.empty:
    st.line_chart(history.set_index("date")[["breadth_pct_above_200dma"]])
    st.line_chart(history.set_index("date")[["fear_greed_score"]])
    st.line_chart(history.set_index("date")[["tech_basket_avg_forward_pe"]])
else:
    st.info(
        "No history yet — the GitHub Actions job needs to run at least once "
        "and commit data/history.csv before charts appear here."
    )

st.divider()

st.subheader("⚠️ Check manually — no free API exists for these")
st.markdown(
    """
| Metric | Where to check | Frequency |
|---|---|---|
| **Hedge fund positioning / Prime Brokerage flows** | Search "Goldman Sachs Prime Services weekly flows" on [Bloomberg](https://www.bloomberg.com) or [Reuters](https://www.reuters.com); GS shares this directly only with PB clients | Weekly |
| **True DSI (Jake Bernstein)** | [trade-futures.com](https://www.trade-futures.com) — paid, roughly $50–100/mo | Daily |
| **Official CBOE put/call ratio** | [CBOE daily market statistics](https://www.cboe.com/us/options/market_statistics/daily/) — free CSV | Daily |
| **AAII sentiment survey** | [aaii.com/sentimentsurvey](https://www.aaii.com/sentimentsurvey) — free, released Thursdays | Weekly |
| **Real S&P Tech sector forward P/E** | [Yardeni Research free chart books](https://yardeni.com/charts) | Weekly |
| **Geopolitical shock context** | No repeating data pull — this is a judgment call made per event, not a metric | As needed |
"""
)

with st.expander("Full raw data notes for this snapshot"):
    for k, v in live.items():
        if k.endswith("_notes"):
            st.markdown(f"**{k}**: {v}")
