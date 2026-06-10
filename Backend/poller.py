'''polling GTFS-RT (TBD) manually polling from designed endpoints.
-> output of API is Json so parse accordingly
-> set up to fetch every 30 to 60 secs'''

import requests
import os
from dotenv import load_dotenv
from datetime import timezone, datetime
from sqlalchemy import text
from json import JSONDecodeError
from models import engine

def poll_vehicle_once(url):
    '''
    Poll the vehicle data manually from url (assumes key is included) and sets data into engine (database)

    Args:
        url (str): url for polling
    '''
    
    try:
        response = requests.get(url=url, timeout=10) #requests handles the url and timeout
        response.raise_for_status()
        
        data = response.json() # GTFS parser 

        if not 'entity' in data:
            print("no enitities in data")
            return
        
        transit_records = data['entity']
        
        if len(transit_records) == 0:
            print("Entity array is empty.")
            return

        #print("Structure of the first record is:", transit_records[0].keys())
    except requests.exceptions.HTTPError as http_err:
        print(f"Transit API down or mad: {http_err}")
        return
    except JSONDecodeError:
        print("API doesnt return valid json!!!")
        return
    

    #loop through transit data and store in records
    records = []
    for entity in transit_records:
        """
        Specifics:
            Entity -> vehicle -> trip      which has; trip_id, route_id
            Entity -> vehicle -> position  which has; latitude, longitude, 

        """
        if entity.get("is_deleted") is True:
            continue
        

        if 'vehicle' in entity and entity['vehicle']:
            v = entity["vehicle"]
            if not v:
                continue
            
            trip = v.get("trip") or v.get("Trip") or {}
            position = v.get("position") or v.get("Position")  or {}

            trip_id = str(trip.get("trip_id", "")).strip()
            route_id = str(trip.get("route_id", "")).strip()

            lat = position.get("latitude") or position.get("Latitude")
            lon = position.get("longitude") or position.get("Longitude")

            ts = v.get("timestamp") or v.get("Timestamp")

            #skip GTFS that dont have a trip_id or lat/lon 
            if (not trip_id and not route_id) or lat is None or lon is None:
                continue
            #validate lat between -90 to 90 AND lon between -180 to 180
            if (float(lat) == 0.0 and float(lon) == 0.0):
                continue
            if not trip_id:
                trip_id = f"UNKNOWN-ROUTE-{route_id}"
            
            
            recorded_at = datetime.fromtimestamp(int(ts), tz=timezone.utc) if ts else datetime.now(timezone.utc)
            

            #add records = trip_id, route_id, lat, lon, delay_s(dont record this cause its unreliable), recorded_at
            records.append({
                "trip_id": trip_id,
                "route_id": route_id,
                "lat": round(lat,6),
                "lon": round(lon,6),
                "delay_s": None,
                "recorded_at": recorded_at,
            })

    #add records to database
    if records:
        with engine.connect() as conn:
            conn.execute(text(""" 
            INSERT INTO vehicle_positions (trip_id, route_id, lat, lon, delay_s, recorded_at)
            VALUES (:trip_id, :route_id, :lat, :lon, :delay_s, :recorded_at)
            ON CONFLICT (trip_id, recorded_at) DO NOTHING
            """), records)
            
            conn.commit()
            print(f"inserted {len(records)} vehicle positions into database")
    else:
        print("no valid records from poller")
    
def poll_trips_once(url):
    '''
    Poll TripUpdate data manually from url (assumes key is included) and sets data into engine (database)

    Args:
        url (str): url for polling
    '''
    try:
        response = requests.get(url=url, timeout=10) #requests handles the url and timeout
        response.raise_for_status()
        
        data = response.json() # GTFS parser 

        if not 'entity' in data:
            print("no enitities in data")
            return
        
        transit_records = data['entity']
        
        if len(transit_records) == 0:
            print("Entity array is empty.")
            return

        #print("Structure of the first record is:", transit_records[0].keys())
    except requests.exceptions.HTTPError as http_err:
        print(f"Transit API down or mad: {http_err}")
        return
    except JSONDecodeError:
        print("API doesnt return valid json!!!")
        return
    
    records = []
    for entity in transit_records:
        """
        Specifics:
            Entity -> trip_update -> trip              which has; route_id, trip_id
            Entity -> trip_update -> stop_time_update  which has; stop_id, arrival, departure(delay,time, uncertainty) 

        """
        if entity.get("is_deleted") is True:
            continue

        if 'trip_update' in entity and entity['trip_update']:
            tu = entity["trip_update"]
            if not tu:
                continue
            
            trip = tu.get("trip") or tu.get("Trip") or {}
            trip_id = str(trip.get("trip_id", "")).strip()
            route_id = str(trip.get("route_id", "")).strip()

            #skip GTFS that dont have a trip_id
            if not trip_id:
                continue
            
            #Time configs
            ts = tu.get("timestamp") or tu.get("Timestamp")
            observed_at = datetime.fromtimestamp(int(ts), tz=timezone.utc) if ts else datetime.now(timezone.utc)

            stop_time_update = tu.get("stop_time_update") or []
            for stu in stop_time_update:

                stop_id = str(stu.get("stop_id","")).strip() or None

                arrival = stu.get("arrival") or {}
                departure = stu.get("departure") or {}
                delay_raw = arrival.get("delay", "") if arrival else departure.get("delay", "") #use arrival delay as first resort
                delay = int(delay_raw) if delay_raw is not None else 0

                #if delays is >2hours or early by 30mins then there is a data error
                if delay > 7200 or delay < -1800:
                    continue

                #add records = trip_id, route_id, stop_id, temp_c, precip_mm, observed_at
                records.append({
                    "trip_id": trip_id,
                    "route_id": route_id,
                    "stop_id": stop_id,
                    "delay_s": delay,
                    "precip_mm": 0.0, #add weather data later
                    "temp_c": None,
                    "observed_at": observed_at,
                })

    #add records to database
    if records:
        with engine.connect() as conn:
            conn.execute(text(""" 
            INSERT INTO delay_observations (trip_id, route_id, stop_id, delay_s, temp_c, precip_mm, observed_at)
            VALUES (:trip_id, :route_id, :stop_id, :delay_s, :temp_c, :precip_mm, :observed_at)
            ON CONFLICT (trip_id, stop_id, observed_at) DO NOTHING
            """), records)
            
            conn.commit()
            print(f"inserted {len(records)} delay observations into database")
    else:
        print("no valid records from poller")   

