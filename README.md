### GO Transit Intelligence Dashboard
A real-time transit analytics platform that ingests live GO Transit and UP Express data, tracks delay patterns over time, and uses machine learning to predict how late a bus or train will be (including a confidence range based on weather, time of day, and historical patterns).

## The idea
This project started from a pretty relatable frustration. My friends and I kept noticing that GO Transit delays felt completely unpredictable, but the more we talked about it, the more we realized they weren't random at all. Rain, snow, rush hour, the specific route - all of it seemed to play a role. We'd be standing at a stop in the middle of a downpour, wondering if the bus was even coming, with no real information about what was actually happening out there or why.

That conversation turned into a question: could you actually predict this? Not just "the bus is late" but "the bus is probably going to be 4–8 minutes late, and here's why." That's what this project is trying to answer.

## What it does
- Polls live GO Transit and UP Express GTFS-Realtime feeds every 30 seconds, capturing vehicle positions and trip delay data
- Stores delay observations in a TimescaleDB time-series database, joined with live weather data from the OpenWeather API
- Trains a LightGBM machine learning model that predicts delays with probabilistic confidence intervals (not just a single number, but a range reflecting real uncertainty)
- Serves the data through a FastAPI backend with Redis caching
- Displays everything on an interactive Next.js dashboard with a live Leaflet map showing vehicle positions colour-coded by delay status, with route shape rendering on click

## Tech stack
| Layer | Technology |
| -------- | -------- |
| Data ingestion | Python, GTFS-Realtime (JSON), OpenWeather API|
| Database	| PostgreSQL + TimescaleDB |
| Caching	| Redis |
| Backend API |	FastAPI, SQLAlchemy |
| Scheduling |	APScheduler |
| ML model	| LightGBM (quantile regression) |
| Frontend	| Next.js, React, Leaflet |
| Infrastructure	| Docker, Docker Compose |

## Data Sources
**GO Transit & UP Express GTFS-Realtime:** provided by Metrolinx under their Open Data Agreement. This is an independent project and is not affiliated with, endorsed by, or associated with Metrolinx or GO Transit.
**OpenWeather API:**  current and historical weather data for the GO Transit service area

## Status
Active development. The data pipeline and map are working. The ML model is currently in training (it needs approximately 30 days of historical delay observations joined with weather data before the predictions become meaningful).
