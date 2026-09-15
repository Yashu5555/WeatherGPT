import requests
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("WEATHER_API_KEY")

if not key:
    raise ValueError("WEATHER_API_KEY is missing")


def get_forecast(city, days):

    url = "https://api.weatherapi.com/v1/forecast.json"

    if not 1 <= days <= 14:
        return {"error": "Forecast days must be between 1 and 14"}

    params = {
        "key": key,
        "q": city,
        "days": days
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if "error" in data:
            code = data["error"].get("code")

            if code == 1006:
                return {"error": "Location not found"}
            if code == 2006:
                return {"error": "Weather API key is invalid"}
            if code == 2007:
                return {"error": "Weather API request limit exceeded"}
            if code == 2008:
                return {"error": "Weather API key is disabled"}
            if code == 2009:
                return {"error": "Weather API access denied"}

            return {"error": "Weather service returned an error"}

        response.raise_for_status()

        forecast = []

        for day in data["forecast"]["forecastday"]:

            weather = {
                "date": day["date"],
                "max_temp": day["day"]["maxtemp_c"],
                "min_temp": day["day"]["mintemp_c"],
                "condition": day["day"]["condition"]["text"],
                "rain_chance": day["day"]["daily_chance_of_rain"],
                "uv": day["day"]["uv"],
                "sunrise": day["astro"]["sunrise"],
                "sunset": day["astro"]["sunset"]
            }

            forecast.append(weather)

        return {
            "location": data["location"]["name"],
            "forecast": forecast
        }

    except requests.exceptions.HTTPError:
        return {"error": "Weather API request failed"}

    except requests.exceptions.RequestException:
        return {"error": "Unable to connect to weather service"}

    except ValueError:
        return {"error": "Invalid response received from weather service"}


def get_tonight(city):

    url = "https://api.weatherapi.com/v1/forecast.json"

    params = {
        "key": key,
        "q": city,
        "days": 1
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if "error" in data:
            return {"error": "Weather service returned an error"}

        response.raise_for_status()

        forecast_day = data["forecast"]["forecastday"][0]
        hours = forecast_day["hour"]

        local_time = data["location"]["localtime"]
        current_hour = int(local_time[11:13])

        tonight = []

        for hour in hours:

            hour_time = hour["time"]
            hour_value = int(hour_time[11:13])

            if hour_value >= max(current_hour, 18):

                tonight.append({
                    "time": hour_time,
                    "temperature": hour["temp_c"],
                    "condition": hour["condition"]["text"],
                    "rain_chance": hour["chance_of_rain"],
                    "wind_speed": hour["wind_kph"]
                })

        return {
            "location": data["location"]["name"],
            "tonight": tonight
        }

    except requests.exceptions.RequestException:
        return {"error": "Unable to connect to weather service"}

    except (ValueError, KeyError, IndexError):
        return {"error": "Invalid response received from weather service"}


if __name__ == "__main__":
    print(get_forecast("Hyderabad", 7))
    print(get_tonight("Hyderabad"))
