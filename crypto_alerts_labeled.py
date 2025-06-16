import requests
import pandas as pd
import os
import time

# Read API key from environment variable (set in GitHub Secrets)
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
HEADERS = {
    "x-cg-pro-api-key": COINGECKO_API_KEY
}
API_BASE_URL = "https://api.coingecko.com/api/v3"

def fetch_top_coins(n=300):
    coins = []
    pages = (n // 250) + (1 if n % 250 else 0)
    for page in range(1, pages + 1):
        url = f"{API_BASE_URL}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 250,
            "page": page,
            "price_change_percentage": "1h,24h,7d"
        }
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=15)
            response.raise_for_status()
            coins.extend(response.json())
            time.sleep(1)  # small delay to avoid bursts
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
    return pd.DataFrame(coins)

def generate_alerts(df):
    warming = []
    cooling = []
    strong = []

    for _, row in df.iterrows():
        symbol = row.get("symbol", "").upper()
        name = row.get("name", "")
        price = row.get("current_price", 0)
        pct_1h = row.get("price_change_percentage_1h_in_currency") or 0
        pct_24h = row.get("price_change_percentage_24h_in_currency") or 0
        pct_7d = row.get("price_change_percentage_7d_in_currency") or 0

        summary = f"{name} ({symbol}) - ${price:.4f} | {pct_1h:+.2f}% 1h | {pct_24h:+.2f}% 24h | {pct_7d:+.2f}% 7d"

        if pct_1h > 2 and pct_24h > 5 and pct_7d > 10:
            warming.append(summary)
        if pct_1h < -2 and pct_24h < -5:
            cooling.append(summary)
        if pct_1h > 5 or pct_24h > 10 or pct_7d > 20:
            strong.append(summary)

    return warming, cooling, strong

def save_alerts(warming, cooling, strong):
    with open("triggered_coins.csv", "w") as f:
        f.write("WARMING SIGNALS:\n")
        f.writelines(line + "\n" for line in warming)
        f.write("\nCOOLING SIGNALS:\n")
        f.writelines(line + "\n" for line in cooling)
        f.write("\nSTRONG GAINS:\n")
        f.writelines(line + "\n" for line in strong)
    print("✅ triggered_coins.csv updated.")

def main():
    print("🔄 Fetching top 300 coins...")
    df = fetch_top_coins(n=300)
    print("✅ Market data retrieved.")
    warming, cooling, strong = generate_alerts(df)
    save_alerts(warming, cooling, strong)

if __name__ == "__main__":
    main()
