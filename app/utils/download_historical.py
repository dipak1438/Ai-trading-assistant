import pandas as pd
import requests
import os

def get_klines(symbol="BTCUSDT", interval="1m", limit=1000):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    cols = [
        "Open_time","Open","High","Low","Close","Volume",
        "Close_time","Quote_asset_volume","Number_of_trades",
        "Taker_buy_base_asset_volume","Taker_buy_quote_asset_volume","Ignore"
    ]
    df = pd.DataFrame(data, columns=cols)
    df["Open_time"] = pd.to_datetime(df["Open_time"], unit="ms")
    df[["Open","High","Low","Close","Volume"]] = df[["Open","High","Low","Close","Volume"]].astype(float)
    return df[["Open_time","Open","High","Low","Close","Volume"]]

def save_csv(path="data/BTCUSDT_1m.csv", symbol="BTCUSDT", interval="1m", limit=1000):
    df = get_klines(symbol, interval, limit)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print("✅ Saved data at", path)

if __name__ == "__main__":
    save_csv()
