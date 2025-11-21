import streamlit as st
import pandas as pd
from pycoingecko import CoinGeckoAPI
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

cg = CoinGeckoAPI()

# ✅ Step 1: Fetch Data
def get_historical_data(symbol="bitcoin", days=180, vs_currency="usd"):
    data = cg.get_coin_market_chart_by_id(id=symbol, vs_currency=vs_currency, days=days)
    prices = data["prices"]
    df = pd.DataFrame(prices, columns=["timestamp", "price"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df

# ✅ Step 2: Indicators
def add_indicators(df):
    df["SMA_10"] = df["price"].rolling(window=10).mean()
    df["EMA_10"] = df["price"].ewm(span=10, adjust=False).mean()

    delta = df["price"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    ema12 = df["price"].ewm(span=12, adjust=False).mean()
    ema26 = df["price"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    df = df.dropna()
    return df

# ✅ Step 3: Train Model
def train_model(df):
    df["Target"] = (df["price"].shift(-1) > df["price"]).astype(int)  # 1=UP, 0=DOWN
    df = df.dropna()

    X = df[["SMA_10", "EMA_10", "RSI", "MACD", "Signal"]]
    y = df["Target"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    acc = accuracy_score(y_test, model.predict(X_test))
    return model, acc, df

# ✅ Step 4: Streamlit Page
def ai_model_page():
    st.title("🤖 AI Trading Model")

    symbol = st.selectbox("Select Coin", ["bitcoin", "ethereum"])
    days = st.slider("Select Days", 1, 365, 180)

    df = get_historical_data(symbol, days)
    df = add_indicators(df)

    model, acc, df = train_model(df)

    st.metric("📊 Model Accuracy", f"{acc*100:.2f}%")

    latest_features = df[["SMA_10", "EMA_10", "RSI", "MACD", "Signal"]].iloc[-1:].values
    proba = model.predict_proba(latest_features)[0]
    prediction = model.predict(latest_features)[0]

    confidence = max(proba) * 100

    # ✅ Decision Logic
    if confidence < 55:
        st.warning("😐 AI Suggestion: **HOLD (Low Confidence)**")
    elif prediction == 1:
        st.success(f"✅ AI Suggestion: **BUY (Price may go UP)** | Confidence: {confidence:.2f}%")
    else:
        st.error(f"❌ AI Suggestion: **SELL (Price may go DOWN)** | Confidence: {confidence:.2f}%")

# Run
if __name__ == "__main__":
    ai_model_page()
