from fastapi import FastAPI
from dotenv import load_dotenv
import uvicorn
from backend.screener.router import router as screener_router
from backend.diary.router import router as diary_router
from backend.positions.router import router as positions_router
from backend.watchlists.router import router as watchlists_router
from backend.pnl.router import router as pnl_router

load_dotenv()

app = FastAPI()
app.include_router(screener_router)
app.include_router(diary_router)
app.include_router(positions_router)
app.include_router(watchlists_router)
app.include_router(pnl_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
