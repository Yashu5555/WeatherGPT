import requests
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("WEATHER_API_KEY")
if not key:
    raise ValueError("WEATHER_API_KEY is missing")


def get_forecast(city,days):

    url = "https://api.weatherapi.com/v1/forecast.json"

    params = {
        "key": key,
        "q": city,
        "days": days
    }
    try:
        response = requests.get(url, params=params,timeout=10)
        response.raise_for_status()

        data = response.json()
        if "error" in data:
            return {
                "error": data["error"]["message"]
            }

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

        return {
    "location": data["location"]["name"],
    "forecast": forecast
}
    except requests.exceptions.RequestException:
                return {"error": "Internet or API connection failed"}


if __name__ == "__main__":
        print(get_forecast("Hyderabad",7))
