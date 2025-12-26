import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from streamlit_autorefresh import st_autorefresh

# --- 1. SETTINGS & REFRESH ---
st.set_page_config(page_title="NSE Pair Trader ⚡", layout="wide")
st_autorefresh(interval=15 * 1000, key="global_refresh")

# --- 2. LIVE DATA ENGINE ---
def get_spot(ticker):
    try:
        url = f"https://www.google.com/finance/quote/{ticker}:NSE"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(resp.text, 'html.parser')
        price = soup.find("div", {"class": "YMlS7e"}).text
        return float(price.replace("₹", "").replace(",", ""))
    except: return None

@st.cache_data(ttl=3600)
def get_stats(s1, s2):
    # Historical data to calculate Mean and Std Dev for Z-Score
    df = yf.download([f"{s1}.NS", f"{s2}.NS"], period="5d", interval="5m", progress=False)['Close']
    ratio = df[f"{s1}.NS"] / df[f"{s2}.NS"]
    return ratio.mean(), ratio.std()

# --- 3. SESSION STATE FOR TRADES ---
if 'ledger' not in st.session_state:
    st.session_state.ledger = []

# --- 4. UI TOP BAR ---
st.title("⚡ NSE Pair Trader")
st.write("Market Status: 🟢 Live | Refresh: 15s")

# SECTORS from your sketch
sectors = {
    "🏦 Banking": [("HDFCBANK", "ICICIBANK"), ("SBIN", "BANKBARODA")],
    "💻 IT": [("TCS", "INFY"), ("WIPRO", "HCLTECH")],
    "⛽ Energy": [("RELIANCE", "ONGC"), ("BPCL", "IOC")]
}

# --- 5. SECTOR TABS ---
tabs = st.tabs(list(sectors.keys()))

for i, (name, pairs) in enumerate(sectors.items()):
    with tabs[i]:
        for s1, s2 in pairs:
            # Logic & Calculations
            mean, std = get_stats(s1, s2)
            p1 = get_spot(s1)
            p2 = get_spot(s2)
            
            if p1 and p2:
                curr_ratio = p1 / p2
                z_score = round((curr_ratio - mean) / std, 2)
                
                # Layout based on your drawing
                col_info, col_chart = st.columns([1, 1])
                
                with col_info:
                    st.markdown(f"### {s1} vs {s2}")
                    st.write(f"**Z-Value:** `{z_score}`")
                    st.write(f"**{s1} Live:** ₹{p1}")
                    st.write(f"**{s2} Live:** ₹{p2}")
                    
                    b1, b2 = st.columns(2)
                    if b1.button(f"Buy {s1}", key=f"b_{s1}"):
                        st.session_state.ledger.append({"pair": f"{s1}/{s2}", "entry_z": z_score, "price": p1})
                    if b2.button(f"Sell {s1}", key=f"s_{s1}"):
                        st.session_state.ledger.append({"pair": f"{s1}/{s2}", "entry_z": z_score, "price": p1})
                
                with col_chart:
                    # Placeholder for the chart in your sketch
                    st.line_chart(pd.Series([mean-std*2, mean, mean+std*2, curr_ratio], index=['Low','Mean','High','Now']))
            st.divider()

# --- 6. PNL PANEL (Bottom of your sketch) ---
st.subheader("📊 Active Positions | PnL")
if st.session_state.ledger:
    for trade in st.session_state.ledger:
        st.info(f"Trade: {trade['pair']} | Entry Z: {trade['entry_z']} | Live tracking...")
else:
    st.write("No active trades. Tap 'Buy' to start paper trading.")
