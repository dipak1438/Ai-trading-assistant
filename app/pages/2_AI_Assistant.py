import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from services.binance_api import get_live_data
from models.price_predictor import predict_next_price


def ai_price_prediction():
    st.title("🤖 AI Price Prediction")

    # Symbol & Interval selection
    symbol = st.selectbox("Select Symbol", ["BTCUSDT", "ETHUSDT"])
    interval = st.selectbox("Time Frame", ["1m", "5m", "15m", "1h"])

    if st.button("Predict"):
        try:
            # ✅ Fetch latest data from Binance
            df = get_live_data(symbol, interval, limit=100)

            # ✅ Clean column names
            df.columns = df.columns.str.strip()

            # ✅ Make sure Volume is numeric
            if "Volume" in df.columns:
                df["Volume"] = (
                    df["Volume"].astype(str)
                    .str.replace(",", "", regex=False)
                    .str.strip()
                )
                df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0)

            # ✅ Predict next price
            next_price = predict_next_price(df)

            last_close = df["Close"].iloc[-1]
            diff = next_price - last_close

            if diff > 0:
                signal = "🟢 BUY"
            elif diff < 0:
                signal = "🔴 SELL"
            else:
                signal = "⚪ HOLD"

            confidence = abs(diff / last_close) * 100

            st.metric("Predicted Next Close", f"${next_price:.2f}")
            st.metric("AI Signal", f"{signal}")
            st.metric("Confidence", f"{confidence:.2f}%")

            # ✅ Plot candlestick chart
            fig = go.Figure(data=[go.Candlestick(
                x=df["Time"],
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"]
            )])
            fig.update_layout(
                xaxis_rangeslider_visible=False,
                template="plotly_dark",
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"⚠️ Error fetching or predicting data: {e}")


if __name__ == "__main__":
    ai_price_prediction()
