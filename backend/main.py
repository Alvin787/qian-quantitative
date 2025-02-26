import yfinance as yf
import talib
import pandas as pd
import numpy as np
from fastapi import FastAPI
import uvicorn

app = FastAPI()

def get_data(ticker):
    # Fetch one year of historical data to cover both recent (60-day) and 52-week indicators.
    df = yf.Ticker(ticker).history(period="1y")
    if df.empty:
        raise Exception("No data found for ticker")
    return df

def calculate_indicators(df):
    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']
    
    # RSI (14-day)
    df['RSI'] = talib.RSI(close, timeperiod=14)
    
    # Stochastic Oscillator: slow %K and slow %D (14-day, 3-day smoothing)
    slowk, slowd = talib.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowd_period=3)
    df['slowk'] = slowk
    df['slowd'] = slowd
    
    # MACD: MACD line, signal line, and histogram
    macd, macdsignal, macdhist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
    df['MACD'] = macd
    df['MACD_signal'] = macdsignal
    df['MACD_hist'] = macdhist
    
    # Moving Averages: 9-day EMA, 20-day EMA, and 50-day SMA
    df['EMA9'] = talib.EMA(close, timeperiod=9)
    df['EMA20'] = talib.EMA(close, timeperiod=20)
    df['SMA50'] = talib.SMA(close, timeperiod=50)
    
    # Bollinger Bands: 20-day moving average and bands at ±2 standard deviations
    middle, upper, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    df['BB_middle'] = middle
    df['BB_upper'] = upper
    df['BB_lower'] = lower
    
    # On-Balance Volume (OBV)
    df['OBV'] = talib.OBV(close, volume)
    
    # ADX (14-day)
    df['ADX'] = talib.ADX(high, low, close, timeperiod=14)
    
    # ATR (14-day)
    df['ATR'] = talib.ATR(high, low, close, timeperiod=14)
    
    # 20-day average volume
    df['avg_volume_20'] = volume.rolling(window=20).mean()
    
    # 52-week low (using approx. 252 trading days)
    df['52_week_low'] = df['Low'].rolling(window=252, min_periods=1).min()
    
    return df

