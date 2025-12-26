import streamlit as st
import pandas as pd
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. SETUP & AUTO-REFRESH ---
st.set_page_config(page_title="NSE Pair Trader", layout="wide")
st_autorefresh(interval=15 * 1000, key="market_refresh")

# --- 2. RELIABLE DATA ENGINE ---
def get_market_data(s1, s2):
    try:
        # Fetching 2 days of 1-minute data for the most "on-spot" prices possible
        tickers = f"{s1}.NS {s2}.NS"
        data = yf.download(tickers, period="2d", interval="1m", progress=False)['Close']
        
        # Get the very last price in the list
        p1 = round(data[f"{s1}.NS"].iloc[-1], 2)
        p2 = round(data[f"{s2}.NS"].iloc[-1], 2)
        
        # Calculate Z-Score using last 100 minutes
        ratio = data[f"{s1}.NS"] / data[f"{s2}.NS"]
        mean = ratio.tail(100).mean()
        std = ratio.tail(100).std()
        z_score = round((ratio.iloc[-1] - mean) / std, 2)
        
        return p1, p2, z_score
    except:
        return None, None, None

# --- 3. TRADE STORAGE ---
if 'ledger' not in st.session_state:
    st.session_state.ledger = []

# --- 4. UI TOP BAR (From your sketch) ---
st.title("⚡ NSE Pair Trader")
st.write("🟢 **Live Market Terminal** | Refreshing Every 15s")

# --- 5. SECTOR TABS ---
tabs = st.tabs(["🏦 Banking", "💻 IT", "⛽ Energy"])
sectors = {
    0: [("HDFCBANK", "ICICIBANK"), ("SBIN", "BANKBARODA")],
    1: [("TCS", "INFY"), ("WIPRO", "HCLTECH")],
    2: [("RELIANCE", "ONGC"), ("BPCL", "IOC")]
}

for i, pairs in sectors.items():
    with tabs[i]:
        for s1, s2 in pairs:
            p1, p2, z = get_market_data(s1, s2)
            
            if p1:
                col_left, col_right = st.columns([1, 1])
                
                with col_left:
                    st.subheader(f"{s1} vs {s2}")
                    st.metric("Z-Score Value", z)
                    st.write(f"**{s1} Live:** ₹{p1}")
                    st.write(f"**{s2} Live:** ₹{p2}")
                    
                    # TRADE OPTIONS (From your sketch)
                    c1, c2 = st.columns(2)
                    if c1.button(f"BUY {s1}", key=f"b_{s1}"):
                        st.session_state.ledger.append({"pair": f"{s1}/{s2}", "z": z, "p1": p1, "side": "BUY"})
                    if c2.button(f"SELL {s1}", key=f"s_{s1}"):
                        st.session_state.ledger.append({"pair": f"{s1}/{s2}", "z": z, "p1": p1, "side": "SELL"})
                
                with col_right:
                    # Simple Trend View
                    st.line_chart([z-1, 0, z+1, z])
            else:
                st.error(f"Connecting to NSE for {s1}/{s2}...")
            st.divider()

# --- 6. POSITION PANEL ---
st.subheader("📊 Active Positions | PnL")
if st.session_state.ledger:
    for trade in st.session_state.ledger:
        st.success(f"**{trade['side']} {trade['pair']}** | Entry Z: {trade['z']} | Entry Price: ₹{trade['p1']}")
else:
    st.info("No active trades. Use the buttons above to enter a paper trade.")
