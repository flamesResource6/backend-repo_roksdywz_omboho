from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="Weather Effects API")

# CORS for local dev and preview
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"
GEOCODE_BASE = "https://geocoding-api.open-meteo.com/v1/search"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/geocode")
async def geocode(q: str = Query(..., description="City or place name")):
    params = {"name": q, "count": 5, "language": "en", "format": "json"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(GEOCODE_BASE, params=params)
        r.raise_for_status()
        data = r.json()
        results = []
        for item in data.get("results", []):
            results.append({
                "name": item.get("name"),
                "country": item.get("country"),
                "admin1": item.get("admin1"),
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
            })
        return {"results": results}


@app.get("/weather")
async def weather(lat: float, lon: float):
    # We request current weather and hourly precipitation for rain intensity
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "precipitation",
            "wind_speed_10m",
            "wind_gusts_10m",
            "weather_code",
        ],
        "hourly": ["precipitation", "cloud_cover"],
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(OPEN_METEO_BASE, params=params)
        r.raise_for_status()
        data = r.json()

    curr = data.get("current", {})
    hourly = data.get("hourly", {})
    result = {
        "temperature": curr.get("temperature_2m"),
        "apparent_temperature": curr.get("apparent_temperature"),
        "humidity": curr.get("relative_humidity_2m"),
        "precipitation": curr.get("precipitation"),
        "wind_speed": curr.get("wind_speed_10m"),
        "wind_gusts": curr.get("wind_gusts_10m"),
        "weather_code": curr.get("weather_code"),
        "hourly": {
            "precipitation": hourly.get("precipitation"),
            "cloud_cover": hourly.get("cloud_cover"),
            "time": hourly.get("time"),
        },
    }
    return result
