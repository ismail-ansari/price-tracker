from kafka import KafkaProducer
import json
from datetime import datetime

#Kafka producer setup
producer = KafkaProducer(
    bootstrap_servers=["localhost:9092"],
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    retries=5,
)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yfinance as yf

from db   import engine, Base, SessionLocal
import models
from models import RawPrice

# Create the tables
Base.metadata.create_all(bind=engine)

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
#db persistence block
    db = SessionLocal()#open a database session
    try:
         raw = RawPrice(symbol=symbol.upper(), price=float(latest_price))
         db.add(raw)
         db.commit()
    finally:
         db.close()
#publish event to Kafka
    try:
        event = {
         "symbol":   symbol.upper(),
          "price":    float(latest_price),
          "timestamp": datetime.utcnow().isoformat(),
    }
        producer.send("price-events", event)
        producer.flush()
    except Exception as e:
         print(f"[Kafka publish error] {e}")

         
    return PriceResponse(symbol=symbol.upper(), price=round(float(latest_price), 2))