def evaluate_signals(df):
    signals = {}
    score = 0
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else latest

    # 1. RSI Condition:
    recent_rsi = df['RSI'].iloc[-3:]
    if recent_rsi.isnull().any():
        signals['RSI'] = "Insufficient data"
    else:
        # If RSI <= 30 for last 3 days and rising today
        if (recent_rsi <= 30).all() and (recent_rsi.iloc[-1] > recent_rsi.iloc[-2]):
            score += 15
            signals['RSI'] = "+15 (RSI low and rising)"
        # If RSI is overbought (>70)
        elif latest['RSI'] > 70:
            score -= 10
            signals['RSI'] = "-10 (RSI overbought)"
    
    # 2. Stochastic Oscillator:
    if (prev['slowk'] < prev['slowd']) and (latest['slowk'] > latest['slowd']) and (latest['slowk'] < 20):
        score += 10
        signals['Stochastic'] = "+10 (Bullish stochastic crossover below 20)"
    elif (prev['slowk'] > prev['slowd']) and (latest['slowk'] < latest['slowd']) and (latest['slowk'] > 80):
        score -= 5
        signals['Stochastic'] = "-5 (Bearish stochastic crossover above 80)"
    
    # 3. MACD:
    if (prev['MACD'] < prev['MACD_signal']) and (latest['MACD'] > latest['MACD_signal']) \
       and (abs(latest['MACD']) < 0.5) and (latest['MACD_hist'] > 0):
        score += 15
        signals['MACD'] = "+15 (Bullish MACD crossover near zero)"
    elif (prev['MACD'] > prev['MACD_signal']) and (latest['MACD'] < latest['MACD_signal']) \
         and (latest['MACD'] > 0):
        score -= 10
        signals['MACD'] = "-10 (Bearish MACD crossover above zero)"
    
    # 4. Moving Averages:
    if (prev['Close'] < prev['EMA20']) and (latest['Close'] > latest['EMA20']) \
       and (latest['EMA9'] > latest['EMA20']) and (latest['Close'] > latest['SMA50']):
        score += 10
        signals['Moving Averages'] = "+10 (Price crossed above EMA20, EMA9 > EMA20, and price > SMA50)"
    elif latest['Close'] < latest['SMA50']:
        score -= 10
        signals['Moving Averages'] = "-10 (Price below SMA50)"
    
    # 5. Bollinger Bands:
    if (prev['Close'] < prev['BB_lower']) and (latest['Close'] > latest['BB_lower']) and (latest['Close'] < latest['BB_middle']):
        score += 10
        signals['Bollinger Bands'] = "+10 (Price rebounding from lower Bollinger Band)"
    elif (prev['Close'] > prev['BB_upper']) and (latest['Close'] < latest['BB_upper']):
        score -= 5
        signals['Bollinger Bands'] = "-5 (Price falling from upper Bollinger Band)"
    
    # 6. Support Level Bounce:
    # Check if previous close was at or near support (SMA50 or near 52-week low) and now above SMA50.
    if (prev['Close'] <= prev['SMA50'] or prev['Close'] <= prev['52_week_low'] * 1.05) and (latest['Close'] > latest['SMA50']):
        score += 10
        signals['Support Bounce'] = "+10 (Price bounced from support level)"
    elif (prev['Close'] >= prev['SMA50']) and (latest['Close'] < latest['SMA50']):
        score -= 10
        signals['Support Bounce'] = "-10 (Price broke support level)"
    
    # 7. Volume Spike:
    if (latest['Volume'] >= 2 * latest['avg_volume_20']) and (latest['Close'] > prev['Close']):
        score += 15
        signals['Volume'] = "+15 (Volume spike on rebound)"
    elif (latest['Volume'] < latest['avg_volume_20']) and (latest['Close'] > prev['Close']):
        score -= 5
        signals['Volume'] = "-5 (Volume below average on breakout)"
    
    # 8. On-Balance Volume (OBV):
    if (latest['OBV'] > prev['OBV']) and (latest['Close'] > prev['Close']):
        score += 10
        signals['OBV'] = "+10 (OBV rising with price)"
    elif (latest['OBV'] < prev['OBV']) and (latest['Close'] > prev['Close']):
        score -= 5
        signals['OBV'] = "-5 (Divergence: OBV falling while price rising)"
    
    # 9. Candlestick Pattern:
    # Check for bullish patterns: Hammer or Engulfing.
    hammer = talib.CDLHAMMER(df['Open'], df['High'], df['Low'], df['Close'])
    engulfing = talib.CDLENGULFING(df['Open'], df['High'], df['Low'], df['Close'])
    if hammer.iloc[-1] > 0 or engulfing.iloc[-1] > 0:
        score += 5
        signals['Candlestick'] = "+5 (Bullish candlestick pattern)"
    # Alternatively, check for bearish reversal (e.g., Shooting Star).
    shooting_star = talib.CDLSHOOTINGSTAR(df['Open'], df['High'], df['Low'], df['Close'])
    if shooting_star.iloc[-1] < 0:
        score -= 5
        signals['Candlestick'] = "-5 (Bearish candlestick pattern)"
    
    # 10. ADX:
    if latest['ADX'] > 20:
        score += 5
        signals['ADX'] = "+5 (ADX indicates a trend)"
    else:
        score -= 5
        signals['ADX'] = "-5 (ADX indicates a weak trend)"
    
    return score, signals

def classify_signal(score):
    if score >= 60:
        return "Strong Buy"
    elif score >= 40:
        return "Moderate Buy"
    elif score >= 20:
        return "Neutral"
    else:
        return "Avoid/Sell"

@app.get("/analyze/{ticker}")
async def analyze(ticker: str):
    try:
        df = get_data(ticker)
        df = calculate_indicators(df)
        score, signals = evaluate_signals(df)
        classification = classify_signal(score)
        latest = df.iloc[-1]
        result = {
            "ticker": ticker,
            "score": score,
            "classification": classification,
            "signals": signals,
            "entry_price": latest['Close']
        }
        return result
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)