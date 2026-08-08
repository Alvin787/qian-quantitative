from fastapi import FastAPI
from dotenv import load_dotenv
import uvicorn
from backend.utils.data import get_data, get_sentiment
from backend.utils.indicators import calculate_indicators
from backend.utils.scoring import evaluate_signals, classify_signal
from backend.utils.youtubeSentiment import YouTubeSentimentAnalyzer
from backend.screener.router import router as hybrid_screener_router
import pandas as pd

load_dotenv()

app = FastAPI()
app.include_router(hybrid_screener_router)

@app.get("/analyze/{ticker}")
async def analyze(ticker: str):
    try:
        df = get_data(ticker)
        df, weekly_sma = calculate_indicators(df)
        sentiment_score = get_sentiment(ticker)
        score, signals = evaluate_signals(df, weekly_sma, sentiment_score)
        classification = classify_signal(score)
        latest = df.iloc[-1]
        
        # Get all the technical indicators from the latest row
        indicators = {
            "RSI": round(latest['RSI'], 2) if not pd.isna(latest['RSI']) else None,
            "Stochastic_K": round(latest['slowk'], 2) if not pd.isna(latest['slowk']) else None,
            "Stochastic_D": round(latest['slowd'], 2) if not pd.isna(latest['slowd']) else None,
            "MACD": round(latest['MACD'], 2) if not pd.isna(latest['MACD']) else None,
            "MACD_Signal": round(latest['MACD_signal'], 2) if not pd.isna(latest['MACD_signal']) else None,
            "MACD_Hist": round(latest['MACD_hist'], 2) if not pd.isna(latest['MACD_hist']) else None,
            "EMA9": round(latest['EMA9'], 2) if not pd.isna(latest['EMA9']) else None,
            "EMA20": round(latest['EMA20'], 2) if not pd.isna(latest['EMA20']) else None,
            "SMA50": round(latest['SMA50'], 2) if not pd.isna(latest['SMA50']) else None,
            "BB_Middle": round(latest['BB_middle'], 2) if not pd.isna(latest['BB_middle']) else None,
            "BB_Upper": round(latest['BB_upper'], 2) if not pd.isna(latest['BB_upper']) else None,
            "BB_Lower": round(latest['BB_lower'], 2) if not pd.isna(latest['BB_lower']) else None,
            "OBV": round(latest['OBV'], 2) if not pd.isna(latest['OBV']) else None,
            "ADX": round(latest['ADX'], 2) if not pd.isna(latest['ADX']) else None,
            "ATR": round(latest['ATR'], 2) if not pd.isna(latest['ATR']) else None,
            "Volume": round(latest['Volume'], 2) if not pd.isna(latest['Volume']) else None,
            "Avg_Volume_20": round(latest['avg_volume_20'], 2) if not pd.isna(latest['avg_volume_20']) else None,
            "52_Week_Low": round(latest['52_week_low'], 2) if not pd.isna(latest['52_week_low']) else None,
            "Tenkan_Sen": round(latest['tenkan_sen'], 2) if not pd.isna(latest['tenkan_sen']) else None,
            "Kijun_Sen": round(latest['kijun_sen'], 2) if not pd.isna(latest['kijun_sen']) else None,
            "Senkou_Span_A": round(latest['senkou_span_a'], 2) if not pd.isna(latest['senkou_span_a']) else None,
            "Senkou_Span_B": round(latest['senkou_span_b'], 2) if not pd.isna(latest['senkou_span_b']) else None,
            "MFI": round(latest['MFI'], 2) if not pd.isna(latest['MFI']) else None,
            "SuperTrend": round(latest['supertrend'], 2) if not pd.isna(latest['supertrend']) else None,
        }

        result = {
            "ticker": ticker,
            "score": round(score, 2),
            "classification": classification,
            "signals": signals,
            "entry_price": latest['Close'],
            "stop_loss": round(latest['Close'] - 2 * latest['ATR'], 2),
            "take_profit": round(latest['Close'] * 1.3, 2),
            "indicators": indicators
        }
        return result
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/youtube-sentiment")
async def youtube_sentiment():
    try:
        analyzer = YouTubeSentimentAnalyzer()
        results = analyzer.process_latest_livestream()
        
        if not results:
            return {"error": "Failed to process livestream"}
            
        return {
            "video_info": results["video_info"],
            "analysis": results["analysis"],
            "results_path": results["results_path"]
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)