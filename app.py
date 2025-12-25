import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from streamlit_autorefresh import st_autorefresh
import time

# --- 1. CONFIG & THEME ---
st.set_page_config(page_title="NSE Live Spot Terminal", layout="wide")
st_autorefresh(interval=15 * 1000, key="global_refresh") # Refreshes every 15 seconds

# --- 2. LIVE DATA SCRAPER (ON-SPOT) ---
def get_live_price(symbol):
    try:
        # Pulls directly from Google Finance (Real-time NSE)
        ticker = symbol.replace(".NS", "")
        url = f"https://www.google.com/finance/quote/{ticker}:NSE"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Scrapes the main price div
        price_div = soup.find("div", {"class": "YMlS7e"})
        if price_div:
            return float(price_div.text.replace("₹", "").replace(",", ""))
        return None
    except:
        return None

# --- 3. SECTOR DEFINITIONS ---
SECTORS = {
    "🏦 BANKS": [("HDFCBANK", "ICICIBANK"), ("SBIN", "BANKBARODA")],
    "⛽ ENERGY": [("RELIANCE", "ONGC"), ("BPCL", "IOC")],
    "💻 IT": [("TCS", "INFY"), ("WIPRO", "HCLTECH")]
}

# --- 4. DASHBOARD ---
st.title("⚡ NSE On-Spot Radar")
st.caption("Status: Pulling Real-Time Prices from Google Finance")

if 'balance' not in st.session_state:
    st.session_state.balance = 1000000.0

col1, col2 = st.columns(2)
col1.metric("Virtual Cash", f"₹{st.session_state.balance:,}")

tabs = st.tabs(list(SECTORS.keys()))

for i, sector in enumerate(SECTORS.keys()):
    with tabs[i]:
        for s1, s2 in SECTORS[sector]:
            p1 = get_live_price(s1)
            p2 = get_live_price(s2)
            
            if p1 and p2:
                # Calculate simple ratio since we can't do Z-score on a single spot price
                ratio = round(p1 / p2, 4)
                
                st.markdown(f"""
                <div style="background:#161B22; padding:15px; border-radius:10px; margin-bottom:10px; border:1px solid #30363D">
                    <div style="display:flex; justify-content:space-between">
                        <span><b>{s1} vs {s2}</b></span>
                        <span style="color:#39FF14">Ratio: {ratio}</span>
                    </div>
                    <div style="font-size:0.8rem; color:gray">
                        {s1}: ₹{p1} | {s2}: ₹{p2}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning(f"Waiting for {s1}/{s2} Spot Data...")
