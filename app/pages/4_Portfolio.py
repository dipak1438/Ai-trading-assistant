import streamlit as st
import pandas as pd
import random
from pycoingecko import CoinGeckoAPI

# CoinGecko client
cg = CoinGeckoAPI()

# Symbol → CoinGecko ID map
COIN_MAP = {
    "BTC": "bitcoin",
    "BTCUSDT": "bitcoin",
    "ETH": "ethereum",
    "ETHUSDT": "ethereum",
    "DOGE": "dogecoin"
}

USD_INR_RATE = 83.0  # update if you want live INR conversion

def safe_rerun():
    """Try to rerun the Streamlit script in a way compatible with different Streamlit versions."""
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            # can't rerun — just continue
            pass

def get_live_price(symbol: str) -> float:
    """Fetch real crypto price (USD) from CoinGecko. Falls back to random price if API fails."""
    try:
        coin_id = COIN_MAP.get(symbol.upper())
        if not coin_id:
            raise ValueError("Symbol not mapped")
        data = cg.get_price(ids=coin_id, vs_currencies='usd')
        return float(data[coin_id]['usd'])
    except Exception as e:
        # avoid spamming too many warnings, show once
        st.warning(f"Live price fetch failed for {symbol}: {e}")
        return round(random.uniform(100, 30000), 2)

def normalize_trades_to_df(trades_list):
    """
    Build a clean DataFrame from session_state.trades (which might contain inconsistent dicts/series/dataframes).
    This function:
      - converts each item to a dict row
      - normalizes column names (strip + lower)
      - renames common variants (e.g. 'price (usd)' -> 'price')
      - coalesces duplicate column names by taking the first non-null value across duplicates
    """
    # convert all items to dict rows
    rows = []
    for item in trades_list:
        if isinstance(item, dict):
            rows.append(item)
        elif isinstance(item, pd.Series):
            rows.append(item.to_dict())
        elif isinstance(item, pd.DataFrame):
            # flatten dataframe rows into rows
            for _, r in item.iterrows():
                rows.append(r.to_dict())
        else:
            try:
                rows.append(dict(item))
            except Exception:
                # skip unknown types
                continue

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # normalize headers (strip, lower)
    df.columns = df.columns.astype(str).str.strip().str.lower()

    # rename known variants to canonical names
    rename_map = {
        "price (usd)": "price",
        "price (inr)": "price",
        "price_usd": "price",
        "price_usdt": "price",
        "total (usd)": "total",
        "total (inr)": "total",
        "quantity": "quantity",
        "qty": "quantity",
        "time": "time",
        "symbol": "symbol",
        "action": "action",
        # keep other names as-is
    }
    df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})

    # If duplicate column names now exist after renaming, coalesce them:
    # Use groupby on column names (axis=1) and take first non-null across duplicates.
    if df.columns.duplicated().any():
        df = df.groupby(level=0, axis=1).first()

    # Ensure canonical columns exist (optional)
    # We won't force columns, but lower-case consistent column names are returned.
    return df

def calculate_trade_pnl(trades_df: pd.DataFrame):
    """Calculate per-trade P/L using live price for each symbol."""
    rows = []
    for _, t in trades_df.iterrows():
        sym = str(t.get("symbol", "")).upper()
        try:
            qty = float(t.get("quantity", 0))
        except Exception:
            qty = 0.0
        try:
            price = float(t.get("price", 0))
        except Exception:
            price = 0.0
        action = str(t.get("action", "")).lower()

        live_price = get_live_price(sym)
        pl = 0.0
        if action == "buy":
            pl = (live_price - price) * qty
        elif action == "sell":
            # For sells we treat it as realized/short style: positive if sold high then live lower
            pl = (price - live_price) * qty

        rows.append({
            "Symbol": sym,
            "Action": action.capitalize(),
            "Quantity": qty,
            "Trade Price ($)": price,
            "Live Price ($)": round(live_price, 2),
            "Trade P/L ($)": round(pl, 2)
        })
    return pd.DataFrame(rows)

