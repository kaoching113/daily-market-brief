#!/usr/bin/env python3
import json
import urllib.request
import urllib.parse

ITEMS = [
    {"group": "股市指數", "name": "台灣加權指數", "symbol": "^TWII"},
    {"group": "股市指數", "name": "中國A50", "symbol": "XIN9.FGI"},
    {"group": "股市指數", "name": "小道瓊", "symbol": "YM=F"},
    {"group": "股市指數", "name": "小那斯達克", "symbol": "NQ=F"},
    {"group": "股市指數", "name": "德國DAX", "symbol": "^GDAXI"},
    {"group": "股市指數", "name": "恆生指數", "symbol": "^HSI"},
    {"group": "商品", "name": "黃金", "symbol": "GC=F"},
    {"group": "商品", "name": "輕原油", "symbol": "CL=F"},
    {"group": "匯率", "name": "美元", "symbol": "TWD=X"},
    {"group": "匯率", "name": "歐元", "symbol": "EURTWD=X"},
    {"group": "匯率", "name": "人民幣", "symbol": "CNYTWD=X"},
    {"group": "匯率", "name": "比特幣", "symbol": "BTC-USD"},
]

SYMBOLS = [item["symbol"] for item in ITEMS]

def yahoo_fetch(symbol, params=None):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}"
    if params:
        url += f"?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.load(resp)
