'''APScheduler will run every 30 secs in the backround and FastAPI will be used as the API endpoint'''
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler #AsyncIOScheduler works best for FastAPI (whole architecture need to be async though)
from apscheduler.triggers.interval import IntervalTrigger
import random
from api.routes import router as routes_router

#poller.py get poll functions
from poller import poll_vehicle_once
from poller import poll_trips_once

load_dotenv()
GO_VEHICLE_URL = (
    "https://api.openmetrolinx.com/OpenDataAPI/api/V1/Gtfs/Feed/VehiclePosition"
    f"?key={os.getenv('GO_API_KEY')}"
)
GO_TRIP_UPDATE_URL = (
    "https://api.openmetrolinx.com/OpenDataAPI/api/V1/Gtfs/Feed/TripUpdates"
    f"?key={os.getenv('GO_API_KEY')}"
)

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
  
    #set up poll_once job's; use interval triggers every 30 sec (+/- 3secs), set id, name, and replace_existing ==TRUE
    scheduler.add_job(poll_vehicle_once, trigger=IntervalTrigger(seconds=30 + random.randint(-3,3)), id="vehicle_poller", name="Poll Vehicle Positions", replace_existing=True,args=[GO_VEHICLE_URL])
    scheduler.add_job(poll_trips_once, trigger=IntervalTrigger(seconds=30 + random.randint(-3,3)), id="trip_poller", name="Poll Trip Updates", replace_existing=True,args=[GO_TRIP_UPDATE_URL])
    
    #start scheduler
    scheduler.start()
    print("Poller Started")

    yield #run app

    #shutdown scheduler
    scheduler.shutdown()
    print("Poller Stopped")


app = FastAPI(title="Transit Dashboard API",version="0.1.0", lifespan=lifespan)
app.include_router(routes_router)

#set up health check
@app.get("/health")
async def health():
    jobs = []
    for i in scheduler.get_jobs():
        jobs.append({"id":i.id, "next_run": str(i.next_run_time)})

    return {"status": "ok", "scheduled_jobs": jobs}