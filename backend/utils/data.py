import yfinance as yf
import pandas as pd

def get_data(ticker):
    df = yf.Ticker(ticker).history(period="1y")
    if df.empty:
        raise Exception("No data found for ticker")
    df.index = pd.to_datetime(df.index)
    return df

def get_sentiment(ticker):
    # Dummy sentiment function.
    # For real implementation, integrate with a news/sentiment API.
    return 0.0