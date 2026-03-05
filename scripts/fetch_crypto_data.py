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
    # 메이저 달러 페그
    'tether', 'usd-coin', 'dai', 'trueusd', 'true-usd',
    'first-digital-usd', 'paypal-usd', 'frax',
    'gemini-dollar', 'paxos-standard', 'liquity-usd',
    'terrausd', 'magic-internet-money', 'usdd',

    # USD1 (World Liberty Financial)
    'usd1', 'wlfi-usd1', 'world-liberty-financial-usd1',

    # BFUSD (Binance)
    'bfusd', 'binance-usd', 'binance-peg-busd', 'busd', 'binance-futures-usd',

    # RLUSD (Ripple)
    'rlusd', 'ripple-usd', 'ripple-usd-rlusd',

    # USYC (Hashnote — 수익형 달러 페그)
    'usyc', 'hashnote-usyc', 'hashnote-short-duration-yield-coin',

    # OUSG (Ondo)
    'ousg', 'ondo-us-dollar-yield', 'ondo-short-term-us-government-bond',

    # USDG, USDF
    'usdg', 'usdg-stablecoin',
    'usdf', 'usdf-stablecoin',

    # USTB, USDAI
    'ustb', 'usdtb', 'usdai',

    # USDX
    'usdx', 'usdx-stablecoin', 'usdx-money',

    # EURC (Circle Euro)
    'circle-eurc', 'eurc', 'euro-coin',

    # EURT (Tether Euro)
    'tether-eurt', 'eurt',

    # STABLE 토큰
    'stable', 'stable-usd', 'raft-r',

    # FIGR_HELOC (Figure 주택담보 토큰 — 페그 자산)
    'figure-heloc', 'figr-heloc', 'figure-markets-usd',

    # 기타 달러 페그
    'ethena-usde', 'usds', 'usual-usd', 'usd0',
    'gho', 'celo-dollar',
    'tusd',

    # LEO (Bitfinex 유틸리티 — 거래소 토큰이나 가격 변동성 낮아 필터)
    # → 제거: LEO는 스테이블코인 아님, 유지
}

# 심볼 기반 추가 필터 (ID가 달라도 차단)
STABLECOIN_SYMBOLS = {
    'usdt', 'usdc', 'dai', 'tusd', 'usdp', 'usdd', 'frax', 'lusd', 'mim',
    'gusd', 'busd', 'usdn', 'ust', 'usd1', 'bfusd', 'rlusd', 'usyc',
    'usdg', 'usdf', 'ustb', 'usdtb', 'usdai', 'eurc', 'eurt', 'ousg',
    'usdx', 'usd0', 'usds', 'usde', 'usdm', 'usdy', 'ondo',
    'stable', 'gho', 'celo', 'cusd', 'figr',
}
OUTPUT_DIR  = "data"
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
        # ID 기반 필터
        if coin['id'] in STABLECOINS:
            continue
        if coin['symbol'].lower() in STABLECOIN_SYMBOLS:
            continue
        # 심볼 기반 추가 필터 (USD/EUR 페그 패턴)
        symbol = coin.get('symbol', '').lower()
        if symbol in {'usdt','usdc','busd','dai','tusd','usdp','usdn','frax',
                      'lusd','usdd','usde','eurc','eurt','usd1','bfusd','rlusd',
                      'usyc','usdg','usdf','ustb','usdtb','usdai','gho',
                      'usd0','usds','gusd','usdp','ust','mim','fei','usdx',
                      'stable','figr'}:
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
