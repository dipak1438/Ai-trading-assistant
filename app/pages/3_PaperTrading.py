import streamlit as st
import pandas as pd
import datetime
import requests

# --- Helper: Fetch Live Crypto Price ---
def get_live_price(symbol="BTCUSDT"):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        data = requests.get(url, timeout=5).json()
        return float(data["price"])
    except Exception:
        return None

def main():
    st.title("💸 Paper Trading ")

    st.write("""
    Trade crypto **risk-free** with a $10,000 demo balance.  
    Practice buy & sell orders and track your positions like a real exchange.
    """)

    # --- Init Session ---
    if "balance" not in st.session_state:
        st.session_state.balance = 10000.0
    if "trades" not in st.session_state:
        st.session_state.trades = []
    if "positions" not in st.session_state:
        st.session_state.positions = {}

    # ===== Currency Option =====
    currency = st.radio("💱 Display Currency", ["USD ($)", "INR (₹)"], horizontal=True)
    USD_INR_RATE = 83.0

    def cvt(val):
        return val if currency.startswith("USD") else val * USD_INR_RATE

    symbol_sign = "₹" if currency.startswith("INR") else "$"

    # --- Current Balance ---
    st.metric("💰 Available Balance", f"{symbol_sign}{cvt(st.session_state.balance):,.2f}")

    # === Holdings Table ===
    st.subheader("📊 Current Holdings")
    if st.session_state.positions:
        pos_data = []
        for sym, p in st.session_state.positions.items():
            last_price = get_live_price(sym) or p.get("last_price", p["avg_price"])
            p["last_price"] = last_price
            pos_data.append({
                "Symbol": sym,
                "Quantity": p["qty"],
                f"Avg Entry Price ({symbol_sign})": cvt(p["avg_price"]),
                f"Market Price ({symbol_sign})": cvt(last_price),
                f"Unrealized P/L ({symbol_sign})": cvt((last_price - p["avg_price"]) * p["qty"])
            })
        st.dataframe(pd.DataFrame(pos_data), use_container_width=True)
    else:
        st.info("No open positions.")

    st.markdown("---")

    # === Trade Controls ===
    st.subheader("📝 Place a Trade")

    crypto = st.selectbox("Select Symbol", ["BTCUSDT", "ETHUSDT"])
    qty = st.number_input("Quantity", min_value=0.001, step=0.001)

    # Fetch live market price automatically
    live_price = get_live_price(crypto)
    if live_price:
        st.success(f"💹 Live Market Price: ${live_price:,.2f}")
    else:
        st.warning("⚠️ Could not fetch live price, using fallback price.")
        live_price = 50000.0

    col1, col2 = st.columns(2)

    # ----- BUY -----
    if col1.button("✅ BUY", use_container_width=True):
        if qty > 0:
            cost_usd = qty * live_price
            if cost_usd <= st.session_state.balance:
                st.session_state.balance -= cost_usd
                pos = st.session_state.positions.get(crypto, {"qty": 0, "avg_price": 0})
                new_qty = pos["qty"] + qty
                new_avg = ((pos["qty"] * pos["avg_price"]) + cost_usd) / new_qty
                st.session_state.positions[crypto] = {
                    "qty": new_qty,
                    "avg_price": new_avg,
                    "last_price": live_price
                }
                st.session_state.trades.append({
                    "Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Symbol": crypto,
                    "Action": "Buy",
                    "Quantity": qty,
                    "Price (USD)": live_price,
                    "Total (USD)": cost_usd
                })
                st.success(f"✅ Bought {qty} {crypto} @ ${live_price:,.2f}")
            else:
                st.error("❌ Insufficient balance.")
        else:
            st.warning("Enter a valid quantity.")

    # ----- SELL -----
    if col2.button("❌ SELL", use_container_width=True):
        if qty > 0:
            cost_usd = qty * live_price
            pos = st.session_state.positions.get(crypto, {"qty": 0, "avg_price": live_price})
            new_qty = pos["qty"] - qty
            new_avg = market_price_usd = live_price

            st.session_state.balance += cost_usd
            if new_qty > 0:
                st.session_state.positions[crypto] = {
                    "qty": new_qty,
                    "avg_price": new_avg,
                    "last_price": live_price
                }
            else:
                st.session_state.positions.pop(crypto, None)

            st.session_state.trades.append({
                "Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Symbol": crypto,
                "Action": "Sell",
                "Quantity": qty,
                "Price (USD)": live_price,
                "Total (USD)": cost_usd
            })
            st.success(f"✅ Sold {qty} {crypto} @ ${live_price:,.2f}")
        else:
            st.warning("Enter a valid quantity.")

    st.markdown("---")

    # === Trade History Table ===
    st.subheader("📜 Trade History")
    if st.session_state.trades:
        df = pd.DataFrame(st.session_state.trades).copy()
        if currency.startswith("INR"):
            df["Price (INR)"] = df["Price (USD)"] * USD_INR_RATE
            df["Total (INR)"] = df["Total (USD)"] * USD_INR_RATE
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No trades yet.")

if __name__ == "__main__":
    main()
