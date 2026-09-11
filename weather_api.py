import requests
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("WEATHER_API_KEY")

if not key:
    print("WEATHER_API_KEY is missing")


def get_weather(city):

    url = "https://api.weatherapi.com/v1/current.json"

    params = {
        "key": key,
        "q": city
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        data = response.json()

        if "error" in data:
            return {"error": data["error"]["message"]}

        weather = {
            "location": data["location"]["name"],
            "temperature": data["current"]["temp_c"],
            "humidity": data["current"]["humidity"],
            "condition": data["current"]["condition"]["text"],
            "wind_speed": data["current"]["wind_kph"],
            "rain_chance": data["current"]["chance_of_rain"],
            "feeling_like": data["current"]["feelslike_c"]
        }

        return weather

    except requests.exceptions.RequestException:
        return {"error": "Internet or API connection failed"}


weather = get_weather("Istanbul")

print(weather)