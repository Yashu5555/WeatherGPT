import json
import logging
import os
import re
from datetime import date, timedelta

from dotenv import load_dotenv
from groq import Groq


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
RESPONSE_GROQ_API_KEY = os.getenv("RESPONSE_GROQ_API_KEY")


SYSTEM_PROMPT = """You are a helpful weather response generator for WeatherGPT.

The backend provides current weather, forecast, or tonight's hourly weather data.

Current weather may contain:
- location
- temperature
- humidity
- condition
- wind_speed
- rain_chance
- feeling_like
- uv

Forecast data may contain:
- date
- max_temp
- min_temp
- condition
- rain_chance
- uv
- sunrise
- sunset

Tonight data may contain:
- time
- temperature
- condition
- rain_chance
- wind_speed

Rules:
- Answer ONLY using the provided weather data.
- Never invent weather values.
- Keep answers short, natural and directly related to the question.
- Do not return JSON, markdown or code blocks.
- For UV questions, use the provided UV value.
- For sunscreen questions, explain that sunscreen is generally useful when UV is elevated, but do not invent a UV value.
- For tonight questions, use hourly tonight data when available.
- For weekend questions, summarize the available weekend forecast.
- For "after N days", use the forecast entry for that actual future date.
- Do not claim information that is missing.
"""


def _find_forecast_item(forecast, target_offset):
    """Find a forecast entry using its actual calendar date."""

    target_date = date.today() + timedelta(days=target_offset)

    for item in forecast:
        if not isinstance(item, dict):
            continue

        forecast_date = item.get("date")

        if not forecast_date:
            continue

        try:
            if date.fromisoformat(forecast_date) == target_date:
                return item
        except ValueError:
            continue

    return None


def _format_uv_advice(location, uv, question):
    """Answer UV and sunscreen questions using the available UV value."""

    if uv is None:
        return f"UV information is unavailable for {location}."

    if "sunscreen" in question or "sun protection" in question:
        if uv >= 8:
            return (
                f"Yes, you should use sunscreen in {location}. "
                f"The UV index is {uv}, which is very high."
            )

        if uv >= 6:
            return (
                f"Yes, sunscreen is recommended in {location}. "
                f"The UV index is {uv}, which is high."
            )

        if uv >= 3:
            return (
                f"Sunscreen is a good idea in {location}. "
                f"The UV index is {uv}, which is moderate."
            )

        return (
            f"The UV index in {location} is {uv}, so UV exposure is currently low."
        )

    return f"The current UV index in {location} is {uv}."


