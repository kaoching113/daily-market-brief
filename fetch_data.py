#!/usr/bin/env python3
import json
from datetime import datetime, timezone, timedelta
from market_data import ITEMS, yahoo_fetch

def last_close_before_market_day(symbol, meta):
    data = yahoo_fetch(symbol, {"range": "10d", "interval": "1d"})
    result = data["chart"]["result"][0]
    tz = timezone(timedelta(seconds=meta["gmtoffset"]))
    day = lambda ts: datetime.fromtimestamp(ts, tz).date()
    market_day = day(meta["regularMarketTime"])
    closes = result["indicators"]["quote"][0].get("close", [])
    earlier = [c for ts, c in zip(result.get("timestamp", []), closes)
               if c is not None and day(ts) < market_day]
    return earlier[-1] if earlier else None

def fetch_one(symbol):
    data = yahoo_fetch(symbol)
    meta = data["chart"]["result"][0]["meta"]
    price = meta["regularMarketPrice"]
    prev = meta.get("previousClose") or meta.get("chartPreviousClose")
    # Yahoo 的現貨指數前收盤可能落後一個交易日（如 ^TWII、^HSI），改以日K為準
    if meta.get("instrumentType") == "INDEX":
        try:
            prev = last_close_before_market_day(symbol, meta) or prev
        except Exception:
            pass
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
