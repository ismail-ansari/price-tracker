# show_ma.py
from db import SessionLocal
from models import MovingAverage

db = SessionLocal()
for row in db.query(MovingAverage).order_by(MovingAverage.id):
    print(f"{row.id}\t{row.symbol}\t{row.window_size}\t{row.moving_average:.4f}\t{row.calculated_at}")
db.close()
