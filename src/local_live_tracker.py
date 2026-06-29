import os
import json
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

PORTFOLIO_FILE = 'data/live_portfolio.json'
LOG_FILE = 'data/live_execution_log.csv'

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

def load_latest_sentiment_score(csv_path, lookback_days=10):
    if not os.path.exists(csv_path):
        return 0.0, 0.0
    try:
        signals = pd.read_csv(csv_path)
        signals['effective_market_time'] = pd.to_datetime(signals['effective_market_time'])
        daily = signals.sort_values('effective_market_time').groupby(signals['effective_market_time'].dt.date).last().reset_index()
        latest_score = daily['conviction_score'].iloc[-1]
        smoothed_neg = daily['conviction_score'].tail(lookback_days).mean()
        return latest_score, smoothed_neg
    except Exception:
        return 0.0, 0.0

def initialize_or_load_portfolio(initial_budget=100.00):
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, 'r') as f:
            return json.load(f)
    else:
        state = {
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_portfolio_value": initial_budget,
            "cash_balance": initial_budget,
            "tsla_shares_held": 0.0,
            "tsla_current_price": 0.0
        }
        with open(PORTFOLIO_FILE, 'w') as f:
            json.dump(state, f, indent=4)
        return state

def run_live_tracker_cycle():
    portfolio = initialize_or_load_portfolio(100.00)
    
    ticker = yf.Ticker("TSLA")
    hist = ticker.history(period="120d", interval="1d")
    if hist.empty:
        return
        
    current_price = float(hist['Close'].iloc[-1])
    hist['returns'] = hist['Close'].pct_change()
    hist['rsi_14'] = calculate_rsi(hist['Close'], 14)
    hist['vol_10d'] = hist['returns'].rolling(10).std()
    hist['vol_60d'] = hist['returns'].rolling(60).std()
    
    current_rsi = float(hist['rsi_14'].iloc[-1])
    vol_ratio = float(hist['vol_10d'].iloc[-1] / hist['vol_60d'].iloc[-1]) if hist['vol_60d'].iloc[-1] != 0 else 1.0
    vol_ratio = max(0.5, min(2.0, vol_ratio))
    
    current_equity_value = portfolio["tsla_shares_held"] * current_price
    total_portfolio_value = portfolio["cash_balance"] + current_equity_value
    
    conviction, smoothed_neg = load_latest_sentiment_score('data/quantpad_roberta_signals.csv')
    
    upside_mod = 0.5 if conviction >= 0.4 else (conviction * (0.5 / 0.4) if conviction > 0 else 0.0)
    downside_mod = max(-0.5, smoothed_neg * 0.5 * vol_ratio) if smoothed_neg < 0 else 0.0
    
    target_leverage = 1.0 + upside_mod + downside_mod
    if current_rsi <= 30:
        target_leverage = max(1.0, target_leverage)
    target_leverage = max(1.00, min(1.15, target_leverage))
    
    target_equity_value = total_portfolio_value * target_leverage
    target_shares = target_equity_value / current_price
    share_delta = target_shares - portfolio["tsla_shares_held"]
    
    trade_cost = abs(share_delta * current_price)
    slippage_fee = trade_cost * 0.0015 if share_delta != 0 else 0.0
    
    portfolio["tsla_shares_held"] = round(target_shares, 6)
    portfolio["cash_balance"] = round(total_portfolio_value - (target_shares * current_price) - slippage_fee, 2)
    portfolio["total_portfolio_value"] = round(portfolio["cash_balance"] + (portfolio["tsla_shares_held"] * current_price), 2)
    portfolio["tsla_current_price"] = round(current_price, 2)
    portfolio["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(PORTFOLIO_FILE, 'w') as f:
        json.dump(portfolio, f, indent=4)
        
    log_exists = os.path.exists(LOG_FILE)
    log_df = pd.DataFrame([{
        "Timestamp": portfolio["last_updated"],
        "TSLA_Price": current_price,
        "Target_Leverage": f"{target_leverage:.2f}x",
        "Shares_Held": portfolio["tsla_shares_held"],
        "Portfolio_Value_GBP": portfolio["total_portfolio_value"],
        "Trade_Adjustment": f"{share_delta:+.4f}"
    }])
    log_df.to_csv(LOG_FILE, mode='a', header=not log_exists, index=False)

if __name__ == "__main__":
    run_live_tracker_cycle()
