'''APScheduler will run every 30 secs in the backround and FastAPI will be used as the API endpoint'''
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apscheduler.schedulers.asyncio import AsyncIOScheduler #AsyncIOScheduler works best for FastAPI (whole architecture need to be async though)
from apscheduler.triggers.interval import IntervalTrigger

import random
from datetime import timezone, datetime

from api.routes import router as routes_router
from api.vehicles import router as vehicle_router
from api.predictions import router as prediction_router

#poller.py get poll functions
from poller import poll_vehicle_once
from poller import poll_trips_once, poll_weather_once


load_dotenv()
GO_VEHICLE_URL = (
    "https://api.openmetrolinx.com/OpenDataAPI/api/V1/Gtfs/Feed/VehiclePosition"
    f"?key={os.getenv('GO_API_KEY')}"
)
GO_TRIP_UPDATE_URL = (
    "https://api.openmetrolinx.com/OpenDataAPI/api/V1/Gtfs/Feed/TripUpdates"
    f"?key={os.getenv('GO_API_KEY')}"
)
OPENWEATHER_URL = (
    "https://api.openweathermap.org/data/2.5/weather?lat="
    f"{os.getenv('WEATHER_LAT')}&lon={os.getenv('WEATHER_LON')}&appid={os.getenv('OPENWEATHER_API_KEY')}&units=metric"
)

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
  
    #set up poll_once job's; use interval triggers every 30 sec (+/- 3secs), set id, name, and replace_existing ==TRUE
    scheduler.add_job(poll_vehicle_once, trigger=IntervalTrigger(seconds=30 + random.randint(-3,3)), id="vehicle_poller", name="Poll Vehicle Positions", replace_existing=True,args=[GO_VEHICLE_URL])
    scheduler.add_job(poll_trips_once, trigger=IntervalTrigger(seconds=30 + random.randint(-3,3)), id="trip_poller", name="Poll Trip Updates", replace_existing=True,args=[GO_TRIP_UPDATE_URL])
    scheduler.add_job(poll_weather_once, trigger=IntervalTrigger(hours=1), id="weather_poller", name="Poll Weather Observations", replace_existing=True, next_run_time=datetime.now(timezone.utc), args=[OPENWEATHER_URL]) 
    
    #start scheduler
    scheduler.start()
    print("Poller Started")

    yield #run app

    #shutdown scheduler
    scheduler.shutdown()
    print("Poller Stopped")


#initalize endpoints
app = FastAPI(title="Transit Dashboard API",version="0.1.0", lifespan=lifespan)

#ports that are allowed to call eachother
origins = [
    f"{os.getenv('ORIGIN1')}",  
    f"{os.getenv('ORIGIN2')}",
]

app.add_middleware(
    CORSMiddleware, 
    allow_origins=origins, 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"],
)

app.include_router(routes_router)
app.include_router(vehicle_router)
app.include_router(prediction_router)

#set up health check
@app.get("/health")
async def health():
    jobs = []
    for i in scheduler.get_jobs():
        jobs.append({"id":i.id, "next_run": str(i.next_run_time)})

    return {"status": "ok", "scheduled_jobs": jobs}