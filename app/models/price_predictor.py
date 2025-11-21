import lightgbm as lgb
import joblib
import pandas as pd
from ta.momentum import RSIIndicator
import os

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add technical indicators & target column to the dataframe.
    """
    df = df.copy()
    df["returns"] = df["Close"].pct_change()
    df["sma20"] = df["Close"].rolling(20).mean()
    df["rsi14"] = RSIIndicator(df["Close"], 14).rsi()
    df["target"] = df["Close"].shift(-1)
    return df.dropna()

def train_model(df: pd.DataFrame, save_path: str = "models/crypto_lgb.pkl"):
    """
    Train LightGBM model and save to file.
    """
    df = add_features(df)
    features = ["Close", "Volume", "returns", "sma20", "rsi14"]
    X, y = df[features], df["target"]
    model = lgb.LGBMRegressor()
    model.fit(X, y)
    # ensure directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    joblib.dump(model, save_path)
    return model

def predict_next_price(df: pd.DataFrame, model_path: str = "models/crypto_lgb.pkl") -> float:
    """
    Load trained model and predict the next closing price.
    """
    # prepare features for the latest row
    df = add_features(df)
    latest = df.iloc[-1:]
    features = ["Close", "Volume", "returns", "sma20", "rsi14"]

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}. "
                                "Train model first using train_model().")

    model = joblib.load(model_path)
    next_price = model.predict(latest[features])[0]
    return float(next_price)
