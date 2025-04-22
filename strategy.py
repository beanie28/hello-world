# strategy.py
import yfinance as yf
import pandas as pd
import numpy as np
from ta.trend import CCIIndicator
import requests
import os

# Load from GitHub Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})

def arnold_legaux_ma(series, short=5, long=35):
    return (series.rolling(window=short).mean() + series.rolling(window=long).mean()) / 2

def fetch_weekly_data(symbol, period="1y"):
    data = yf.download(symbol, interval="1wk", period=period)
    return data

def apply_strategy(data):
    cci = CCIIndicator(data['High'], data['Low'], data['Close'], window=20).cci()
    alma = arnold_legaux_ma(data['Close'])

    data['CCI'] = cci
    data['ALMA'] = alma
    data['Signal'] = (cci > 100) & (data['Close'] > alma)
    return data

def backtest(data):
    data['Position'] = data['Signal'].shift(1).fillna(False)
    data['Returns'] = data['Close'].pct_change()
    data['Strategy'] = data['Position'] * data['Returns']
    return data['Strategy'].cumsum().iloc[-1]

def main():
    stock_list = ['AAPL', 'MSFT', 'GOOGL']  # Add more tickers here
    passing = []

    for stock in stock_list:
        df = fetch_weekly_data(stock)
        df = apply_strategy(df)
        performance = backtest(df)

        if df['Signal'].iloc[-1]:
            msg = f"{stock} passed the strategy. Backtest return: {performance:.2%}"
            send_telegram_message(msg)
            passing.append(stock)

    if not passing:
        send_telegram_message("No stocks passed the strategy this week.")

if __name__ == "__main__":
    main()