def _fallback_response(question: str, weather_data: dict) -> str:

    if not weather_data or not isinstance(weather_data, dict):
        return "Sorry, weather information is currently unavailable."

    location = weather_data.get("location", "the requested area")
    q_lower = (question or "").lower()

    if weather_data.get("type") == "current":

        temperature = weather_data.get("temperature")
        humidity = weather_data.get("humidity")
        condition = weather_data.get("condition")
        wind_speed = weather_data.get("wind_speed")
        rain_chance = weather_data.get("rain_chance")
        feeling_like = weather_data.get("feeling_like")
        uv = weather_data.get("uv")

        # UV / sunscreen
        if "uv" in q_lower or "sunscreen" in q_lower or "sun protection" in q_lower:
            return _format_uv_advice(location, uv, q_lower)

        # Umbrella
        if "umbrella" in q_lower:

            if rain_chance is not None:

                if rain_chance >= 50:
                    return (
                        f"Yes, you should carry an umbrella in {location} "
                        f"because there is a {rain_chance}% chance of rain."
                    )

                return (
                    f"An umbrella is probably not necessary in {location} "
                    f"because there is only a {rain_chance}% chance of rain."
                )

            return (
                f"The rain probability is unavailable for {location}, "
                f"so umbrella advice cannot be confirmed."
            )

        # Rain
        if any(
            word in q_lower
            for word in ["rain", "raining", "rainy", "shower", "storm"]
        ):

            if rain_chance is not None:

                if rain_chance >= 50:
                    return (
                        f"Yes, there is a high chance of rain "
                        f"({rain_chance}%) in {location} right now."
                    )

                if rain_chance > 0:
                    return (
                        f"There is a {rain_chance}% chance of rain "
                        f"in {location} right now."
                    )

                return f"No rain is expected in {location} right now."

            return f"Rain information is unavailable for {location}."

        # Temperature
        if any(
            word in q_lower
            for word in [
                "temp",
                "temperature",
                "how hot",
                "how cold",
                "warm",
                "cool",
            ]
        ):

            if temperature is not None:
                return f"The current temperature in {location} is {temperature}°C."

            return f"Temperature information is unavailable for {location}."

        # Humidity
        if "humidity" in q_lower:

            if humidity is not None:
                return f"The current humidity in {location} is {humidity}%."

            return f"Humidity information is unavailable for {location}."

        # Wind
        if any(word in q_lower for word in ["wind", "windy"]):

            if wind_speed is not None:
                return (
                    f"The current wind speed in {location} "
                    f"is {wind_speed} km/h."
                )

            return f"Wind information is unavailable for {location}."

        # Feels like
        if "feels like" in q_lower or "feeling like" in q_lower:

            if feeling_like is not None:
                return (
                    f"It feels like {feeling_like}°C "
                    f"in {location} right now."
                )

            return (
                f"Feels-like temperature information is unavailable "
                f"for {location}."
            )

        # General current weather
        parts = []

        if temperature is not None:
            parts.append(f"{temperature}°C")

        if condition:
            parts.append(condition.lower())

        if rain_chance is not None:
            parts.append(f"{rain_chance}% chance of rain")

        if parts:
            return f"The current weather in {location} is " + ", ".join(parts) + "."

        return f"Current weather information for {location} is unavailable."

    if weather_data.get("type") == "tonight":

        tonight = weather_data.get("tonight")

        if not isinstance(tonight, list) or not tonight:
            return f"Tonight's weather information is unavailable for {location}."

        temperatures = [
            item.get("temperature")
            for item in tonight
            if isinstance(item, dict)
            and item.get("temperature") is not None
        ]

        rain_chances = [
            item.get("rain_chance")
            for item in tonight
            if isinstance(item, dict)
            and item.get("rain_chance") is not None
        ]

        conditions = [
            item.get("condition")
            for item in tonight
            if isinstance(item, dict)
            and item.get("condition")
        ]

        # Jacket / cold questions
        if any(
            word in q_lower
            for word in ["jacket", "cold", "warm", "clothes", "wear"]
        ):

            if temperatures:

                low = min(temperatures)
                high = max(temperatures)

                if low <= 15:
                    advice = "Yes, a jacket would be a good idea."
                elif low <= 20:
                    advice = "A light jacket may be useful."
                else:
                    advice = "A jacket probably won't be necessary."

                return (
                    f"{advice} Tonight in {location}, temperatures are "
                    f"expected to range from {low}°C to {high}°C."
                )

            return f"Tonight's temperature information is unavailable for {location}."

        # Rain / umbrella
        if "umbrella" in q_lower or "rain" in q_lower:

            if rain_chances:
                rain = max(rain_chances)

                if rain >= 50:
                    return (
                        f"Carry an umbrella tonight in {location}; "
                        f"the rain chance reaches {rain}%."
                    )

                return (
                    f"Rain chances are relatively low tonight in {location}, "
                    f"with a maximum chance of {rain}%."
                )

            return f"Tonight's rain information is unavailable for {location}."

        # Wind
        if "wind" in q_lower or "windy" in q_lower:

            winds = [
                item.get("wind_speed")
                for item in tonight
                if isinstance(item, dict)
                and item.get("wind_speed") is not None
            ]

            if winds:
                return (
                    f"Tonight's wind speed in {location} "
                    f"will range from {min(winds)} to {max(winds)} km/h."
                )

            return f"Tonight's wind information is unavailable for {location}."

        # General tonight response
        parts = []

        if temperatures:
            parts.append(
                f"temperatures from {min(temperatures)}°C "
                f"to {max(temperatures)}°C"
            )

        if conditions:
            parts.append(f"mostly {conditions[0].lower()}")

        if rain_chances:
            parts.append(f"up to {max(rain_chances)}% chance of rain")

        if parts:
            return f"Tonight in {location}, expect " + ", ".join(parts) + "."

        return f"Tonight's weather information is unavailable for {location}."

    forecast = weather_data.get("forecast")

    if not isinstance(forecast, list) or not forecast:
        return (
            f"Sorry, weather forecast information is currently "
            f"unavailable for {location}."
        )

    after_match = re.search(r"\bafter\s+(\d+)\s*days?\b", q_lower)

    if after_match:

        target_offset = int(after_match.group(1))
        target_label = f"after {target_offset} days"

    elif "day after tomorrow" in q_lower:

        target_offset = 2
        target_label = "the day after tomorrow"

    elif "tomorrow" in q_lower:

        target_offset = 1
        target_label = "tomorrow"

    else:

        target_offset = 0
        target_label = None

    if "weekend" in q_lower:

        weekend_items = []

        for item in forecast:

            if not isinstance(item, dict):
                continue

            item_date = item.get("date")

            if not item_date:
                continue

            try:
                weekday = date.fromisoformat(item_date).weekday()

                # Saturday = 5, Sunday = 6
                if weekday in [5, 6]:
                    weekend_items.append(item)

            except ValueError:
                continue

        if not weekend_items:
            return f"Weekend forecast information is unavailable for {location}."

        rain_values = [
            item.get("rain_chance")
            for item in weekend_items
            if item.get("rain_chance") is not None
        ]

        conditions = [
            item.get("condition")
            for item in weekend_items
            if item.get("condition")
        ]

        if rain_values:

            highest_rain = max(rain_values)

            if highest_rain >= 50:
                return (
                    f"There is a high chance of rain this weekend in "
                    f"{location}, reaching {highest_rain}%."
                )

            return (
                f"Rain chances this weekend in {location} "
                f"reach {highest_rain}%."
            )

        if conditions:
            return (
                f"This weekend in {location}, the forecast is "
                f"{conditions[0].lower()}."
            )

        return f"Weekend forecast information is unavailable for {location}."

    is_multiday = (
        target_offset == 0
        and len(forecast) > 1
        and any(
            word in q_lower
            for word in [
                "days",
                "week",
                "multi",
                "next 3",
                "3 day",
                "3-day",
                "7 day",
                "7-day",
            ]
        )
    )

    if is_multiday:

        lines = [f"Forecast for {location}:"]

        for item in forecast:

            if not isinstance(item, dict):
                continue

            item_date = item.get("date", "Upcoming")
            condition = item.get("condition")
            max_temp = item.get("max_temp")
            min_temp = item.get("min_temp")
            rain_chance = item.get("rain_chance")

            parts = []

            if condition:
                parts.append(condition)

            if max_temp is not None and min_temp is not None:
                parts.append(f"{max_temp}°C / {min_temp}°C")

            if rain_chance is not None:
                parts.append(f"{rain_chance}% rain chance")

            detail = ", ".join(parts) if parts else "Data unavailable"

            lines.append(f"- {item_date}: {detail}")

        return "\n".join(lines)

    if target_offset > 0:

        item = _find_forecast_item(forecast, target_offset)

        if item is None:
            return f"The forecast for {target_label} is unavailable."

    else:

        item = forecast[0] if isinstance(forecast[0], dict) else {}

    item_date = item.get("date")
    max_temp = item.get("max_temp")
    min_temp = item.get("min_temp")
    condition = item.get("condition")
    rain_chance = item.get("rain_chance")
    uv = item.get("uv")
    sunrise = item.get("sunrise")
    sunset = item.get("sunset")

    if target_label:
        time_frame = f" {target_label}"
    elif "today" in q_lower:
        time_frame = " today"
    else:
        time_frame = ""

    if "uv" in q_lower or "sunscreen" in q_lower or "sun protection" in q_lower:
        return _format_uv_advice(location, uv, q_lower)

    if "umbrella" in q_lower:

        if rain_chance is not None:

            if rain_chance >= 50:
                return (
                    f"Yes, you should carry an umbrella in {location} "
                    f"because there is a {rain_chance}% chance of rain."
                )

            return (
                f"An umbrella is probably not necessary in {location} "
                f"because there is only a {rain_chance}% chance of rain."
            )

        return (
            f"The rain probability is unavailable for {location}, "
            f"so umbrella advice cannot be confirmed."
        )

    if any(
        word in q_lower
        for word in ["rain", "raining", "rainy", "shower", "storm"]
    ):

        if rain_chance is not None:

            if rain_chance >= 50:
                return (
                    f"Yes, there is a high chance of rain "
                    f"({rain_chance}%) in {location}{time_frame}."
                )

            if rain_chance > 0:
                return (
                    f"There is a {rain_chance}% chance of rain "
                    f"in {location}{time_frame}."
                )

            return f"No rain is expected in {location}{time_frame}."

        return f"Rain information is unavailable for {location}."

    condition_keywords = [
        "cloudy",
        "sunny",
        "clear",
        "rainy",
        "overcast",
        "snow",
        "foggy",
        "stormy",
        "partly cloudy",
    ]

    matched_condition = next(
        (word for word in condition_keywords if word in q_lower),
        None,
    )

    if matched_condition:

        if condition:

            condition_lower = condition.lower()

            if matched_condition in condition_lower:
                return (
                    f"Yes, the forecast for {location}{time_frame} "
                    f"is {condition_lower}."
                )

            return (
                f"No, the forecast for {location}{time_frame} "
                f"is {condition_lower}."
            )

        return f"Condition information is unavailable for {location}."

    if any(
        word in q_lower
        for word in [
            "temp",
            "temperature",
            "how hot",
            "how cold",
            "warm",
            "cool",
        ]
    ):

        if min_temp is not None and max_temp is not None:
            return (
                f"The temperature in {location}{time_frame} "
                f"is expected to range from {min_temp}°C to {max_temp}°C."
            )

        if max_temp is not None:
            return (
                f"The maximum temperature in {location}{time_frame} "
                f"is expected to be {max_temp}°C."
            )

        if min_temp is not None:
            return (
                f"The minimum temperature in {location}{time_frame} "
                f"is expected to be {min_temp}°C."
            )

        return f"Temperature information is unavailable for {location}."

    if "sunrise" in q_lower:

        if sunrise:
            return f"The sunrise in {location} is expected at {sunrise}."

        return f"Sunrise information is unavailable for {location}."

    if "sunset" in q_lower:

        if sunset:
            return f"The sunset in {location} is expected at {sunset}."

        return f"Sunset information is unavailable for {location}."

    date_str = f" on {item_date}" if item_date else ""

    condition_str = (
        f" is {condition.lower()}"
        if condition
        else ""
    )

    parts = []

    if max_temp is not None:
        parts.append(f"a high of {max_temp}°C")

    if min_temp is not None:
        parts.append(f"a low of {min_temp}°C")

    if rain_chance is not None:
        parts.append(f"a {rain_chance}% chance of rain")

    if condition and parts:
        return (
            f"The forecast for {location}{date_str}{condition_str}, "
            f"with {', '.join(parts)}."
        )

    if condition:
        return f"The forecast for {location}{date_str}{condition_str}."

    if parts:
        return (
            f"The forecast for {location}{date_str} "
            f"includes {', '.join(parts)}."
        )

    return f"Sorry, weather information is currently unavailable for {location}."


