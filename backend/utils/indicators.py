import talib
import pandas as pd
import numpy as np

def calculate_ichimoku(df):
    # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
    period9_high = df['High'].rolling(window=9).max()
    period9_low = df['Low'].rolling(window=9).min()
    df['tenkan_sen'] = (period9_high + period9_low) / 2
    
    # Kijun-sen (Base Line): (26-period high + 26-period low)/2
    period26_high = df['High'].rolling(window=26).max()
    period26_low = df['Low'].rolling(window=26).min()
    df['kijun_sen'] = (period26_high + period26_low) / 2
    
    # Senkou Span A: (tenkan_sen + kijun_sen)/2, shifted 26 periods ahead
    df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)
    
    # Senkou Span B: (52-period high + 52-period low)/2, shifted 26 periods ahead
    period52_high = df['High'].rolling(window=52).max()
    period52_low = df['Low'].rolling(window=52).min()
    df['senkou_span_b'] = ((period52_high + period52_low) / 2).shift(26)
    
    return df

def calculate_mfi(df):
    df['MFI'] = talib.MFI(df['High'], df['Low'], df['Close'], df['Volume'], timeperiod=14)
    return df

def calculate_weekly_sma(df):
    df_weekly = df['Close'].resample('W').mean()
    last_weekly_sma = df_weekly.iloc[-1]
    df['weekly_sma'] = last_weekly_sma
    return df, last_weekly_sma

def compute_supertrend(df, period=10, multiplier=3):
    atr = talib.ATR(df['High'], df['Low'], df['Close'], timeperiod=period)
    hl2 = (df['High'] + df['Low']) / 2
    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)
    
    final_upperband = upperband.copy()
    final_lowerband = lowerband.copy()
    supertrend = pd.Series(index=df.index)
    
    for i in range(1, len(df)):
        final_upperband.iloc[i] = (
            min(upperband.iloc[i], final_upperband.iloc[i-1])
            if df['Close'].iloc[i-1] <= final_upperband.iloc[i-1] 
            else upperband.iloc[i]
        )
        final_lowerband.iloc[i] = (
            max(lowerband.iloc[i], final_lowerband.iloc[i-1])
            if df['Close'].iloc[i-1] >= final_lowerband.iloc[i-1] 
            else lowerband.iloc[i]
        )
        if df['Close'].iloc[i] <= final_upperband.iloc[i]:
            supertrend.iloc[i] = final_upperband.iloc[i]
        else:
            supertrend.iloc[i] = final_lowerband.iloc[i]
    df['supertrend'] = supertrend
    return df

def calculate_indicators(df):
    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']
    
    # Standard indicators
    df['RSI'] = talib.RSI(close, timeperiod=14)
    slowk, slowd = talib.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowd_period=3)
    df['slowk'] = slowk
    df['slowd'] = slowd
    macd, macdsignal, macdhist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
    df['MACD'] = macd
    df['MACD_signal'] = macdsignal
    df['MACD_hist'] = macdhist
    df['EMA9'] = talib.EMA(close, timeperiod=9)
    df['EMA20'] = talib.EMA(close, timeperiod=20)
    df['SMA50'] = talib.SMA(close, timeperiod=50)
    middle, upper, lower_bb = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    df['BB_middle'] = middle
    df['BB_upper'] = upper
    df['BB_lower'] = lower_bb
    df['OBV'] = talib.OBV(close, volume)
    df['ADX'] = talib.ADX(high, low, close, timeperiod=14)
    df['ATR'] = talib.ATR(high, low, close, timeperiod=14)
    df['avg_volume_20'] = volume.rolling(window=20).mean()
    df['52_week_low'] = df['Low'].rolling(window=252, min_periods=1).min()
    
    # Additional indicators
    df = calculate_ichimoku(df)
    df = calculate_mfi(df)
    df, weekly_sma = calculate_weekly_sma(df)
    df = compute_supertrend(df, period=10, multiplier=3)
    
    return df, weekly_sma