import streamlit as st
import pandas as pd
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. SETUP ---
st.set_page_config(page_title="NSE Auto-Pair Trader", layout="wide")
st_autorefresh(interval=15 * 1000, key="auto_trade_refresh")

# --- 2. DATA ENGINE ---
def get_market_data(s1, s2):
    try:
        tickers = f"{s1}.NS {s2}.NS"
        data = yf.download(tickers, period="2d", interval="1m", progress=False)['Close']
        p1, p2 = round(data[f"{s1}.NS"].iloc[-1], 2), round(data[f"{s2}.NS"].iloc[-1], 2)
        ratio = data[f"{s1}.NS"] / data[f"{s2}.NS"]
        mean, std = ratio.tail(60).mean(), ratio.tail(60).std()
        z_score = round((ratio.iloc[-1] - mean) / std, 2)
        return p1, p2, z_score
    except: return None, None, None

# --- 3. AUTO-TRADING LOGIC & STORAGE ---
if 'auto_ledger' not in st.session_state:
    st.session_state.auto_ledger = []

# --- 4. APP UI ---
st.title("🤖 NSE Autonomous Paper Trader")
st.write("The bot scans sectors and enters trades automatically when Z > 2.0 or Z < -2.0.")

PAIRS = [
    ("HDFCBANK", "ICICIBANK"), ("SBIN", "BANKBARODA"),
    ("TCS", "INFY"), ("WIPRO", "HCLTECH"),
    ("RELIANCE", "ONGC"), ("BPCL", "IOC")
]

# --- 5. THE STRATEGY ENGINE (THE BOT) ---
active_pair_names = [t['pair'] for t in st.session_state.auto_ledger]

for s1, s2 in PAIRS:
    p1, p2, z = get_market_data(s1, s2)
    pair_label = f"{s1}/{s2}"
    
    if z is not None:
        # AUTO-ENTRY LOGIC
        if pair_label not in active_pair_names:
            if z >= 2.0:
                st.session_state.auto_ledger.append({"pair": pair_label, "entry_z": z, "side": "SELL (High)"})
                st.toast(f"🤖 AUTO-SELL: {pair_label} at Z={z}")
            elif z <= -2.0:
                st.session_state.auto_ledger.append({"pair": pair_label, "entry_z": z, "side": "BUY (Low)"})
                st.toast(f"🤖 AUTO-BUY: {pair_label} at Z={z}")

# --- 6. LIVE PNL DASHBOARD ---
st.subheader("💼 Active Bot Positions")
if st.session_state.auto_ledger:
    total_pnl = 0
    for i, trade in enumerate(st.session_state.auto_ledger):
        t1, t2 = trade['pair'].split("/")
        _, _, curr_z = get_market_data(t1, t2)
        
        if curr_z is not None:
            # Calculate Profit
            z_move = (trade['entry_z'] - curr_z) if "SELL" in trade['side'] else (curr_z - trade['entry_z'])
            pnl = round(z_move * 1000, 2)
            total_pnl += pnl
            
            # AUTO-EXIT LOGIC (Close if Z returns to 0)
            if (trade['entry_z'] > 0 and curr_z <= 0.1) or (trade['entry_z'] < 0 and curr_z >= -0.1):
                st.session_state.auto_ledger.pop(i)
                st.success(f"✅ Target Hit! Closed {trade['pair']} for ₹{pnl}")
                st.rerun()

            col1, col2, col3, col4 = st.columns(4)
            col1.write(f"**{trade['pair']}**")
            col2.write(f"Side: {trade['side']}")
            col3.write(f"Z-Move: {trade['entry_z']} → {curr_z}")
            col4.markdown(f"**PnL: ₹{pnl}**")
    
    st.divider()
    st.metric("Total Session PnL", f"₹{round(total_pnl, 2)}")
else:
    st.info("Scanning markets... No trades meet the Z > 2.0 criteria yet.")
