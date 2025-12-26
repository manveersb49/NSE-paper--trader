import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from streamlit_autorefresh import st_autorefresh

# --- 1. SETTINGS ---
st.set_page_config(page_title="NSE Live Terminal", layout="wide")
st_autorefresh(interval=15 * 1000, key="refresh") # Auto-refresh every 15s

# --- 2. THE "HEAVY DUTY" LIVE SCRAPER ---
def get_spot(ticker):
    try:
        url = f"https://www.google.com/finance/quote/{ticker}:NSE"
        # Using a very specific iPhone user agent to trick Google into thinking we are a real phone
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return "Conn Error"
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # We now look for ANY div that contains the price-specific class names
        # Google uses these for live prices
        potential_classes = ["YMlS7e", "fx67Eb", "IsqPge", "r79p0c"]
        for c in potential_classes:
            el = soup.find("div", {"class": c})
            if el and "₹" in el.text or "." in el.text:
                price_raw = el.text.replace("₹", "").replace(",", "").strip()
                return float(price_raw)
        
        return "Search Fail"
    except Exception as e:
        return f"Err: {str(e)[:10]}"

@st.cache_data(ttl=3600)
def get_stats(s1, s2):
    # Fetching 5 days of 5-minute data for a solid Z-Score baseline
    df = yf.download([f"{s1}.NS", f"{s2}.NS"], period="5d", interval="5m", progress=False)['Close']
    ratio = df[f"{s1}.NS"] / df[f"{s2}.NS"]
    return ratio.mean(), ratio.std()

# --- 3. TRADE SYSTEM ---
if 'ledger' not in st.session_state:
    st.session_state.ledger = []

# --- 4. APP INTERFACE ---
st.title("⚡ NSE Real-Time Pair Trader")
st.markdown("🕒 **Last Update:** " + pd.Timestamp.now().strftime("%H:%M:%S"))

tabs = st.tabs(["🏦 Banking", "💻 IT", "⛽ Energy"])
sectors = {
    0: [("HDFCBANK", "ICICIBANK"), ("SBIN", "BANKBARODA")],
    1: [("TCS", "INFY"), ("WIPRO", "HCLTECH")],
    2: [("RELIANCE", "ONGC"), ("BPCL", "IOC")]
}

for i, pairs in sectors.items():
    with tabs[i]:
        for s1, s2 in pairs:
            p1, p2 = get_spot(s1), get_spot(s2)
            mean, std = get_stats(s1, s2)
            
            # Checks if we actually got numbers back
            if isinstance(p1, float) and isinstance(p2, float):
                curr_ratio = p1 / p2
                z_score = round((curr_ratio - mean) / std, 2)
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.subheader(f"{s1} vs {s2}")
                    st.metric("Z-Score", z_score, delta=f"Ratio: {round(curr_ratio, 3)}")
                    st.write(f"💵 **{s1}:** ₹{p1} | **{s2}:** ₹{p2}")
                    
                    # TRADE BUTTONS (Paper Trading)
                    bt1, bt2 = st.columns(2)
                    if bt1.button(f"BUY {s1}", key=f"b_{s1}"):
                        st.session_state.ledger.append({"pair": f"{s1}/{s2}", "entry": z_score, "side": "BUY"})
                    if bt2.button(f"SELL {s1}", key=f"s_{s1}"):
                        st.session_state.ledger.append({"pair": f"{s1}/{s2}", "entry": z_score, "side": "SELL"})
                
                with col2:
                    st.line_chart([mean-std*2, mean, mean+std*2, curr_ratio])
            else:
                st.error(f"⚠️ {s1}/{s2} - Status: {p1} / {p2}")
            st.divider()

# --- 5. POSITION TRACKER ---
st.subheader("💼 Active Paper Trades")
if st.session_state.ledger:
    for t in st.session_state.ledger:
        st.success(f"**{t['side']} {t['pair']}** | Entry Z: {t['entry']}")
else:
    st.info("No active trades. Use the tabs above to enter a trade.")
