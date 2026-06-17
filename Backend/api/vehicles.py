'''/vehicles endpoints'''
from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from models import engine, Route, Trip, Shape

router = APIRouter(prefix="/api/v1")
Session = sessionmaker(bind=engine)


@router.get("/vehicles/live")
def get_live_vehicles():
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT DISTINCT ON (trip_id)
                trip_id,
                route_id,
                lat,
                lon,
                delay_s,
                recorded_at
            FROM vehicle_positions
            WHERE recorded_at > NOW() - INTERVAL '5 minutes'
            ORDER BY trip_id, recorded_at DESC                                                             
        """)).fetchall()

    return [
        {
            "trip_id": r.trip_id,
            "route_id": r.route_id,
            "lat": r.lat,
            "lon": r.lon,
            "delay_s": r.delay_s,
            "recorded_at": str(r.recorded_at),
        }
        for r in rows
    ]