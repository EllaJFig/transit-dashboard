from fastapi import APIRouter
from sqlalchemy.orm import sessionmaker
from models import engine, Prediction

router = APIRouter(prefix="/api/v1")
Session = sessionmaker(bind=engine)


@router.get("/predictions")
def get_predictions():
    with Session() as session:
        predictions = session.query(Prediction).order_by(Prediction.route_id).all() #get all Routes ordered by their shortname
        final_predictions = []
        for p in predictions:
            final_predictions.append({"route_id": p.route_id, "hour_of_day": p.hour_of_day, "day_of_week": p.day_of_week, "precip_bucket": p.precip_bucket, "prediction_delay": p.prediction_delay, "p10": p.p10, "p90": p.p90, "model_version": p.model_version, "generated_at": p.generated_at,})
        
        return final_predictions