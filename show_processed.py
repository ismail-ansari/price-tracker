# show_processed.py
from db import SessionLocal
from models import ProcessedPrice

db = SessionLocal()
for row in db.query(ProcessedPrice).order_by(ProcessedPrice.id):
    print(row.__dict__)
db.close()