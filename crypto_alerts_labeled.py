import requests
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime

def fetch_top_500():
    all_coins = []
    for page in range(1, 6):
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 100,
            "page": page,
            "sparkline": False,
            "price_change_percentage": "24h"
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            all_coins.extend(response.json())
        else:
            print(f"Failed to fetch page {page}: {response.status_code}")
        time.sleep(1.2)

    df = pd.DataFrame(all_coins)[[
        'id', 'symbol', 'current_price', 'market_cap',
        'total_volume', 'price_change_percentage_24h'
    ]]
    df['timestamp'] = datetime.utcnow()
    return df

def apply_indicators(df):
    df['rsi'] = ta.rsi(df['current_price'], length=14)
    df['ema20'] = ta.ema(df['current_price'], length=20)
    df['ema50'] = ta.ema(df['current_price'], length=50)
    df['volume_avg'] = df['total_volume'].rolling(window=7).mean()

    # Warming
    df['EMA_bullish'] = (df['ema20'] > df['ema50']) & (df['current_price'] >= df['ema20'] * 0.98)
    df['Volume_surge'] = df['total_volume'] > (df['volume_avg'] * 1.5)
    df['RSI_momentum'] = df['rsi'] > 70

    # Cooling
    df['RSI_overbought'] = df['rsi'] > 80
    df['Price_dropping_below_ema20'] = df['current_price'] < df['ema20'] * 0.98
    df['Volume_high'] = df['total_volume'] > (df['volume_avg'] * 1.2)

    return df

def classify_alerts(df):
    warming_df = df[df['EMA_bullish'] & df['Volume_surge']]
    cooling_df = df[df['RSI_overbought'] & df['Price_dropping_below_ema20'] & df['Volume_high']]

    # NEW: Strong Alerts = any of the 3 conditions
    strong_alert_df = df[
        df['RSI_momentum'] | df['EMA_bullish'] | df['Volume_surge']
    ]

    warming_alerts = [
        f"{row['symbol'].upper()}: ${row['current_price']:.3f} ({row['price_change_percentage_24h']:.2f}% 24h) — EMA Bullish, Volume Surge{' ⚡ RSI > 70' if row['RSI_momentum'] else ''}"
        for _, row in warming_df.iterrows()
    ]

    cooling_alerts = [
        f"{row['symbol'].upper()}: ${row['current_price']:.3f} ({row['price_change_percentage_24h']:.2f}% 24h) — RSI > 80, Price < EMA20, High Volume"
        for _, row in cooling_df.iterrows()
    ]

    strong_alerts = [
        f"{row['symbol'].upper()}: ${row['current_price']:.3f} ({row['price_change_percentage_24h']:.2f}% 24h) — " +
        ", ".join([
            condition for condition, met in [
                ("RSI > 70", row['RSI_momentum']),
                ("EMA Bullish", row['EMA_bullish']),
                ("Volume Surge", row['Volume_surge'])
            ] if met
        ])
        for _, row in strong_alert_df.iterrows()
    ]

    return warming_alerts, cooling_alerts, strong_alerts, warming_df, cooling_df, strong_alert_df

def main():
    df = fetch_top_500()
    df = apply_indicators(df)
    warming_alerts, cooling_alerts, strong_alerts, warming_df, cooling_df, strong_df = classify_alerts(df)

    print("\n🔥 WARMING (Potential Price Surge)")
    print("\n".join([" - " + a for a in warming_alerts]) or "No warming signals detected.")

    print("\n❄️ COOLING (Likely Dip / Reversal)")
    print("\n".join([" - " + a for a in cooling_alerts]) or "No cooling signals detected.")

    print("\n🧠 STRONG INDIVIDUAL SIGNALS")
    print("\n".join([" - " + a for a in strong_alerts]) or "No individual strong indicators triggered.")

    # Save for Streamlit
    combined_df = pd.concat([
        warming_df.assign(signal='warming'),
        cooling_df.assign(signal='cooling'),
        strong_df.assign(signal='strong')
    ]).drop_duplicates(subset='symbol')  # Avoid duplicates if overlap
    combined_df.to_csv("triggered_coins.csv", index=False)

if __name__ == "__main__":
    main()