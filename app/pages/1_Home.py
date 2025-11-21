import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime

st.title("💹 Live Crypto Chart")

# ---- 🔹 User Inputs ----
col1, col2, col3 = st.columns(3)

with col1:
    symbol = st.selectbox(
        "Select Coin Pair",
        ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
        index=0
    )

with col2:
    chart_type = st.radio(
        "Chart Type",
        ["Candlestick", "Line"],
        horizontal=True
    )

with col3:
    timeframe = st.selectbox(
        "Time Frame",
        ["1m","5m","15m","1h","4h","1d"],
        index=3
    )

# ---- 🔹 Fetch Data ----
def get_klines(symbol, interval="1h", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    r = requests.get(url).json()
    df = pd.DataFrame(r, columns=[
        "Open time","Open","High","Low","Close","Volume",
        "Close time","q","n","tbbav","tbqav","Ignore"
    ])
    df["Open"] = df["Open"].astype(float)
    df["High"] = df["High"].astype(float)
    df["Low"]  = df["Low"].astype(float)
    df["Close"]= df["Close"].astype(float)
    df["Time"] = pd.to_datetime(df["Open time"], unit='ms')
    return df

data = get_klines(symbol, timeframe, 200)

# ---- 🔹 Plot ----
fig = go.Figure()

if chart_type == "Candlestick":
    fig.add_trace(go.Candlestick(
        x=data["Time"],
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        name=symbol
    ))
else:
    fig.add_trace(go.Scatter(
        x=data["Time"],
        y=data["Close"],
        mode="lines",
        name=symbol
    ))

fig.update_layout(
    xaxis_rangeslider_visible=False,
    height=600,
    title=f"{symbol} - {timeframe} Chart"
)
st.plotly_chart(fig, use_container_width=True)
