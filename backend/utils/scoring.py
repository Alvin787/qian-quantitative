import talib

def evaluate_signals(df, weekly_sma, sentiment_score):
    signals = {}
    raw_score = 0
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else latest

    # Define raw weights for each rule (in %)
    weights = {
        'RSI_positive': 10,
        'RSI_overbought': 10,
        'Stochastic_positive': 8,
        'Stochastic_negative': 5,
        'MACD_positive': 12,
        'MACD_negative': 10,
        'MovingAverages_positive': 8,
        'MovingAverages_negative': 8,
        'Bollinger_positive': 8,
        'Bollinger_negative': 5,
        'SupportBounce_positive': 8,
        'SupportBounce_negative': 8,
        'Volume_positive': 10,
        'Volume_negative': 5,
        'OBV_positive': 8,
        'OBV_negative': 5,
        'Candlestick_positive': 5,
        'Candlestick_negative': 5,
        'ADX_positive': 5,
        'ADX_negative': 5,
        'SwingLow_positive': 5,
        'SwingLow_negative': 5,
        'Ichimoku_positive': 10,
        'MFI_positive': 10,
        'MFI_negative': 10,
        'WeeklyMA_positive': 5,
        'SuperTrend_positive': 5,
        'Sentiment_positive': 5,
        'Sentiment_negative': 5
    }
    
    # Calculate maximum possible positive raw score for scaling
    positive_rules = ['RSI_positive', 'Stochastic_positive', 'MACD_positive', 'MovingAverages_positive',
                      'Bollinger_positive', 'SupportBounce_positive', 'Volume_positive', 'OBV_positive',
                      'Candlestick_positive', 'ADX_positive', 'SwingLow_positive', 'Ichimoku_positive',
                      'MFI_positive', 'WeeklyMA_positive', 'SuperTrend_positive', 'Sentiment_positive']
    max_positive_raw = sum(weights[r] for r in positive_rules)
    scale = 100 / max_positive_raw

    # 1. RSI Condition:
    recent_rsi = df['RSI'].iloc[-3:]
    if recent_rsi.isnull().any():
        signals['RSI'] = "Insufficient data"
    else:
        if (recent_rsi <= 30).all() and (recent_rsi.iloc[-1] > recent_rsi.iloc[-2]):
            add = weights['RSI_positive'] * scale
            raw_score += add
            signals['RSI'] = f"+{add:.1f}% (RSI low and rising)"
        elif latest['RSI'] > 70:
            sub = weights['RSI_overbought'] * scale
            raw_score -= sub
            signals['RSI'] = f"-{sub:.1f}% (RSI overbought)"
    
    # 2. Stochastic Oscillator:
    if (prev['slowk'] < prev['slowd']) and (latest['slowk'] > latest['slowd']) and (latest['slowk'] < 20):
        add = weights['Stochastic_positive'] * scale
        raw_score += add
        signals['Stochastic'] = f"+{add:.1f}% (Bullish stochastic crossover below 20)"
    elif (prev['slowk'] > prev['slowd']) and (latest['slowk'] < latest['slowd']) and (latest['slowk'] > 80):
        sub = weights['Stochastic_negative'] * scale
        raw_score -= sub
        signals['Stochastic'] = f"-{sub:.1f}% (Bearish stochastic crossover above 80)"
    
    # 3. MACD:
    if (prev['MACD'] < prev['MACD_signal']) and (latest['MACD'] > latest['MACD_signal']) and (abs(latest['MACD']) < 0.5) and (latest['MACD_hist'] > 0):
        add = weights['MACD_positive'] * scale
        raw_score += add
        signals['MACD'] = f"+{add:.1f}% (Bullish MACD crossover near zero)"
    elif (prev['MACD'] > prev['MACD_signal']) and (latest['MACD'] < latest['MACD_signal']) and (latest['MACD'] > 0):
        sub = weights['MACD_negative'] * scale
        raw_score -= sub
        signals['MACD'] = f"-{sub:.1f}% (Bearish MACD crossover above zero)"
    
    # 4. Moving Averages:
    if (prev['Close'] < prev['EMA20']) and (latest['Close'] > latest['EMA20']) and (latest['EMA9'] > latest['EMA20']) and (latest['Close'] > latest['SMA50']):
        add = weights['MovingAverages_positive'] * scale
        raw_score += add
        signals['Moving Averages'] = f"+{add:.1f}% (Price crossed above EMA20, with EMA9 > EMA20 and price > SMA50)"
    elif latest['Close'] < latest['SMA50']:
        sub = weights['MovingAverages_negative'] * scale
        raw_score -= sub
        signals['Moving Averages'] = f"-{sub:.1f}% (Price below SMA50)"
    
    # 5. Bollinger Bands:
    if (prev['Close'] < prev['BB_lower']) and (latest['Close'] > latest['BB_lower']) and (latest['Close'] < latest['BB_middle']):
        add = weights['Bollinger_positive'] * scale
        raw_score += add
        signals['Bollinger Bands'] = f"+{add:.1f}% (Price rebounding from lower Bollinger Band)"
    elif (prev['Close'] > prev['BB_upper']) and (latest['Close'] < latest['BB_upper']):
        sub = weights['Bollinger_negative'] * scale
        raw_score -= sub
        signals['Bollinger Bands'] = f"-{sub:.1f}% (Price falling from upper Bollinger Band)"
    
    # 6. Support Level Bounce:
    if ((prev['Close'] <= prev['SMA50']) or (prev['Close'] <= prev['52_week_low'] * 1.05)) and (latest['Close'] > latest['SMA50']):
        add = weights['SupportBounce_positive'] * scale
        raw_score += add
        signals['Support Bounce'] = f"+{add:.1f}% (Price bounced from support level)"
    elif (prev['Close'] >= prev['SMA50']) and (latest['Close'] < latest['SMA50']):
        sub = weights['SupportBounce_negative'] * scale
        raw_score -= sub
        signals['Support Bounce'] = f"-{sub:.1f}% (Price broke support level)"
    
    # 7. Volume Spike:
    if (latest['Volume'] >= 2 * latest['avg_volume_20']) and (latest['Close'] > prev['Close']):
        add = weights['Volume_positive'] * scale
        raw_score += add
        signals['Volume'] = f"+{add:.1f}% (Volume spike on rebound)"
    elif (latest['Volume'] < latest['avg_volume_20']) and (latest['Close'] > prev['Close']):
        sub = weights['Volume_negative'] * scale
        raw_score -= sub
        signals['Volume'] = f"-{sub:.1f}% (Volume below average on breakout)"
    
    # 8. On-Balance Volume (OBV):
    if (latest['OBV'] > prev['OBV']) and (latest['Close'] > prev['Close']):
        add = weights['OBV_positive'] * scale
        raw_score += add
        signals['OBV'] = f"+{add:.1f}% (OBV rising with price)"
    elif (latest['OBV'] < prev['OBV']) and (latest['Close'] > prev['Close']):
        sub = weights['OBV_negative'] * scale
        raw_score -= sub
        signals['OBV'] = f"-{sub:.1f}% (Divergence: OBV falling while price rising)"
    
    # 9. Candlestick Pattern:
    hammer = talib.CDLHAMMER(df['Open'], df['High'], df['Low'], df['Close'])
    engulfing = talib.CDLENGULFING(df['Open'], df['High'], df['Low'], df['Close'])
    if hammer.iloc[-1] > 0 or engulfing.iloc[-1] > 0:
        add = weights['Candlestick_positive'] * scale
        raw_score += add
        signals['Candlestick'] = f"+{add:.1f}% (Bullish candlestick pattern)"
    shooting_star = talib.CDLSHOOTINGSTAR(df['Open'], df['High'], df['Low'], df['Close'])
    if shooting_star.iloc[-1] < 0:
        sub = weights['Candlestick_negative'] * scale
        raw_score -= sub
        signals['Candlestick'] = f"-{sub:.1f}% (Bearish candlestick pattern)"
    
    # 10. ADX:
    if latest['ADX'] > 20:
        add = weights['ADX_positive'] * scale
        raw_score += add
        signals['ADX'] = f"+{add:.1f}% (ADX indicates a strong trend)"
    else:
        sub = weights['ADX_negative'] * scale
        raw_score -= sub
        signals['ADX'] = f"-{sub:.1f}% (ADX indicates a weak trend)"
    
    # 11. Swing Low Bounce:
    if len(df) > 6:
        recent_lows = df['Low'].iloc[-7:-1]
        swing_low = recent_lows.min()
        if abs(prev['Low'] - swing_low) / swing_low < 0.01:
            if latest['Close'] > prev['Low']:
                add = weights['SwingLow_positive'] * scale
                raw_score += add
                signals['Swing Low'] = f"+{add:.1f}% (Price bounced from recent swing low)"
            elif latest['Close'] < prev['Low']:
                sub = weights['SwingLow_negative'] * scale
                raw_score -= sub
                signals['Swing Low'] = f"-{sub:.1f}% (Price broke recent swing low)"
    
    # 12. Ichimoku Cloud:
    if (latest['Close'] > latest['senkou_span_a']) and (latest['Close'] > latest['senkou_span_b']):
        add = weights['Ichimoku_positive'] * scale
        raw_score += add
        signals['Ichimoku'] = f"+{add:.1f}% (Price above Ichimoku cloud)"
    
    # 13. MFI:
    if latest['MFI'] < 20 and latest['MFI'] > prev['MFI']:
        add = weights['MFI_positive'] * scale
        raw_score += add
        signals['MFI'] = f"+{add:.1f}% (MFI oversold and rising)"
    elif latest['MFI'] > 80:
        sub = weights['MFI_negative'] * scale
        raw_score -= sub
        signals['MFI'] = f"-{sub:.1f}% (MFI overbought)"
    
    # 14. Weekly SMA (Multi-timeframe confirmation):
    if latest['Close'] > weekly_sma:
        add = weights['WeeklyMA_positive'] * scale
        raw_score += add
        signals['Weekly SMA'] = f"+{add:.1f}% (Price above weekly SMA)"
    
    # 15. SuperTrend:
    if latest['Close'] > latest['supertrend']:
        add = weights['SuperTrend_positive'] * scale
        raw_score += add
        signals['SuperTrend'] = f"+{add:.1f}% (Price above SuperTrend)"
    
    # 16. Sentiment:
    if sentiment_score > 0.1:
        add = weights['Sentiment_positive'] * scale
        raw_score += add
        signals['Sentiment'] = f"+{add:.1f}% (Positive news sentiment)"
    elif sentiment_score < -0.1:
        sub = weights['Sentiment_negative'] * scale
        raw_score -= sub
        signals['Sentiment'] = f"-{sub:.1f}% (Negative news sentiment)"
    
    return raw_score, signals

def classify_signal(score):
    if score >= 60:
        return "Strong Buy"
    elif score >= 40:
        return "Moderate Buy"
    elif score >= 20:
        return "Neutral"
    else:
        return "Avoid/Sell"