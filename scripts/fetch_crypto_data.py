"""
Crypto Heatmap Data Fetcher
CoinGecko API에서 시총 Top 100 코인 데이터 수집 (스테이블코인 제외)
GitHub Actions에서 매시간 실행
"""

import requests
import json
import os
import time
from datetime import datetime, timezone

BASE_URL   = "https://api.coingecko.com/api/v3"
OUTPUT_DIR  = "data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "crypto_heatmap.json")

# ID 기반 스테이블코인 차단
STABLECOINS = {
    'tether', 'usd-coin', 'dai', 'trueusd', 'true-usd',
    'first-digital-usd', 'paypal-usd', 'frax',
    'gemini-dollar', 'paxos-standard', 'liquity-usd',
    'terrausd', 'magic-internet-money', 'usdd', 'tusd',
    'usd1', 'wlfi-usd1',
    'bfusd', 'binance-usd', 'binance-peg-busd', 'busd',
    'rlusd', 'ripple-usd',
    'usyc', 'hashnote-usyc',
    'ousg', 'ondo-us-dollar-yield',
    'usdg', 'usdg-stablecoin',
    'usdf', 'usdf-stablecoin',
    'ustb', 'usdtb', 'usdai',
    'usdx', 'usdx-money',
    'circle-eurc', 'eurc', 'euro-coin',
    'tether-eurt', 'eurt',
    'stable', 'stable-usd',
    'figure-heloc', 'figr-heloc',
    'ethena-usde', 'usds', 'usual-usd', 'usd0',
    'gho', 'celo-dollar',
}

# 심볼 기반 스테이블코인 차단
STABLECOIN_SYMBOLS = {
    'usdt','usdc','dai','tusd','usdp','usdd','frax','lusd','mim',
    'gusd','busd','usdn','ust','usd1','bfusd','rlusd','usyc',
    'usdg','usdf','ustb','usdtb','usdai','eurc','eurt','ousg',
    'usdx','usd0','usds','usde','usdm','usdy',
    'stable','gho','cusd','figr','fei','susd','musd',
}


def fetch_markets(page=1, per_page=125):
    url = f"{BASE_URL}/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": per_page,
        "page": page,
        "sparkline": "false",
        "price_change_percentage": "24h,7d,30d",
        "locale": "en"
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def process_data(raw_data):
    processed = []
    for coin in raw_data:
        if coin['id'] in STABLECOINS:
            continue
        if coin.get('symbol', '').lower() in STABLECOIN_SYMBOLS:
            continue
        processed.append({
            "id": coin["id"],
            "symbol": coin["symbol"],
            "name": coin["name"],
            "image": coin.get("image", ""),
            "current_price": coin.get("current_price", 0),
            "market_cap": coin.get("market_cap", 0),
            "market_cap_rank": coin.get("market_cap_rank", 999),
            "total_volume": coin.get("total_volume", 0),
            "price_change_percentage_24h": round(coin.get("price_change_percentage_24h") or 0, 2),
            "price_change_percentage_7d": round(coin.get("price_change_percentage_7d_in_currency") or 0, 2),
            "price_change_percentage_30d": round(coin.get("price_change_percentage_30d_in_currency") or 0, 2),
            "ath": coin.get("ath", 0),
            "ath_change_percentage": round(coin.get("ath_change_percentage") or 0, 2),
            "circulating_supply": coin.get("circulating_supply", 0),
            "max_supply": coin.get("max_supply"),
        })
    return processed


def main():
    print(f"🚀 Fetching crypto data at {datetime.now(timezone.utc).isoformat()}")

    all_coins = []
    for page in range(1, 3):
        print(f"  Fetching page {page}...")
        data = fetch_markets(page=page)
        all_coins.extend(data)
        if page < 2:
            time.sleep(1.5)

    processed = process_data(all_coins)
    processed.sort(key=lambda x: x["market_cap"], reverse=True)
    processed = processed[:100]

    print(f"  ✅ {len(processed)} coins processed (stablecoins excluded)")

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_coins": len(processed),
        "coins": processed
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(processed, f, ensure_ascii=False)

    with open(os.path.join(OUTPUT_DIR, "crypto_heatmap_meta.json"), "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"  💾 Saved to {OUTPUT_FILE}")
    print(f"  📊 Top 5: {', '.join([c['symbol'].upper() for c in processed[:5]])}")


if __name__ == "__main__":
    main()
