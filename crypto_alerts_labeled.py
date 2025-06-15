import pandas as pd
import pandas_ta as ta
import requests
import time
import os
from datetime import datetime

# Use API key if provided
headers = {}
api_key = os.getenv("COINGECKO_API_KEY")
if api_key:
    headers["x-cg-pro-api-key"] = api_key

def fetch_top_300():
    all_coins = []
    for page in range(1, 4):  # Top 300 coins
        try:
            response = requests.get(
                "https://api.coingecko.com/api/v3/coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": 100,
                    "page": page,
                    "price_change_percentage": "24h"
                },
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            all_coins.extend(response.json())
            time.sleep(1)  # Avoid rate limiting
        except Exception as e:
            print(f"Failed to fetch page {page}: {e}")
    df = pd.DataFrame(all_coins)[[
        "id", "symbol", "current_price", "market_cap",
        "total_volume", "price_change_percentage_24h"
    ]]
    return df

def calculate_indicators(df):
    results = []
    for _, row in df.iterrows():
        coin_id = row['id']
        for attempt in range(3):
            try:
                ohlc_resp = requests.get(
                    f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
                    params={"vs_currency": "usd", "days": "7", "interval": "hourly"},
                    headers=headers,
                    timeout=10
                )
                ohlc_resp.raise_for_status()
                ohlc = ohlc_resp.json()
                if 'prices' not in ohlc or len(ohlc['prices']) < 50:
                    raise ValueError("Missing or insufficient price data")
                prices = [p[1] for p in ohlc['prices']]
                break
            except Exception as e:
                if attempt == 2:
                    print(f"Failed for coin {row['symbol']} after 3 attempts: {e}")
                    prices = []
                else:
                    print(f"Retry {attempt + 1} for coin {row['symbol']}...")
                    time.sleep(3)
        if len(prices) < 50:
            continue
        price_series = pd.Series(prices)
        rsi = ta.rsi(price_series, length=14).iloc[-1]
        ema12 = ta.ema(price_series, length=12).iloc[-1]
        ema26 = ta.ema(price_series, length=26).iloc[-1]
        current_price = price_series.iloc[-1]
        results.append({
            "symbol": row['symbol'],
            "price": current_price,
            "market_cap": row['market_cap'],
            "volume": row['total_volume'],
            "24h %": row['price_change_percentage_24h'],
            "RSI": rsi,
            "EMA12": ema12,
            "EMA26": ema26
        })
    return pd.DataFrame(results)

def categorize(df):
    warming = df[(df['RSI'] > 50) & (df['RSI'] <= 70) & (df['EMA12'] > df['EMA26']) & (df['price'] > df['EMA12'])].copy()
    warming['category'] = 'warming'
    cooling = df[(df['RSI'] > 75) & (df['price'] < df['EMA12'])].copy()
    cooling['category'] = 'cooling'
    strong = df[(df['RSI'] > 60) & (df['EMA12'] > df['EMA26']) & (df['price'] > df['EMA12'])].copy()
    strong['category'] = 'strong'
    return pd.concat([warming, cooling, strong], ignore_index=True)

def main():
    df = fetch_top_300()
    print("Fetched top 300 coins")
    indicators = calculate_indicators(df)
    print("Calculated technical indicators")
    categorized = categorize(indicators)
    categorized.to_csv("triggered_coins.csv", index=False)
    print("triggered_coins.csv updated!")

if __name__ == "__main__":
    main()