def poll_weather_once(url):
    '''
    Poll OpenWeather data manually from url (assumes key is included) and store it into database in weather_observations table

    Args:
        url (str): url for polling
    '''
    try:
        response = requests.get(url=url, timeout=10) #requests handles the url and timeout
        response.raise_for_status()
        
        data = response.json() #OpenWeather API data 

        
    except requests.exceptions.HTTPError as http_err:
        print(f"OpenWeather API down or mad: {http_err}")
        return
    except requests.exceptions.Timeout:
        print("OpenWeather API Timeout")
        return
    except requests.exceptions.ConnectionError:
        print("OpenWeather API connection failure")
        return
    
    now = datetime.now(timezone.utc)
    observed_hour = now.replace(minute=0, second=0, microsecond=0) #only grab the hour weather was observed at
    
    #headers
    main = data.get('main', {})
    wind = data.get('wind', {})
    rain = data.get('rain', {}) #NOTE: rain and snow data will be absent if no rain or snow
    snow = data.get('snow', {})
    weather = data.get('weather', [{}])[0]

    #body
    temp_c = main.get('temp')
    feels_like_c = main.get('feels_like')
    precip_1h_mm = rain.get('1h',0.0)
    snow_1h_mm = snow.get('1h', 0.0)
    wind_kph = round(wind.get('speed',0) *3.6, 1) # convert mph to kmp

    visibility_m = data.get('visibility', 10000) #visibility in meters; default 10000
    visibility_km = round(min(visibility_m/1000, 10.0), 2) # visibility in km; cap at 10

    """
    OpenWeather id meaning:
    801-804: Clouds
    800: clear sky
    700: fog, mist, dust
    600: snow
    500: rain
    300: Drizzle
    200: Thunderstorms
    """
    condition_id = int(weather.get('id', 800))
    if 701 <= condition_id <= 781:
        condition = "fog" #visibility issue; its a wide range
    elif snow_1h_mm > 0.1 or (600 <= condition_id <= 622):
         condition = "snow"
    elif precip_1h_mm > 2.0 or (500 <= condition_id <= 531):
        condition = "rain"
    elif precip_1h_mm > 0 or (300 <= condition_id <= 321):
        condition = "drizzle"
    elif 200 <= condition_id <= 232:
        condition = "thunderstorm"
    else:
        condition = "clear"

    is_precipitating = condition in ('snow', 'drizzle', 'rain', 'thunderstorm')

    record = {
        "observed_hour": observed_hour,
        "temp_c": temp_c,
        "feels_like_c": feels_like_c,
        "precip_1h_mm": precip_1h_mm,
        "snow_1h_mm": snow_1h_mm,
        "wind_kph": wind_kph,
        "visibility_km": visibility_km,
        "condition": condition,
        "is_precipitating": is_precipitating,
    }

    if record:
        with engine.connect() as conn:
                conn.execute(text(""" 
                INSERT INTO weather_observations (observed_hour, temp_c, feels_like_c, precip_1h_mm, snow_1h_mm, wind_kph, visibility_km, condition, is_precipitating)
                VALUES (:observed_hour, :temp_c, :feels_like_c, :precip_1h_mm, :snow_1h_mm, :wind_kph, :visibility_km, :condition, :is_precipitating)
                ON CONFLICT (observed_hour) DO UPDATE SET
                    temp_c              = EXCLUDED.temp_c,   
                    feels_like_c        = EXCLUDED.feels_like_c,   
                    precip_1h_mm        = EXCLUDED.precip_1h_mm,   
                    snow_1h_mm          = EXCLUDED.snow_1h_mm,
                    wind_kph            = EXCLUDED.wind_kph,
                    visibility_km       = EXCLUDED.visibility_km,
                    condition           = EXCLUDED.condition,
                    is_precipitating    = EXCLUDED.is_precipitating              
                """), record)
                
                conn.commit()
                print(f"Current Weather recorded as: {temp_c} C , {condition}, precip: {precip_1h_mm}mm, snow: {snow_1h_mm}mm, wind: {wind_kph}kph, visibility: {visibility_km}km")
    else:
        print("no valid records from poller")  

#Load URL's + keys
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
if __name__ == "__main__":
    #poll_vehicle_once(GO_VEHICLE_URL)
    #poll_trips_once(GO_TRIP_UPDATE_URL)
    poll_weather_once(OPENWEATHER_URL)
