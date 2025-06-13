import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Crypto Alerts Dashboard", layout="wide")
st.title("📊 Crypto Technical Alert Dashboard")

DATA_FILE = "triggered_coins.csv"

if not os.path.exists(DATA_FILE):
    st.warning("No alerts found. Run the data updater script first.")
    st.stop()

df = pd.read_csv(DATA_FILE)

if df.empty:
    st.info("No alerts triggered in the latest cycle.")
    st.stop()

df['price_change_percentage_24h'] = df['price_change_percentage_24h'].round(2)
df['current_price'] = df['current_price'].round(4)

# Split signal types
warming_df = df[df['signal'] == 'warming']
cooling_df = df[df['signal'] == 'cooling']
strong_df = df[df['signal'] == 'strong']

# === WARMING ===
st.subheader("🔥 WARMING (Potential Breakouts)")
if not warming_df.empty:
    st.dataframe(
        warming_df[['symbol', 'current_price', 'price_change_percentage_24h', 'rsi', 'ema20', 'ema50']]
        .rename(columns={
            'symbol': 'Coin', 'current_price': 'Price (USD)',
            'price_change_percentage_24h': '% Change (24h)',
            'rsi': 'RSI', 'ema20': 'EMA20', 'ema50': 'EMA50'
        }).sort_values(by='% Change (24h)', ascending=False),
        use_container_width=True
    )
else:
    st.write("✅ No warming signals at this time.")

# === COOLING ===
st.subheader("❄️ COOLING (Likely Dip / Reversal)")
if not cooling_df.empty:
    st.dataframe(
        cooling_df[['symbol', 'current_price', 'price_change_percentage_24h', 'rsi', 'ema20']]
        .rename(columns={
            'symbol': 'Coin', 'current_price': 'Price (USD)',
            'price_change_percentage_24h': '% Change (24h)',
            'rsi': 'RSI', 'ema20': 'EMA20'
        }).sort_values(by='RSI', ascending=False),
        use_container_width=True
    )
else:
    st.write("✅ No cooling signals at this time.")

# === STRONG ALERTS ===
st.subheader("🧠 STRONG INDIVIDUAL SIGNALS")
if not strong_df.empty:
    st.dataframe(
        strong_df[['symbol', 'current_price', 'price_change_percentage_24h', 'rsi', 'ema20', 'ema50']]
        .rename(columns={
            'symbol': 'Coin', 'current_price': 'Price (USD)',
            'price_change_percentage_24h': '% Change (24h)',
            'rsi': 'RSI', 'ema20': 'EMA20', 'ema50': 'EMA50'
        }).sort_values(by='% Change (24h)', ascending=False),
        use_container_width=True
    )
else:
    st.write("✅ No standalone strong indicators detected.")