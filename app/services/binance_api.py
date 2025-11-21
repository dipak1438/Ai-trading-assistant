import requests
import pandas as pd

def get_live_data(symbol="BTCUSDT", interval="1m", limit=100):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(url, params=params)
    data = r.json()

    df = pd.DataFrame(data, columns=[
        "Open Time","Open","High","Low","Close","Volume",
        "Close Time","Quote Asset Volume","Number of Trades",
        "Taker Buy Base","Taker Buy Quote","Ignore"
    ])
    df["Open"]  = df["Open"].astype(float)
    df["High"]  = df["High"].astype(float)
    df["Low"]   = df["Low"].astype(float)
    df["Close"] = df["Close"].astype(float)
    df["Time"]  = pd.to_datetime(df["Open Time"], unit="ms")
    return df[["Time","Open","High","Low","Close","Volume"]]