def format_weather_response(question: str, weather_data: dict) -> str:
    """Generate a natural-language weather response."""

    if not RESPONSE_GROQ_API_KEY:
        return _fallback_response(question, weather_data)

    try:

        client = Groq(api_key=RESPONSE_GROQ_API_KEY)

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        f"User question: {question}\n"
                        f"Weather data: {json.dumps(weather_data)}"
                    ),
                },
            ],
            temperature=0.3,
        )

        if response and response.choices:

            content = response.choices[0].message.content

            if content and content.strip():
                return content.strip()

    except Exception as e:
        logger.exception(
            "Groq response formatter failed: %s",
            e,
        )

    return _fallback_response(question, weather_data)


if __name__ == "__main__":

    tests = [
        (
            "Should I use sunscreen today in Hyderabad?",
            {
                "type": "current",
                "location": "Hyderabad",
                "temperature": 28.4,
                "humidity": 51,
                "condition": "Overcast",
                "wind_speed": 11.9,
                "rain_chance": 11,
                "feeling_like": 29.0,
                "uv": 0.6,
            },
        ),
        (
            "Do I need a jacket tonight in Hyderabad?",
            {
                "type": "tonight",
                "location": "Hyderabad",
                "tonight": [
                    {
                        "time": "2026-09-15 18:00",
                        "temperature": 26.9,
                        "condition": "Clear",
                        "rain_chance": 4,
                        "wind_speed": 10.4,
                    },
                    {
                        "time": "2026-09-15 23:00",
                        "temperature": 24.0,
                        "condition": "Partly Cloudy",
                        "rain_chance": 10,
                        "wind_speed": 11.2,
                    },
                ],
            },
        ),
    ]

    for question, data in tests:

        print("\nQuestion:", question)
        print("Response:", format_weather_response(question, data))

