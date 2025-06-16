from sqlalchemy import Column, Integer, String, Float, DateTime, func, JSON
from db import Base

class RawPrice(Base):
    __tablename__ = "raw_prices"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    price = Column(Float)

class MovingAverage(Base):
    __tablename__ = "moving_averages"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    window_size = Column(Integer)
    moving_average = Column(Float)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

class JobConfig(Base):
    __tablename__ = "job_configs"
    id = Column(Integer, primary_key=True, index=True)
    symbols = Column(JSON, nullable=False)
    interval = Column(Integer, nullable=False)
    provider = Column(String, nullable=False)
    status = Column(String, default="accepted")
    created_at = Column(DateTime(timezone=True), server_default=func.now())