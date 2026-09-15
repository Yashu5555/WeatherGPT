import os
import sys

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add project root and weather-api folder to Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "weather-api"))

from weather_api import get_weather
from forecast import get_forecast
from ai_module import parse_weather_query, format_weather_response


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/weather")
def weather(location: str = Query(..., min_length=1, max_length=100)):

    result = get_weather(location)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.get("/forecast")
def forecast(
    location: str = Query(..., min_length=1, max_length=100),
    days: int = Query(..., ge=1, le=14)
):

    result = get_forecast(location, days)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.get("/ask")
def ask(question: str = Query(..., min_length=1, max_length=500)):

    parsed = parse_weather_query(question)

    if "error" in parsed:
        raise HTTPException(status_code=400, detail=parsed["error"])

    location = parsed["location"]

    if parsed["intent"] == "current_weather":

        weather = get_weather(location)

        if "error" in weather:
            raise HTTPException(status_code=400, detail=weather["error"])

        weather_data = {
            "location": weather["location"],
            "forecast": [{
                "date": "today",
                "max_temp": weather["temperature"],
                "min_temp": weather["temperature"],
                "condition": weather["condition"],
                "rain_chance": weather["rain_chance"]
            }]
        }

    else:

        days = parsed.get("days", 1)
        question_lower = question.lower()

        if "day after tomorrow" in question_lower:
            days = max(days, 3)

        elif "tomorrow" in question_lower:
            days = max(days, 2)

        forecast = get_forecast(location, days)

        if "error" in forecast:
            raise HTTPException(status_code=400, detail=forecast["error"])

        weather_data = forecast

    answer = format_weather_response(question, weather_data)

    return {
        "question": question,
        "parsed": parsed,
        "answer": answer
    }
