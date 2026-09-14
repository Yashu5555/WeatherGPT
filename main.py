from weather_api.weather_api import get_weather
from weather_api.forecast import get_forecast
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
app=FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/weather")
def weather(location:str=Query(...,min_length=1,max_length=100)):
    result=get_weather(location)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
@app.get("/forecast")
def forecast(location:str=Query(...,min_length=1,max_length=100),
             days:int=Query(...,ge=1,le=14)):
    result=get_forecast(location,days)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
