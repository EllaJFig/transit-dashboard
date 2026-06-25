"use client";

import { useEffect, useState } from 'react';
import {MapContainer, TileLayer, CircleMarker, Popup, Polyline} from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

interface Vehicle {
    trip_id: string;
    route_id: string;
    lat: number;
    lon: number;
    delay_s: number | null;
    recorded_at: string;
}

function delayColour(s: number | null){
    if (s===null) return "#64748b";
    if (s <=60) return  "#22c55e";
    if (s <= 300) return "#f59e0b"
    return "#f13131";
}

function formatDelay(s:number| null){
    if (s=== null || s=== undefined) return "no data";
    if (s <= 0) return "on time";
    const m = Math.floor(s/60), sec = s%60;
    return m > 0 ? `${m}m ${sec}s late` : `${sec}s late`;
}


export default function Map() {
    const [vehicles, setVehicles] = useState<Vehicle[]>([]);
    const [shape,setShape] = useState<[number,number][]>([]);
    const [updated, setUpdated] = useState("");
    
    useEffect(() => {
        const load = async () =>{
            try {
                const res = await fetch("http://localhost:8000/api/v1/vehicles/live");
                const data = await res.json();
                console.log("Raw API Data:", data);
                
                const seen = new globalThis.Map<string, Vehicle>();
                data.forEach((v:Vehicle) => seen.set(v.trip_id, v));

                setVehicles(Array.from(seen.values()));
                setUpdated(new Date().toLocaleTimeString());
            } catch (error){
                console.error("Fetch failed with error: ", error)}
        };
        load();
        const id = setInterval(load,30_000);
        return () => clearInterval(id);
    }, []);

    const onVehicleClick = async (tripId: string) =>{
        try{
            const res = await fetch(`http://localhost:8000/api/v1/trips/${tripId}/shape`);
            const data = await res.json();
            if (data.points && data.points.length > 0) {
                setShape(data.points.map( (p:any) => [p.lat, p.lon]));
            }else {
                setShape([]);
            }
        } catch (err) {
            console.error("Failed to fetch shape:", err)
        }
    };
    

    return (
        <div style={{display:"flex", flexDirection:"column", height:"100vh"}}> 
            
            {/*header*/}
            <div style={{
                padding: "10px 18px",
                background: "#1e2433",
                borderBottom: "1px solid #2d3548",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                flexShrink: 0,
            }}>
                <span style={{fontWeight: 600, fontSize: 16}}>GO Transit </span>
                <span style={{ fontSize:12, color: "#64748b"}} >
                    {vehicles.length} vehicles
                    {updated && `. ${updated}`}
                </span>
            </div>

            {/*map*/}
            <div style={{flex:1, position:"relative"}}>
                <MapContainer 
                    center={[43.63,-79.39]} 
                    zoom={13} 
                    style={{height: "100%", width: "100%"}}
                >
                    <TileLayer
                    attribution = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                    url = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager_labels_under/{z}/{x}/{y}{r}.png'
                    />
                    {shape.length > 0 && (
                        <Polyline
                            positions={shape}
                            pathOptions={{color: "#3b82f6", weight: 3, opacity: 0.75}}
                        />
                    )} 

                    {vehicles.map(v=> (
                        <CircleMarker
                            key={`${v.trip_id}-${v.recorded_at}`}
                            center={[v.lat, v.lon]}
                            radius={6}
                            pathOptions={{
                                fillColor: delayColour(v.delay_s),
                                fillOpacity: 0.85,
                                color: "#111318",
                                weight: 1.5,
                            }}
                            eventHandlers={{click: () => onVehicleClick(v.trip_id) }}
                        >
                            <Popup>
                                <div style={{fontSize: 13, lineHeight: 1.6}}>
                                    <strong>{v.route_id}</strong><br />
                                    {formatDelay(v.delay_s)}<br />
                                    <span style={{color:"#64748b", fontSize: 11}}>{v.trip_id}</span>
                                </div>
                            </Popup>
                        </CircleMarker>
                    ))}
                </MapContainer>
            </div>


            {/*legend*/}
            <div style={{
                padding:"8px 18px",
                background: "#1e2433",
                borderTop: "1px solid #2d3548",
                display: "flex",
                gap: 20,
                fontSize: 12,
                color: "#94a3b8",
                flexShrink: 0,
            }}>
                {[["#22c55e", "On time"], ["#f59e0b", "< 5 mins late"], ["#cd0e0e", "> 5 mins late"], ["#64748b", "Unknown"],
                ].map(([c,l]) => (
                    <div key={l} style={{display:"flex", alignItems:"center", gap: 6}}>
                        <div style = {{width: 8, height: 8, borderRadius: "50%", background:c}} />
                        {l}
                    </div>
                ))}
                <span style={ {marginLeft: "auto"}}> Click a vehicle to see its route</span>
            </div>
        </div>
    );
}
