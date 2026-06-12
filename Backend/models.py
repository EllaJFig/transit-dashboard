#Import os, dotenv, and needed sqlalchemy 
import os
from dotenv import load_dotenv
from sqlalchemy import (Integer, String, Float, Boolean, Column, Text, SmallInteger, TIMESTAMP, ForeignKey, UniqueConstraint, text, create_engine)
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, UUID
from sqlalchemy.orm import declarative_base, relationship
import sqlalchemy as sa

'''Use SQLAlchemy to do the following:
- enable TimescaleDB
- Create Static Tables
- Create Hyper Tables
'''
#Create Static Tables (stops, routes, trips, predictions, & alert_subscriptions)
Base = declarative_base()

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
    shape_id   = Column(Text)

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

class Shape(Base):
    __tablename__ = "shapes"
    __tableargs__ = (
        {"schema": None }
    )
    id            = Column(Integer, primary_key=True, autoincrement=True)
    shape_id      = Column(Text, nullable=False, index=True)
    lat           = Column(DOUBLE_PRECISION, nullable=False)
    lon           = Column(DOUBLE_PRECISION, nullable=False)
    pt_sequence   = Column(Integer, nullable=False)

#Create hypertables
class VehiclePosition(Base):
    __tablename__ = "vehicle_positions"

    trip_id = Column(String, primary_key=True, unique=True)
    recorded_at = Column(TIMESTAMP(timezone=True), primary_key=True, unique=True)
    
    id = Column(Integer) 
    route_id = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    delay_s = Column(Integer)

class DelayObservation(Base):
    __tablename__ = "delay_observations"

    id = Column(Integer)
    trip_id = Column(String, primary_key=True, unique=True)
    stop_id = Column(String, primary_key=True, unique=True)
    route_id = Column(String)

    delay_s = Column(Integer)

    temp_c = Column(DOUBLE_PRECISION)
    precip_mm = Column(DOUBLE_PRECISION, default=0.0)
    visibility = Column(Integer)

    observed_at = Column(TIMESTAMP(timezone=True), primary_key=True, unique=True)
   
class WeatherObservation(Base):
    __tablename__ = "weather_observations"
    id = Column(Integer)
    observed_hour = Column(TIMESTAMP(timezone=True), nullable=False, unique=True, primary_key=True)

    temp_c = Column(DOUBLE_PRECISION)
    feels_like_c = Column(DOUBLE_PRECISION)
    precip_1h_mm = Column(DOUBLE_PRECISION, default=0)
    snow_1h_mm = Column(DOUBLE_PRECISION, default=0)
    wind_kph = Column(DOUBLE_PRECISION)
    visibility_km = Column(DOUBLE_PRECISION)

    condition = Column(String)
    is_precipitating = Column(Boolean, default=False)


def init_hypertables(engine):
    
    with engine.begin() as conn:
        conn.execute(text("""
            SELECT create_hypertable('vehicle_positions', 'recorded_at', if_not_exists => TRUE);
        """))
        conn.execute(text("""
            SELECT create_hypertable('delay_observations', 'observed_at', if_not_exists => TRUE);
        """))
        conn.execute(text("""
            SELECT create_hypertable('weather_observations', 'observed_hour', if_not_exists => TRUE);
        """))
    

#set up engine
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

#Run
def init_db(engine):

    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaleDB;"))
            
    Base.metadata.create_all(engine)

    init_hypertables(engine)    

    print("Database Created!")

if __name__ == "__main__":
    init_db(engine)