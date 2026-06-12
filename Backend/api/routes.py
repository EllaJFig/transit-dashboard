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