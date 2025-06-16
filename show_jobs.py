from db import SessionLocal
from models import JobConfig

db = SessionLocal()
for job in db.query(JobConfig).order_by(JobConfig.id):
    print(job.__dict__)
db.close()