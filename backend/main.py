from fastapi import FastAPI
import uvicorn
from utils.data import get_data, get_sentiment
from utils.indicators import calculate_indicators
from utils.scoring import evaluate_signals, classify_signal

app = FastAPI()

@app.get("/analyze/{ticker}")
async def analyze(ticker: str):
    try:
        df = get_data(ticker)
        df, weekly_sma = calculate_indicators(df)
        sentiment_score = get_sentiment(ticker)
        score, signals = evaluate_signals(df, weekly_sma, sentiment_score)
        classification = classify_signal(score)
        latest = df.iloc[-1]
        result = {
            "ticker": ticker,
            "score": round(score, 2),
            "classification": classification,
            "signals": signals,
            "entry_price": latest['Close'],
            "stop_loss": round(latest['Close'] - 2 * latest['ATR'], 2),
            "take_profit": round(latest['Close'] * 1.3, 2)
        }
        return result
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)