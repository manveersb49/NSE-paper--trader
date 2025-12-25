import streamlit as st
import yfinance as yf
import pandas as pd
import statsmodels.api as sm
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & THEME ---
st.set_page_config(page_title="NSE Quant Terminal", layout="wide")
st_autorefresh(interval=30 * 1000, key="global_refresh")

# Custom UI Styling for iPhone
st.markdown("""
    <style>
    .stMetric { background-color: #161B22; border-radius: 10px; padding: 15px; border: 1px solid #30363D; }
    .pair-card { 
        background-color: #161B22; border-radius: 12px; padding: 15px; 
        margin-bottom: 10px; border: 1px solid #30363D;
    }
    .buy-sig { color: #39FF14; font-weight: bold; }
    .sell-sig { color: #FF3131; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. VIRTUAL WALLET SETUP ---
if 'balance' not in st.session_state:
    st.session_state.balance = 1000000.0  # ₹10 Lakhs Virtual Cash
if 'trades' not in st.session_state:
    st.session_state.trades = {} # Stores active virtual positions

# --- 3. SECTOR & PAIR DEFINITIONS ---
SECTORS = {
    "🏦 BANKS": [("HDFCBANK.NS", "ICICIBANK.NS"), ("SBIN.NS", "BANKBARODA.NS"), ("AXISBANK.NS", "KOTAKBANK.NS")],
    "⛽ ENERGY": [("RELIANCE.NS", "ONGC.NS"), ("BPCL.NS", "HINDPETRO.NS"), ("IOC.NS", "GAIL.NS")],
    "💻 IT": [("TCS.NS", "INFY.NS"), ("WIPRO.NS", "HCLTECH.NS"), ("TECHM.NS", "LTIM.NS")]
}

# --- 4. DATA ENGINE (Simultaneous Fetch) ---
@st.cache_data(ttl=25)
def fetch_nse_data():
    all_tickers = list(set([s for pairs in SECTORS.values() for p in pairs for s in p]))
    # Download 5 days of 5-minute data for all stocks at once
    df = yf.download(all_tickers, period="5d", interval="5m", progress=False)['Close']
    return df.ffill()

# --- 5. MAIN INTERFACE ---
st.title("⚡ NSE Paper Trading Radar")

# Dashboard Header
c1, c2, c3 = st.columns(3)
c1.metric("Virtual Cash", f"₹{round(st.session_state.balance, 2)}")
c2.metric("Active Trades", len(st.session_state.trades))
if c3.button("Reset Portfolio"):
    st.session_state.balance = 1000000.0
    st.session_state.trades = {}
    st.rerun()

prices = fetch_nse_data()
tabs = st.tabs(list(SECTORS.keys()))

for i, sector in enumerate(SECTORS.keys()):
    with tabs[i]:
        for s1, s2 in SECTORS[sector]:
            try:
                # Statistical Math (Z-Score)
                pair_df = prices[[s1, s2]].dropna()
                y, x = pair_df[s1], sm.add_constant(pair_df[s2])
                res = sm.OLS(y, x).fit()
                spread = pair_df[s1] - (res.params[1] * pair_df[s2])
                z = round((spread.iloc[-1] - spread.mean()) / spread.std(), 2)
                
                curr_p1, curr_p2 = pair_df[s1].iloc[-1], pair_df[s2].iloc[-1]
                pair_id = f"{s1}-{s2}"
                
                # Paper Trading Logic
                status = "Neutral"
                if z > 2.3 and pair_id not in st.session_state.trades:
                    st.session_state.trades[pair_id] = {"p1": curr_p1, "p2": curr_p2, "type": "SELL_SPREAD"}
                elif z < -2.3 and pair_id not in st.session_state.trades:
                    st.session_state.trades[pair_id] = {"p1": curr_p1, "p2": curr_p2, "type": "BUY_SPREAD"}
                
                # Close Trade at Mean Reversion (Z close to 0)
                if pair_id in st.session_state.trades and abs(z) < 0.2:
                    entry = st.session_state.trades[pair_id]
                    pnl = (curr_p1 - entry['p1']) if entry['type'] == "BUY_SPREAD" else (entry['p1'] - curr_p1)
                    st.session_state.balance += pnl
                    del st.session_state.trades[pair_id]
                    st.toast(f"Trade Closed! PnL: ₹{round(pnl, 2)}")

                # Card Display
                pnl_text = ""
                if pair_id in st.session_state.trades:
                    entry = st.session_state.trades[pair_id]
                    cur_pnl = (curr_p1 - entry['p1']) if entry['type'] == "BUY_SPREAD" else (entry['p1'] - curr_p1)
                    pnl_text = f" | <span style='color:yellow'>Live PnL: ₹{round(cur_pnl, 2)}</span>"

                st.markdown(f"""
                <div class="pair-card">
                    <div style="display: flex; justify-content: space-between;">
                        <span><b>{s1} / {s2}</b></span>
                        <span style="font-size: 1.2rem;">Z: <b>{z}</b></span>
                    </div>
                    <div style="font-size: 0.8rem; margin-top: 5px; color: #8B949E;">
                        {'🟢 IN TRADE' if pair_id in st.session_state.trades else '⚪ SCANNING'} {pnl_text}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except:
                continue
