import os
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("WEATHER_API_KEY")

if not key:
    raise ValueError("WEATHER_API_KEY is missing")


def get_weather(city):

    url = "https://api.weatherapi.com/v1/current.json"

    params = {
        "key": key,
        "q": city
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if "error" in data:
            return {"error": data["error"]["message"]}

        return {
            "location": data["location"]["name"],
            "temperature": data["current"]["temp_c"],
            "humidity": data["current"]["humidity"],
            "condition": data["current"]["condition"]["text"],
            "wind_speed": data["current"]["wind_kph"],
            "rain_chance": data["current"]["chance_of_rain"],
            "feeling_like": data["current"]["feelslike_c"]
        }

    except requests.exceptions.RequestException as e:
        return {"error": f"Weather API request failed: {e}"}

    except ValueError:
        return {"error": "Invalid response received from weather API"}


if __name__ == "__main__":
    print(get_weather("Hyderabad"))
