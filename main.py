from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
import json
import yfinance as yf
from kafka import KafkaProducer

from db import engine, Base, SessionLocal
from models import RawPrice, ProcessedPrice, JobConfig

#Create all tables
Base.metadata.create_all(bind=engine)

#Kafka producer setup
producer = KafkaProducer(
    bootstrap_servers=["localhost:9092"],
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    retries=5,
)

#FastAPI app
app = FastAPI(
    title="Price Tracker",
    description="Fetch latest stock prices via Yahoo Finance",
    version="0.1.0",
)

#Pydantic Schemas
class PriceResponse(BaseModel):
    symbol: str
    price: float
    timestamp: str
    provider: str

class PollRequest(BaseModel):
    symbols: List[str]
    interval: int
    provider: str

class PollResponse(BaseModel):
    job_id: str
    status: str
    config: Dict[str, object]

#GET /prices/latest
@app.get("/prices/latest", response_model=PriceResponse)
async def get_latest_price(symbol: str):
    # Fetch the most recent daily close
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="2d", interval="1d")
    if data.empty:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found or no data")
    latest_price = data["Close"].iloc[-1]

    # Build metadata
    ts = datetime.utcnow().isoformat() + "Z"
    prov = "yahoo_finance"

    # Persist raw + processed price
    db = SessionLocal()
    try:
        raw = RawPrice(symbol=symbol.upper(), price=float(latest_price))
        db.add(raw)
        db.commit()
        db.refresh(raw)
        raw_id = raw.id

        proc = ProcessedPrice(
            symbol=symbol.upper(),
            price=float(latest_price),
            timestamp=datetime.utcnow(),
            source=prov,
            raw_response_id=raw_id,
        )
        db.add(proc)
        db.commit()
    finally:
        db.close()

    #Build enriched event
    event = {
        "symbol": symbol.upper(),
        "price": float(latest_price),
        "timestamp": ts,
        "source": prov,
        "raw_response_id": raw_id,
    }

    #Publish to Kafka
    try:
        producer.send("price-events", event)
        producer.flush()
        print(f"[DEBUG] Published to Kafka → {event}")
    except Exception as e:
        print(f"[Kafka publish error] {e}")

    #Return response
    return PriceResponse(
        symbol=symbol.upper(),
        price=round(float(latest_price), 2),
        timestamp=ts,
        provider=prov,
    )

#POST /prices/poll
@app.post("/prices/poll", status_code=202, response_model=PollResponse)
async def poll_prices(req: PollRequest):
    db = SessionLocal()
    try:
        job = JobConfig(
            symbols=req.symbols,
            interval=req.interval,
            provider=req.provider,
            status="accepted",
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return PollResponse(
            job_id=f"poll_{job.id}",
            status=job.status,
            config={"symbols": job.symbols, "interval": job.interval},
        )
    finally:
        db.close()