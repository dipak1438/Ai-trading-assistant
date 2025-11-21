import streamlit as st
import pandas as pd
import numpy as np
from pycoingecko import CoinGeckoAPI
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

cg = CoinGeckoAPI()

# ------------------ Fetch Data ------------------ #
def get_historical_data(symbol="bitcoin", days=180, vs_currency="usd"):
    data = cg.get_coin_market_chart_by_id(id=symbol, vs_currency=vs_currency, days=days)
    prices = data["prices"]
    df = pd.DataFrame(prices, columns=["timestamp", "price"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df

# ------------------ Prepare Data for LSTM ------------------ #
def prepare_lstm_data(df, window_size=30):
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(df[["price"]])

    X, y = [], []
    for i in range(window_size, len(scaled_data)):
        X.append(scaled_data[i-window_size:i, 0])
        # If next price > current → Buy (1), else Sell (-1)
        y.append(1 if scaled_data[i, 0] > scaled_data[i-1, 0] else -1)

    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))  # (samples, timesteps, features)
    return X, y, scaler

# ------------------ Train LSTM Model ------------------ #
def train_lstm(df):
    X, y, scaler = prepare_lstm_data(df)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    model = tf.keras.Sequential([
        tf.keras.layers.LSTM(50, return_sequences=True, input_shape=(X_train.shape[1], 1)),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.LSTM(50, return_sequences=False),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(25, activation='relu'),
        tf.keras.layers.Dense(1, activation='tanh')  # -1 to 1 (Sell to Buy)
    ])

    model.compile(optimizer='adam', loss='mse', metrics=['accuracy'])
    model.fit(X_train, y_train, epochs=5, batch_size=32, verbose=1)

    loss, acc = model.evaluate(X_test, y_test, verbose=0)
    return model, acc, scaler

# ------------------ Streamlit UI ------------------ #
def ai_lstm_strategy_app():
    st.title("🤖 LSTM AI Trading Strategy")

    coin = st.selectbox("Select Coin", ["bitcoin", "ethereum"])
    days = st.slider("Select Days of Historical Data", 1, 365, 180)

    if st.button("🔮 Run LSTM Model"):
        with st.spinner("Training LSTM Model... Please wait ⏳"):
            df = get_historical_data(coin, days)
            st.line_chart(df.set_index("timestamp")["price"])

            model, accuracy, scaler = train_lstm(df)
            st.success(f"✅ Model Trained with Accuracy: {accuracy:.2f}")

            # Last window ka data le kar predict karo
            window_size = 30
            last_data = df["price"].values[-window_size:]
            scaled_last_data = scaler.transform(last_data.reshape(-1, 1))
            X_input = np.reshape(scaled_last_data, (1, window_size, 1))

            prediction = model.predict(X_input)[0][0]

            if prediction > 0.2:
                st.success("📈 Signal: BUY")
            elif prediction < -0.2:
                st.error("📉 Signal: SELL")
            else:
                st.info("⚖️ Signal: HOLD")

# ------------------ Run App ------------------ #
if __name__ == "__main__":
    ai_lstm_strategy_app()
