from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yfinance as yf

# make sure this is literally `app`
app = FastAPI(
    title="Price Tracker",
    description="Fetch latest stock prices via Yahoo Finance",
    version="0.1.0",
)

class PriceResponse(BaseModel):
    symbol: str
    price: float

@app.get("/prices/latest", response_model=PriceResponse)
async def get_latest_price(symbol: str):
    """Fetch the latest market price for a given ticker symbol."""
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d", interval="1m")
    if data.empty:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")
    latest_price = data["Close"].iloc[-1]
    return PriceResponse(symbol=symbol.upper(), price=round(float(latest_price), 2))