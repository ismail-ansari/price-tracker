import json
from kafka import KafkaConsumer
from datetime import datetime
from sqlalchemy import desc

from db import SessionLocal, engine, Base
from models import RawPrice, MovingAverage

# Ensure the moving_averages table exists
Base.metadata.create_all(bind=engine)

# Kafka consumer setup
consumer = KafkaConsumer(
    "price-events",
    bootstrap_servers=["localhost:9092"],
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id="ma-calc-group",
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
)

WINDOW = 5

def compute_and_store(symbol: str, price_list: list[float]):
    db = SessionLocal()
    try:
        # Compute the moving average
        ma = sum(price_list) / WINDOW

        # Upsert into moving_averages
        row = (
            db.query(MovingAverage)
              .filter(
                  MovingAverage.symbol == symbol,
                  MovingAverage.window_size == WINDOW
             )
              .first()
        )
        if row:
            row.moving_average = ma
            row.calculated_at  = datetime.utcnow()
        else:
            row = MovingAverage(
                symbol=symbol,
                window_size=WINDOW,
                moving_average=ma,
                calculated_at=datetime.utcnow(),
            )
            db.add(row)
        db.commit()
    finally:
        db.close()

print("🔊 Moving-average consumer listening on ‘price-events’…")
for msg in consumer:
    data = msg.value
    symbol = data["symbol"]
    # Fetch latest WINDOW raw prices for this symbol
    db = SessionLocal()
    try:
        recent = (
            db.query(RawPrice.price)
              .filter(RawPrice.symbol == symbol)
              .order_by(desc(RawPrice.id))
              .limit(WINDOW)
              .all()
        )
    finally:
        db.close()

    prices = [p[0] for p in recent]
    if len(prices) == WINDOW:
        compute_and_store(symbol, prices)