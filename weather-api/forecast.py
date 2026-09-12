import requests
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("WEATHER_API_KEY")
if not key:
    print("WEATHER_API_KEY is missing")


def get_forecast(city):

    url = "https://api.weatherapi.com/v1/forecast.json"

    params = {
        "key": key,
        "q": city,
        "days": 3
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()

        forecast = []

        for day in data["forecast"]["forecastday"]:
            weather = {
                "date": day["date"],
                "max_temp": day["day"]["maxtemp_c"],
                "min_temp": day["day"]["mintemp_c"],
                "condition": day["day"]["condition"]["text"],
                "rain_chance": day["day"]["daily_chance_of_rain"],
                "sunrise": day["astro"]["sunrise"],
                "sunset": day["astro"]["sunset"]
            }   

            forecast.append(weather)

        return forecast
    except requests.exceptions.RequestException:
                return {"error": "Internet or API connection failed"}


forecast = get_forecast("Hyderabad")

for day in forecast:
    print(day)
