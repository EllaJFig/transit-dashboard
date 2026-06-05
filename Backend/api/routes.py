'''/route endpoints'''
from fastapi import APIRouter
from sqlalchemy.orm import sessionmaker
from models import engine, Route

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
       