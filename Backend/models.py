#Import os, dotenv, and needed sqlalchemy 
import os
from dotenv import load_dotenv
from sqlalchemy import (Integer, Column, Text, SmallInteger, TIMESTAMP, ForeignKey, UniqueConstraint, text, create_engine)
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, UUID
from sqlalchemy.orm import DeclarativeBase, relationship
import sqlalchemy as sa

'''Use SQLAlchemy to do the following:
- enable TimescaleDB
- Create Static Tables
- Create Hyper Tables
'''
#Create Static Tables (stops, routes, trips, predictions, & alert_subscriptions)
class Base(DeclarativeBase):
    pass

class Stop(Base):
    __tablename__ = "stops"
    stop_id = Column(Text, primary_key=True)
    stop_name = Column(Text, nullable=False)
    lat = Column(DOUBLE_PRECISION)
    lon = Column(DOUBLE_PRECISION)

class Route(Base):
    __tablename__ = "routes"
    route_id = Column(Text, primary_key=True)
    short_name = Column(Text)
    long_name = Column(Text)
    route_type = Column(Integer)

    trip = relationship('Trip', back_populates='route')

class Trip(Base):
    __tablename__ = "trips"
    trip_id = Column(Text, primary_key=True)
    route_id = Column(Text, ForeignKey('routes.route_id'))
    service_id = Column(Text)
    headsign = Column(Text)

    route = relationship('Route', back_populates='trip')

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(Text, ForeignKey('routes.route_id'))
    hour_of_day = Column(SmallInteger, nullable=False)
    day_of_week = Column(Text, nullable=False)
    precip_bucket = Column(Text, nullable=False)
    prediction_delay = Column(Integer, nullable=False)
    p10 = Column(Integer, nullable=False)
    p90 = Column(Integer, nullable=False)
    model_version = Column(Text, nullable=False)
    generated_at = Column(TIMESTAMP(timezone=True), server_default=sa.func.now())

    __table_args__ = ( UniqueConstraint("route_id", "hour_of_day", "day_of_week", "precip_bucket", "model_version"), )

    route = relationship('Route')

class AlertSubscription(Base):
    __tablename__ = "alert_subscriptions"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    route_id = Column(Text, ForeignKey('routes.route_id'))
    email = Column(Text, nullable=False)
    threshold_min = Column(Integer, nullable=False, default=5)
    created_at = Column(TIMESTAMP(timezone=True), server_default=sa.func.now())

    route = relationship('Route')


#Create hypertables (vehicle_position & delay observations)
def init_hypertables(engine):
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaleDB"))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vehicle_positions (
                    id          BIGSERIAL,
                    trip_id     TEXT NOT NULL, 
                    route_id    TEXT,
                    lat         DOUBLE PRECISION,
                    lon         DOUBLE PRECISION,
                    delay_s     INTEGER,
                    recorded_at TIMESTAMPTZ NOT NULL, 
                    UNIQUE (trip_id, recorded_at)             
            )
        """))

        conn.execute(text("""
                SELECT create_hypertable('vehicle_positions', 'recorded_at', if_not_exists => TRUE)
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS delay_observations (
                    id          BIGSERIAL, 
                    trip_id     TEXT,
                    route_id    TEXT,
                    stop_id     TEXT,
                    delay_s     INTEGER,
                    temp_c      DOUBLE PRECISION,
                    precip_mm   DOUBLE PRECISION DEFAULT 0,
                    observed_at TIMESTAMPTZ NOT NULL, 
                    UNIQUE (trip_id, stop_id, observed_at)             
            )
        """))

        conn.execute(text("""
                SELECT create_hypertable('delay_observations', 'observed_at', if_not_exists => TRUE)
        """))

        conn.commit() #solitify changes


#set up engine
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

#Run
def init_db(engine):

    Base.metadata.create_all(engine)

    init_hypertables(engine)    

    print("Database Created!")

if __name__ == "__main__":
    init_db(engine)