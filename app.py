import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from streamlit_autorefresh import st_autorefresh

# --- 1. SETTINGS & REFRESH ---
st.set_page_config(page_title="NSE LIVE SPOT", layout="wide")
st_autorefresh(interval=10 * 1000, key="price_update") # Updates every 10s

# --- 2. THE SPOT SCRAPER ---
def get_spot_price(ticker):
    try:
        url = f"https://www.google.com/finance/quote/{ticker}:NSE"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        price_div = soup.find("div", {"class": "YMlS7e"})
        if price_div:
            return float(price_div.text.replace("₹", "").replace(",", ""))
        return None
    except: return None

# --- 3. SESSION STATE (SAVES YOUR TRADES) ---
if 'trades' not in st.session_state:
    st.session_state.trades = []

# --- 4. DASHBOARD HEADER ---
st.title("⚡ NSE Spot Pair Trader")
st.write(f"🟢 **Live Market Terminal** | Refreshing every 10 seconds")

# --- 5. LIVE MONITOR & BUY BUTTONS ---
PAIRS = [("HDFCBANK", "ICICIBANK"), ("TCS", "INFY"), ("SBIN", "BANKBARODA")]

st.subheader("📊 Live Pair Watchlist")
for s1, s2 in PAIRS:
    p1 = get_spot_price(s1)
    p2 = get_spot_price(s2)
    
    if p1 and p2:
        ratio = round(p1 / p2, 4)
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        
        with col1: st.metric(s1, f"₹{p1}")
        with col2: st.metric(s2, f"₹{p2}")
        with col3: st.metric("Ratio", ratio)
        with col4:
            if st.button(f"Buy", key=f"buy_{s1}"):
                st.session_state.trades.append({"pair": f"{s1}/{s2}", "entry": ratio})
                st.toast(f"Trade Opened for {s1}/{s2}")
        st.divider()

# --- 6. PNL CALCULATOR ---
if st.session_state.trades:
    st.subheader("💼 Active Paper Trades")
    for trade in st.session_state.trades:
        t1, t2 = trade['pair'].split("/")
        curr_p1 = get_spot_price(t1)
        curr_p2 = get_spot_price(t2)
        
        if curr_p1 and curr_p2:
            curr_ratio = round(curr_p1 / curr_p2, 4)
            # PnL logic: if ratio moves by 0.01, you make/lose ₹100
            diff = curr_ratio - trade['entry']
            pnl = round(diff * 10000, 2)
            
            color = "#39FF14" if pnl >= 0 else "#FF3131"
            st.markdown(f"**{trade['pair']}** | Entry: {trade['entry']} → Now: {curr_ratio} | **PnL: <span style='color:{color}'>₹{pnl}</span>**", unsafe_allow_html=True)
