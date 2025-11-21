import pandas as pd
from services.binance_api import get_live_data

# BTCUSDT ke 1000 minute candles download karo
df = get_live_data("BTCUSDT", interval="1m", limit=1000)

# CSV me save karo
df.to_csv("../data/BTCUSDT_1m.csv", index=False)
print("✅ Data saved to ../data/BTCUSDT_1m.csv")
