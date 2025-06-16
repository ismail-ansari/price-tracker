from kafka import KafkaProducer
import json
from datetime import datetime
from typing import List, Dict

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
from models import JobConfig, RawPrice, MovingAverage

# Create the tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Price Tracker",
    description="Fetch latest stock prices via Yahoo Finance",
    version="0.1.0",
)

class PollRequest(BaseModel):
    symbols: List[str]
    interval: int
    provider: str

class PollResponse(BaseModel):
    job_id: str
    status: str
    config: Dict[str, object]

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

         
    return PriceResponse(
        symbol=symbol.upper(),
        price=round(float(latest_price), 2),
        timestamp=ts,
        provider=prov,
     )