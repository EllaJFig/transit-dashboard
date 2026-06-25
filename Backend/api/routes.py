'''/route endpoints'''
from fastapi import APIRouter
from sqlalchemy.orm import sessionmaker
from models import engine, Route, Trip, Shape

router = APIRouter(prefix="/api/v1")
Session = sessionmaker(bind=engine)


@router.get("/routes")
def get_routes():
    with Session() as session:
        routes = session.query(Route).order_by(Route.short_name).all() #get all Routes ordered by their shortname
        final_routes = []
        for r in routes:
            final_routes.append({"route_id": r.route_id, "short_name": r.short_name, "long_name": r.long_name, "route_type": r.route_type,})
        
        return final_routes
       

@router.get("/routes/{route_id}/shape")
def get_shape(route_id: str):
    '''Get polyline points; order by sequence'''
    with Session() as session:
        trips = (
            session.query(Trip.shape_id)
            .filter(Trip.route_id == route_id, Trip.shape_id != None, Trip.shape_id != '')
            .distinct()
            .all()
        )
       
        if not trips:
            return {"route_id": route_id, "shapes": []}

        shapes = []
        for (shape_id,) in trips:
            points = (
                session.query(Shape)
                .filter(Shape.shape_id == shape_id)
                .order_by(Shape.pt_sequence)
                .all()
            )
            shapes.append({
                "shape_id": shape_id,
                "points": [{"lat": p.lat, "lon": p.lon} for p in points]
            })

        return {"route_id": route_id, "shapes": shapes}
    
@router.get("/trips/{trip_id}/shape")
def get_trip_shape(trip_id:str):
    '''return shape for a specific trip_id to handle routes and variants 
    ex. 31A, 31B, 31C...ect'''

    with Session() as session:
        trip = (
            session.query(Trip)
            .filter(Trip.trip_id == trip_id)
            .first()
        )
        print(f"looking for trip_id:{trip_id!r}")
        print(f"found trip: {trip}")
        print(f"shape_id is: {trip.shape_id if trip else 'NOT FOUND'}")

        if not trip or not trip.shape_id:
            return {"trip_id": trip_id, "points": []}

        #fetch shape points in order
        points = (
                session.query(Shape)
                .filter(Shape.shape_id == trip.shape_id)
                .order_by(Shape.pt_sequence)
                .all()
        )

        print(f"Found {len(points)} shape points")

        return {
            "trip_id": trip_id,
            "shape_id": trip.shape_id,
            "headsign": trip.headsign,
            "points": [{"lat": p.lat, "lon": p.lon} for p in points]
        }