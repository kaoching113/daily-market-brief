#!/usr/bin/env python3
import json
from datetime import datetime, timezone, timedelta
from market_data import ITEMS, yahoo_fetch

def fetch_one(symbol):
    data = yahoo_fetch(symbol)
    meta = data["chart"]["result"][0]["meta"]
    price = meta["regularMarketPrice"]
    prev = meta.get("previousClose") or meta.get("chartPreviousClose")
    change = price - prev if prev else None
    pct = (change / prev * 100) if prev else None
    return {
        "price": price,
        "previousClose": prev,
        "change": change,
        "changePercent": pct,
        "currency": meta.get("currency"),
    }

def main():
    results = []
    for item in ITEMS:
        try:
            q = fetch_one(item["symbol"])
            results.append({**item, **q})
        except Exception as e:
            results.append({**item, "error": str(e)})

    tz = timezone(timedelta(hours=8))
    out = {
        "updatedAt": datetime.now(tz).strftime("%Y-%m-%d %H:%M"),
        "items": results,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
