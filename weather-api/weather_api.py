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
        
        data = response.json()
        
        if "error" in data:
            code = data["error"].get("code")

            if code == 1006:
                return {"error": "Location not found"}

            if code == 2006:
                return {"error": "Weather API key is invalid"}

            return {"error": "Weather service returned an error"}
        
        response.raise_for_status()

        return {
            "location": data["location"]["name"],
            "temperature": data["current"]["temp_c"],
            "humidity": data["current"]["humidity"],
            "condition": data["current"]["condition"]["text"],
            "wind_speed": data["current"]["wind_kph"],
            "rain_chance": data["current"]["chance_of_rain"],
            "feeling_like": data["current"]["feelslike_c"]
        }

    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            try:
                error_data = e.response.json()
                error_code = error_data.get("error", {}).get("code")

                if error_code == 1006:
                    return {"error": "Location not found"}

                if error_code == 2006:
                    return {"error": "Weather API key is invalid"}

            except ValueError:
                pass

        return {"error": "Weather API request failed"}
    
    except requests.exceptions.RequestException:
        return {"error": "Unable to connect to weather service"}

    except ValueError:
        return {"error": "Invalid response received from weather service"}


if __name__ == "__main__":
    print(get_weather("Hyderabad"))
