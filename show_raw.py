# show_raw.py
from db import SessionLocal
from models import RawPrice

db = SessionLocal()
for row in db.query(RawPrice).order_by(RawPrice.id):
    print(f"{row.id}\t{row.symbol}\t{row.price}\t{row.timestamp}")
db.close()