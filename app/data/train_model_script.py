import os
import pandas as pd
from app.models.price_predictor import train_model

# Go to project root
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# ✅ CSV path
csv_path = os.path.join(base_dir, "app", "data", "BTCUSDT_1m.csv")

# ✅ Model output path
model_path = os.path.join(base_dir, "models", "crypto_lgb.pkl")

# ✅ Load CSV
df = pd.read_csv(csv_path)

# 🔧 Clean/convert Volume to numeric
# Remove commas/spaces and convert to float; replace non-numeric with NaN, then fill
if "Volume" in df.columns:
    df["Volume"] = (
        df["Volume"]
        .astype(str)                    # ensure string for cleaning
        .str.replace(",", "", regex=False)  # remove thousand separators if any
        .str.strip()
    )
    df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0)

# ✅ Train and save model
train_model(df, save_path=model_path)

print("✅ Model training completed and saved at:", model_path)
