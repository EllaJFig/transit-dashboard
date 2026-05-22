'''Load the static GTFS data from the zips folder'''
import io
import csv
import os
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from zipfile import ZipFile
from models import engine, Route, Stop, Trip

load_dotenv()
Session = sessionmaker(bind=engine)

def load_static_GTFS(zip_path):
    '''
    Load static GTFS Go data from files named routes.txt, stops.txt, & trips.txt into the database using SQLalchemy

    Args:
        zip_path (str): zip file path
    '''

    with ZipFile(zip_path, 'r') as f:
        #print(f.namelist())
        
        with Session() as session:

            with f.open('routes.txt', 'r') as routes:
                #read the route_id, route_short_name, route_long_name, route_type
                reader = csv.DictReader(io.TextIOWrapper(routes, encoding='utf-8-sig')) #first column appears as '\ufeffroute_id' so fixed using encoding
                for r in reader:
                    route_id = r['route_id']
                    route_short_name = r.get('route_short_name', "")
                    route_long_name = r.get('route_long_name', "")
                    route_type = int(r.get('route_type',3)) #if not there default to a bus route
                    
                    route = Route(route_id=route_id, short_name=route_short_name, long_name= route_long_name, route_type=route_type,)
                    session.merge(route) #use merge not add to handle error if something needs to be updated 
                session.commit()
                print("Routes loaded")
               

            with f.open('stops.txt', 'r') as stops:
                #read the stop_id, stop_name, stop_lat, stop_lon
                reader = csv.DictReader(io.TextIOWrapper(stops, encoding='utf-8-sig'))
                for r in reader:
                    stop_id = r['stop_id']
                    stop_name = r.get('stop_name', "")
                    stop_lat = float(r.get('stop_lat', 0))
                    stop_lon = float(r.get('stop_lon', 0)) 

                    stop = Stop(stop_id=stop_id, stop_name=stop_name, lat= stop_lat, lon=stop_lon,)
                    session.merge(stop)
                session.commit()
                print("Stops loaded")

            with f.open('trips.txt', 'r') as trips:
                #read the trip_id, route_id, service_id, trip_headsign
                reader = csv.DictReader(io.TextIOWrapper(trips, encoding='utf-8-sig'))
                for r in reader:
                    trip_id = r['trip_id']
                    route_id = r.get('route_id', "")
                    service_id = r.get('service_id', "")
                    trip_headsign = r.get('trip_headsign', "") 

                    trip = Trip(trip_id=trip_id, route_id=route_id, service_id= service_id, headsign=trip_headsign,)
                    session.merge(trip)
                session.commit()
                print("Trips loaded")

    print("Static GTFS loaded!")


#Testing & Set up

ZIP_PATH_GTFS_GO = os.getenv("ZIP_PATH_GTFS_GO")
ZIP_PATH_GTFS_UP = os.getenv("ZIP_PATH_GTFS_UP")

if __name__ == '__main__':
    load_static_GTFS(ZIP_PATH_GTFS_GO)
    print("Static GTFS-Go loaded!---")

    load_static_GTFS(ZIP_PATH_GTFS_UP)
    print("Static GTFS-Up loaded!---")




