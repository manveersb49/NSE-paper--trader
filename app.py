import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from streamlit_autorefresh import st_autorefresh

# --- 1. SETTINGS ---
st.set_page_config(page_title="NSE Live Pair Trader", layout="wide")
st_autorefresh(interval=15 * 1000, key="refresh")

# --- 2. THE IMPROVED SCRAPER (FIXED) ---
def get_spot(ticker):
    try:
        url = f"https://www.google.com/finance/quote/{ticker}:NSE"
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15'}
        resp = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Checking multiple possible price classes used by Google
        for class_name in ["YMlS7e", "fx67Eb", "IsqPge"]:
            element = soup.find("div", {"class": class_name})
            if element:
                price_text = element.text.replace("₹", "").replace(",", "").strip()
                return float(price_text)
        return None
    except: return None

@st.cache_data(ttl=3600)
def get_stats(s1, s2):
    df = yf.download([f"{s1}.NS", f"{s2}.NS"], period="5d", interval="5m", progress=False)['Close']
    ratio = df[f"{s1}.NS"] / df[f"{s2}.NS"]
    return ratio.mean(), ratio.std()

# --- 3. SESSION STATE ---
if 'ledger' not in st.session_state:
    st.session_state.ledger = []

# --- 4. APP LAYOUT ---
st.title("⚡ NSE Pair Trader")
st.write("Status: 🟢 Live Market Feed")

sectors = {
    "🏦 Banking": [("HDFCBANK", "ICICIBANK"), ("SBIN", "BANKBARODA")],
    "💻 IT": [("TCS", "INFY"), ("WIPRO", "HCLTECH")],
    "⛽ Energy": [("RELIANCE", "ONGC"), ("BPCL", "IOC")]
}

tabs = st.tabs(list(sectors.keys()))

for i, (name, pairs) in enumerate(sectors.items()):
    with tabs[i]:
        for s1, s2 in pairs:
            p1 = get_spot(s1)
            p2 = get_spot(s2)
            mean, std = get_stats(s1, s2)
            
            if p1 and p2:
                curr_ratio = p1 / p2
                z_score = round((curr_ratio - mean) / std, 2)
                
                # Side-by-side layout from your sketch
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.markdown(f"### {s1} vs {s2}")
                    st.metric("Z-Value", z_score)
                    st.write(f"**{s1}:** ₹{p1} | **{s2}:** ₹{p2}")
                    
                    if st.button(f"Trade {s1}/{s2}", key=f"tr_{s1}"):
                        st.session_state.ledger.append({"pair": f"{s1}/{s2}", "z": z_score, "p1": p1})
                
                with col2:
                    st.line_chart([mean-std*2, mean, mean+std*2, curr_ratio])
            else:
                st.warning(f"Searching for {s1} and {s2} live prices...")
            st.divider()

# --- 5. PNL SECTION ---
st.subheader("📊 Active Positions | PnL")
if st.session_state.ledger:
    for trade in st.session_state.ledger:
        st.write(f"✅ **{trade['pair']}** | Entry Z: {trade['z']} | Entry Price: ₹{trade['p1']}")
else:
    st.caption("No active trades. Tap 'Trade' to begin.")
