"""
Converts structured weather data from the backend into clear,
natural-language responses for the user.
"""

import json
from typing import Any, Dict, Union


def format_weather_response(weather_data: Union[Dict[str, Any], str, None]) -> str:
    """
    Convert weather data into a readable natural-language response.

    Args:
        weather_data: A dictionary or JSON string containing weather fields
                      such as city, date, temperature, feels_like, condition,
                      humidity, wind_speed, and rain_probability.

    Returns:
        str: A human-readable weather summary string, or a fallback message
             if weather data is unavailable or invalid.
    """
    fallback_message = "Sorry, weather information is currently unavailable."

    # 1. Validate input and parse JSON string if needed
    if weather_data is None:
        return fallback_message

    if isinstance(weather_data, str):
        try:
            weather_data = json.loads(weather_data)
        except (json.JSONDecodeError, TypeError, ValueError):
            return fallback_message

    if not isinstance(weather_data, dict) or not weather_data:
        return fallback_message

    # 2. Extract fields safely with fallback to None
    city = weather_data.get("city") or weather_data.get("location")
    date_val = weather_data.get("date")
    temperature = weather_data.get("temperature") or weather_data.get("temp")
    feels_like = weather_data.get("feels_like")
    condition = weather_data.get("condition") or weather_data.get("weather")
    humidity = weather_data.get("humidity")
    wind_speed = weather_data.get("wind_speed")
    rain_probability = weather_data.get("rain_probability") or weather_data.get("chance_of_rain")

    # If all primary data fields are missing, return fallback
    if not any([city, temperature, condition, humidity, wind_speed, feels_like, rain_probability]):
        return fallback_message

    # 3. Format date and determine tense (is vs will be)
    date_str = str(date_val).strip() if date_val is not None else ""
    date_lower = date_str.lower()

    is_future = date_lower in {"tomorrow", "day after tomorrow", "next week", "next weekend"} or (
        date_lower and date_lower not in {"today", "now", "currently", "present", "at present"}
    )

    verb_be = "will be" if is_future else "is"

    # Build intro phrase (e.g. "Tomorrow in Hyderabad", "In Hyderabad", "Today")
    intro_parts = []
    if date_str:
        intro_parts.append(date_str.capitalize())
    if city:
        city_formatted = str(city).strip().title()
        intro_parts.append(f"in {city_formatted}" if date_str else f"In {city_formatted}")

    intro_phrase = " ".join(intro_parts) if intro_parts else ""

    # Helper function to format units
    def format_temp(val: Any) -> str:
        s = str(val).strip()
        if not s.endswith("°C") and not s.endswith("°F") and not s.endswith("°") and not s.endswith("C") and not s.endswith("F"):
            return f"{s}°C"
        return s

    def format_percent(val: Any) -> str:
        s = str(val).strip()
        return s if s.endswith("%") else f"{s}%"

    def format_speed(val: Any) -> str:
        s = str(val).strip()
        return s if ("km/h" in s.lower() or "mph" in s.lower() or "m/s" in s.lower()) else f"{s} km/h"

    sentences = []

    # 4. Build main temperature and condition sentence
    main_sentence_parts = []

    if intro_phrase:
        main_sentence_parts.append(f"{intro_phrase},")

    if temperature is not None and condition:
        temp_str = format_temp(temperature)
        cond_str = str(condition).strip().lower()
        cond_phrase = cond_str if "conditions" in cond_str or "weather" in cond_str else f"{cond_str} conditions"
        main_sentence_parts.append(f"the temperature {verb_be} {temp_str} with {cond_phrase}.")
    elif temperature is not None:
        temp_str = format_temp(temperature)
        main_sentence_parts.append(f"the temperature {verb_be} {temp_str}.")
    elif condition:
        cond_str = str(condition).strip().lower()
        cond_phrase = cond_str if "conditions" in cond_str or "weather" in cond_str else f"{cond_str} conditions"
        main_sentence_parts.append(f"expect {cond_phrase}.")

    if main_sentence_parts:
        sentences.append(" ".join(main_sentence_parts))

    # 5. Feels like temperature sentence
    if feels_like is not None:
        feels_str = format_temp(feels_like)
        verb_feels = "will feel" if is_future else "feels"
        sentences.append(f"It {verb_feels} like {feels_str}.")

    # 6. Humidity and Wind Speed sentence
    sec_details = []
    if humidity is not None:
        hum_str = format_percent(humidity)
        sec_details.append(f"Humidity {verb_be} {hum_str}")
    if wind_speed is not None:
        wind_str = format_speed(wind_speed)
        sec_details.append(f"wind speed {verb_be} {wind_str}")

    if len(sec_details) == 2:
        sentences.append(f"{sec_details[0]} and {sec_details[1]}.")
    elif len(sec_details) == 1:
        sentences.append(f"{sec_details[0]}.")

    # 7. Rain probability sentence
    if rain_probability is not None:
        rain_str = format_percent(rain_probability)
        sentences.append(f"There is a {rain_str} chance of rain.")

    # 8. Combine and clean final output
    if not sentences:
        return fallback_message

    final_response = " ".join(sentences).strip()
    return final_response


if __name__ == "__main__":
    print("=" * 60)
    print("Weather Response Formatter - Test Cases")
    print("=" * 60)

    test_cases = [
        # 1. Full data with future forecast (tomorrow)
        {
            "name": "Full Data (Tomorrow)",
            "data": {
                "city": "Hyderabad",
                "date": "tomorrow",
                "temperature": 29,
                "feels_like": 31,
                "condition": "partly cloudy",
                "humidity": 65,
                "wind_speed": 12,
                "rain_probability": 20
            }
        },
        # 2. Current weather (today)
        {
            "name": "Current Weather (Today)",
            "data": {
                "city": "Mumbai",
                "date": "today",
                "temperature": 32,
                "feels_like": 36,
                "condition": "sunny",
                "humidity": 70,
                "wind_speed": 15,
                "rain_probability": 10
            }
        },
        # 3. JSON string input
        {
            "name": "JSON String Input",
            "data": json.dumps({
                "city": "Delhi",
                "date": "tomorrow",
                "temperature": "34°C",
                "condition": "clear sky",
                "humidity": "45%",
                "wind_speed": "10 km/h"
            })
        },
        # 4. Partial data (missing humidity, wind, and feels_like)
        {
            "name": "Partial Data (City, Date, Temp, Condition)",
            "data": {
                "city": "Bangalore",
                "date": "Friday",
                "temperature": 26,
                "condition": "light rain",
                "rain_probability": 80
            }
        },
        # 5. Minimal data (only city and temperature)
        {
            "name": "Minimal Data (City & Temp only)",
            "data": {
                "city": "Tokyo",
                "temperature": 18
            }
        },
        # 6. Empty dictionary (Invalid)
        {
            "name": "Empty Data",
            "data": {}
        },
        # 7. None / Null input (Invalid)
        {
            "name": "None Input",
            "data": None
        },
        # 8. Malformed JSON string
        {
            "name": "Malformed JSON String",
            "data": "{invalid_json: true"
        }
    ]

    for tc in test_cases:
        print(f"\n[Test: {tc['name']}]")
        print(f"Input : {tc['data']}")
        result = format_weather_response(tc["data"])
        print(f"Output: {result}")

    print("\n" + "=" * 60)
