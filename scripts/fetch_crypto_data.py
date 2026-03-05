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

# CoinGecko Free API
BASE_URL = "https://api.coingecko.com/api/v3"

# 스테이블코인 제외 리스트
STABLECOINS = {
    'tether', 'usd-coin', 'dai', 'trueusd', 'first-digital-usd',
    'ethena-usde', 'usds', 'paypal-usd', 'frax', 'binance-peg-busd',
    'tether-eurt', 'gemini-dollar', 'paxos-standard', 'celo-dollar',
    'binance-usd', 'terrausd', 'magic-internet-money', 'liquity-usd',
    'usdd', 'tusd', 'true-usd',
    'usd1', 'usual-usd', 'usd0', 'circle-eurc', 'eurc', 'usdtb', 'usdai', 'gho',
    'usdf', 'usdf-stablecoin',
}

OUTPUT_DIR = "data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "crypto_heatmap.json")


def fetch_markets(page=1, per_page=100):
    """CoinGecko /coins/markets 엔드포인트에서 데이터 가져오기"""
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
    """필요한 필드만 추출하고 스테이블코인 제외"""
    processed = []

    for coin in raw_data:
        if coin['id'] in STABLECOINS:
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
            "price_change_percentage_7d": round(coin.get("price_change_percentage_7d_in_currency") or coin.get("price_change_percentage_7d") or 0, 2),
            "price_change_percentage_30d": round(coin.get("price_change_percentage_30d_in_currency") or coin.get("price_change_percentage_30d") or 0, 2),
            "ath": coin.get("ath", 0),
            "ath_change_percentage": round(coin.get("ath_change_percentage") or 0, 2),
            "circulating_supply": coin.get("circulating_supply", 0),
            "max_supply": coin.get("max_supply"),
        })

    return processed


def main():
    print(f"🚀 Fetching crypto data at {datetime.now(timezone.utc).isoformat()}")

    all_coins = []

    # 2페이지 가져와서 스테이블코인 제외 후 100개 확보
    for page in range(1, 3):
        print(f"  Fetching page {page}...")
        data = fetch_markets(page=page, per_page=125)
        all_coins.extend(data)
        if page < 2:
            time.sleep(1.5)  # Rate limit 존중

    # 데이터 가공
    processed = process_data(all_coins)

    # 시총 순으로 정렬 후 상위 100개
    processed.sort(key=lambda x: x["market_cap"], reverse=True)
    processed = processed[:100]

    print(f"  ✅ {len(processed)} coins processed (stablecoins excluded)")

    # 메타데이터 추가
    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_coins": len(processed),
        "coins": processed
    }

    # 디렉토리 생성 및 저장
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # coins 배열만 저장 (HTML에서 바로 파싱)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(processed, f, ensure_ascii=False)

    # 메타데이터 포함 버전도 저장
    with open(os.path.join(OUTPUT_DIR, "crypto_heatmap_meta.json"), "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"  💾 Saved to {OUTPUT_FILE}")
    print(f"  📊 Top 5: {', '.join([c['symbol'].upper() for c in processed[:5]])}")


if __name__ == "__main__":
    main()