def main():
    st.title("💼 Live Portfolio Dashboard ")
    st.write("Track your **Paper Trading** trades, holdings, and live **Profit & Loss** (P/L).")

    # --- session init ---
    if "balance" not in st.session_state:
        st.session_state.balance = 10000.0
    if "trades" not in st.session_state:
        st.session_state.trades = []
    if "positions" not in st.session_state:
        st.session_state.positions = {}

    cash_balance = st.session_state.balance
    trades_raw = st.session_state.trades

    st.metric("💵 Cash Balance", f"${cash_balance:,.2f}")

    if not trades_raw:
        st.info("🚀 No trades yet. Use Paper Trading page to place trades.")
        return

    # Normalize trades into a clean DataFrame
    df = normalize_trades_to_df(trades_raw)

    # Final safety: ensure no duplicate column names remain
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]

    # Refresh button
    if st.button("🔄 Refresh Live P&L"):
        safe_rerun()

    st.subheader("📜 Trade History")
    # show df (use width='stretch' if your Streamlit version suggests)
    try:
        st.dataframe(df, width="stretch")
    except Exception:
        # fallback
        st.dataframe(df)

    # Per-trade P&L
    st.subheader("💡 Per-Trade Live P&L")
    trade_pl_df = calculate_trade_pnl(df)
    def color_pl(val):
        return 'color: green;' if val > 0 else 'color: red;' if val < 0 else ''
    try:
        st.dataframe(trade_pl_df.style.map(color_pl, subset=["Trade P/L ($)"]), width="stretch")
    except Exception:
        st.dataframe(trade_pl_df)

    # Holdings calculation (supports short-selling: negative qty)
    st.subheader("📊 Current Holdings & Total P&L")
    holdings = {}
    for _, t in df.iterrows():
        sym = str(t.get("symbol", "")).upper()
        try:
            qty = float(t.get("quantity", 0))
        except Exception:
            qty = 0.0
        try:
            price = float(t.get("price", 0))
        except Exception:
            price = 0.0
        action = str(t.get("action", "")).lower()

        if sym == "":
            continue

        if sym not in holdings:
            holdings[sym] = {"qty": 0.0, "total_cost": 0.0, "realized_pl": 0.0}

        if action == "buy":
            holdings[sym]["qty"] += qty
            holdings[sym]["total_cost"] += qty * price
        elif action == "sell":
            # allow selling even if qty is zero (short-selling)
            sell_qty = qty
            if holdings[sym]["qty"] != 0:
                avg_price = holdings[sym]["total_cost"] / holdings[sym]["qty"] if holdings[sym]["qty"] != 0 else price
            else:
                avg_price = price
            pnl = (price - avg_price) * sell_qty
            holdings[sym]["realized_pl"] += pnl
            holdings[sym]["qty"] -= sell_qty
            holdings[sym]["total_cost"] -= avg_price * sell_qty
            # if negative qty, set total_cost relative to short
            if holdings[sym]["qty"] < 0:
                holdings[sym]["total_cost"] = abs(holdings[sym]["qty"]) * price

    rows = []
    total_value = cash_balance
    total_pl = 0.0
    for sym, data in holdings.items():
        live_price = get_live_price(sym)
        avg_buy = (data["total_cost"] / abs(data["qty"])) if abs(data["qty"]) > 0 else 0
        market_value = live_price * data["qty"]
        unrealized_pl = (live_price - avg_buy) * data["qty"]
        net_pl = unrealized_pl + data["realized_pl"]

        total_value += market_value
        total_pl += net_pl

        rows.append({
            "Symbol": sym,
            "Quantity": round(data["qty"], 6),
            "Avg Buy ($)": round(avg_buy, 4),
            "Live Price ($)": round(live_price, 2),
            "Investment ($)": round(data["total_cost"], 4),
            "Market Value ($)": round(market_value, 4),
            "Unrealized P/L ($)": round(unrealized_pl, 4),
            "Realized P/L ($)": round(data["realized_pl"], 4),
            "Total P/L ($)": round(net_pl, 4)
        })

    if rows:
        hold_df = pd.DataFrame(rows)
        try:
            st.dataframe(hold_df.style.map(color_pl, subset=[
                "Unrealized P/L ($)", "Realized P/L ($)", "Total P/L ($)"
            ]), width="stretch")
        except Exception:
            st.dataframe(hold_df)

        st.metric("💰 Total Portfolio Value", f"${total_value:,.2f}")
        st.metric("📈 Total Profit/Loss", f"${total_pl:,.2f}")

        # Book profit per symbol
        for sym, data in holdings.items():
            if abs(data["qty"]) <= 1e-12:
                continue
            if st.button(f"💰 Book Profit for {sym}"):
                # Append a consistent, canonical trade entry
                booked_qty = abs(data["qty"])
                booked_price = get_live_price(sym)
                st.session_state.trades.append({
                    "time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "symbol": sym,
                    "action": "sell" if data["qty"] >= 0 else "buy",
                    "quantity": booked_qty,
                    "price": booked_price,
                    "total": booked_qty * booked_price
                })
                st.success(f"✅ Profit booked for {sym}")
                safe_rerun()

        # Book all profits button
        if st.button("💵 Book All Profits"):
            realized = 0.0
            for sym, data in holdings.items():
                if abs(data["qty"]) > 1e-8:
                    live_price = get_live_price(sym)
                    avg = data["total_cost"] / abs(data["qty"]) if abs(data["qty"]) > 0 else 0
                    pnl = (live_price - avg) * data["qty"]
                    realized += pnl

                    # append canonical sell/buy for each coin (to mark realized)
                    st.session_state.trades.append({
                        "time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "symbol": sym,
                        "action": "sell" if data["qty"] >= 0 else "buy",
                        "quantity": abs(data["qty"]),
                        "price": live_price,
                        "total": abs(data["qty"]) * live_price
                    })

            # update cash balance with realized profit (we add net difference)
            st.session_state.balance += realized
            st.success(f"✅ All profits booked! Realized P&L: ${realized:,.2f}")
            safe_rerun()
    else:
        st.info("No open positions.")

if __name__ == "__main__":
    main()
