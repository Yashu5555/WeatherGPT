import os
import sys
import re

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEATHER_API_DIR = os.path.join(BASE_DIR, "weather-api")

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

if WEATHER_API_DIR not in sys.path:
    sys.path.append(WEATHER_API_DIR)


from weather_api import get_weather
from forecast import get_forecast, get_tonight
from ai_module import parse_weather_query, format_weather_response


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/weather")
def weather(
    location: str = Query(..., min_length=1, max_length=100)
):
    result = get_weather(location)

    if "error" in result:
        raise HTTPException(
            status_code=400,
            detail=result["error"]
        )

    return result


@app.get("/forecast")
def forecast(
    location: str = Query(..., min_length=1, max_length=100),
    days: int = Query(..., ge=1, le=14)
):
    result = get_forecast(location, days)

    if "error" in result:
        raise HTTPException(
            status_code=400,
            detail=result["error"]
        )

    return result


@app.get("/ask")
def ask(
    question: str = Query(..., min_length=1, max_length=500)
):

    # 1. Understand question
    parsed = parse_weather_query(question)

    if "error" in parsed:
        raise HTTPException(
            status_code=400,
            detail=parsed["error"]
        )

    location = parsed["location"]
    intent = parsed["intent"]
    requested_date = parsed.get("date")

    if requested_date == "tonight":

        weather_data = get_tonight(location)

        if "error" in weather_data:
            raise HTTPException(
                status_code=400,
                detail=weather_data["error"]
            )

        weather_data["type"] = "tonight"

    elif intent == "current_weather":

        weather = get_weather(location)

        if "error" in weather:
            raise HTTPException(
                status_code=400,
                detail=weather["error"]
            )

        weather_data = {
            "type": "current",
            **weather
        }

    else:

        days = parsed.get("days", 1)
        question_lower = question.lower()

        # Tomorrow
        if "day after tomorrow" in question_lower:
            days = max(days, 3)

        elif "tomorrow" in question_lower:
            days = max(days, 2)

        # After N days
        after_match = re.search(
            r"\bafter\s+(\d+)\s*days?\b",
            question_lower
        )

        if after_match:
            days_after = int(after_match.group(1))
            days = max(days, days_after + 1)

        # This weekend
        if requested_date == "this_weekend":
            days = max(days, 7)

        forecast = get_forecast(location, days)

        if "error" in forecast:
            raise HTTPException(
                status_code=400,
                detail=forecast["error"]
            )

        weather_data = {
            "type": "forecast",
            **forecast
        }

    answer = format_weather_response(
        question,
        weather_data
    )

    return {
        "question": question,
        "parsed": parsed,
        "answer": answer
    }
