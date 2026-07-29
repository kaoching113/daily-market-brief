#!/usr/bin/env python3
import json
from market_data import SYMBOLS, yahoo_fetch

def fetch_history(symbol, range_="6mo", interval="1d"):
    data = yahoo_fetch(symbol, {"range": range_, "interval": interval})
    result = data["chart"]["result"][0]
    timestamps = result["timestamp"]
    quote = result["indicators"]["quote"][0]
    candles = []
    for i, t in enumerate(timestamps):
        o, h, l, c = quote["open"][i], quote["high"][i], quote["low"][i], quote["close"][i]
        if None in (o, h, l, c):
            continue
        candles.append({"t": t, "o": round(o, 4), "h": round(h, 4), "l": round(l, 4), "c": round(c, 4)})
    return candles

def main():
    out = {}
    for symbol in SYMBOLS:
        try:
            out[symbol] = fetch_history(symbol)
        except Exception as e:
            out[symbol] = []
    print(json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    main()
