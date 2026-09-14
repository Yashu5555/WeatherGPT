import json
import logging
import os
import re
from dotenv import load_dotenv
from groq import Groq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load RESPONSE_GROQ_API_KEY from .env
load_dotenv()
RESPONSE_GROQ_API_KEY = os.getenv("RESPONSE_GROQ_API_KEY")

SYSTEM_PROMPT = """You are a helpful weather response generator for WeatherGPT.

The FastAPI backend always provides weather data in this JSON format:
{
    "location": "Hyderabad",
    "forecast": [
        {
            "date": "2026-09-13",
            "max_temp": 29.5,
            "min_temp": 23.4,
            "condition": "Cloudy",
            "rain_chance": 20,
            "sunrise": "06:00 AM",
            "sunset": "06:20 PM"
        }
    ]
}

Instructions:
- Answer the user's question using ONLY the provided weather data.
- Read forecast values from the "forecast" list. Do not expect top-level temperature or rain fields.
- Use the relevant forecast item to answer the question.
- Return ONLY a plain text string. Do NOT return JSON, markdown formatting, bold markers (**), or code blocks.
- Do NOT invent or guess missing weather values.
- If the forecast list is empty, state clearly that weather information is currently unavailable.
- If a requested field is missing, clearly say that the information is unavailable.
- Keep responses short, natural, accurate, and directly related to the user's question.

Examples:
- Umbrella question with high rain chance (e.g. 85%):
  "Yes, you should carry an umbrella in Hyderabad because there is an 85% chance of rain."
- Umbrella question with low rain chance (e.g. 20%):
  "An umbrella is probably not necessary in Hyderabad because there is only a 20% chance of rain."
- Umbrella question with missing rain chance:
  "The rain probability is unavailable for Hyderabad, so umbrella advice cannot be confirmed."
- Condition question ("Will it be cloudy in Hyderabad tomorrow?"):
  "Yes, the forecast for Hyderabad tomorrow is cloudy."
- Temperature question ("What is the temperature in Hyderabad tomorrow?"):
  "The temperature in Hyderabad tomorrow is expected to range from 23.4°C to 29.5°C."
- General forecast ("Give me the forecast for Hyderabad."):
  "The forecast for Hyderabad on 2026-09-13 is cloudy, with a high of 29.5°C, a low of 23.4°C, and a 20% chance of rain."
"""


def _fallback_response(question: str, weather_data: dict) -> str:
    """Simple Python fallback for weather formatting adhering to the forecast-list structure."""
    if not weather_data or not isinstance(weather_data, dict):
        return "Sorry, weather information is currently unavailable."

    location = weather_data.get("location", "the requested area")
    forecast = weather_data.get("forecast")

    if not isinstance(forecast, list) or len(forecast) == 0:
        return f"Sorry, weather forecast information is currently unavailable for {location}."

    q_lower = (question or "").lower()

    # Check specific future day request ("after N days", "day after tomorrow", "tomorrow")
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

    # 1. Multi-day forecast request (only if not a specific single-day offset request)
    is_multiday = target_offset == 0 and len(forecast) > 1 and any(
        w in q_lower for w in ["days", "week", "multi", "next 3", "3 day", "3-day", "7 day", "7-day"]
    )
    if is_multiday:
        lines = [f"Forecast for {location}:"]
        for f in forecast:
            if isinstance(f, dict):
                date = f.get("date", "Upcoming")
                cond = f.get("condition")
                max_t = f.get("max_temp")
                min_t = f.get("min_temp")
                rain_c = f.get("rain_chance")

                parts = []
                if cond:
                    parts.append(cond)
                if max_t is not None and min_t is not None:
                    parts.append(f"{max_t}°C / {min_t}°C")
                elif max_t is not None:
                    parts.append(f"High {max_t}°C")
                elif min_t is not None:
                    parts.append(f"Low {min_t}°C")
                if rain_c is not None:
                    parts.append(f"{rain_c}% rain chance")

                detail = ", ".join(parts) if parts else "Data unavailable"
                lines.append(f"- {date}: {detail}")
        return "\n".join(lines)

    # Relevant single-day item
    if target_offset > 0:
        if len(forecast) > target_offset and isinstance(forecast[target_offset], dict) and forecast[target_offset]:
            item = forecast[target_offset]
        else:
            return f"The forecast for {target_label} is unavailable."
    else:
        item = forecast[0] if isinstance(forecast[0], dict) else {}
    date = item.get("date")
    max_temp = item.get("max_temp")
    min_temp = item.get("min_temp")
    condition = item.get("condition")
    rain_chance = item.get("rain_chance")
    sunrise = item.get("sunrise")
    sunset = item.get("sunset")

    if target_label:
        time_frame = f" {target_label}"
    elif "today" in q_lower or "tonight" in q_lower:
        time_frame = " today"
    else:
        time_frame = ""

    # 2. Umbrella advice
    if "umbrella" in q_lower:
        if rain_chance is not None:
            if rain_chance >= 50:
                return f"Yes, you should carry an umbrella in {location} because there is an {rain_chance}% chance of rain."
            return f"An umbrella is probably not necessary in {location} because there is only a {rain_chance}% chance of rain."
        return f"The rain probability is unavailable for {location}, so umbrella advice cannot be confirmed."

    # 3. Rain / Precipitation check
    if any(w in q_lower for w in ["rain", "raining", "rainy", "shower", "storm"]):
        if rain_chance is not None:
            if rain_chance >= 50:
                return f"Yes, there is a high chance of rain ({rain_chance}%) in {location}{time_frame}."
            elif rain_chance > 0:
                return f"There is a {rain_chance}% chance of rain in {location}{time_frame}."
            return f"No rain is expected in {location}{time_frame}."
        return f"Rain information is unavailable for {location}."

    # 4. Specific condition check (e.g. cloudy, sunny)
    condition_keywords = ["cloudy", "sunny", "clear", "rainy", "overcast", "snow", "foggy", "stormy", "partly cloudy"]
    matched_condition = next((w for w in condition_keywords if w in q_lower), None)
    if matched_condition:
        if condition:
            cond_lower = condition.lower()
            if matched_condition in cond_lower:
                return f"Yes, the forecast for {location}{time_frame} is {cond_lower}."
            return f"No, the forecast for {location}{time_frame} is {cond_lower}."
        return f"Condition information is unavailable for {location}."

    # 5. Temperature check
    if any(w in q_lower for w in ["temp", "temperature", "how hot", "how cold", "warm", "cool"]):
        if min_temp is not None and max_temp is not None:
            return f"The temperature in {location}{time_frame} is expected to range from {min_temp}°C to {max_temp}°C."
        elif max_temp is not None:
            return f"The maximum temperature in {location}{time_frame} is expected to be {max_temp}°C."
        elif min_temp is not None:
            return f"The minimum temperature in {location}{time_frame} is expected to be {min_temp}°C."
        return f"Temperature information is unavailable for {location}."

    # 6. Sunrise / Sunset
    if "sunrise" in q_lower:
        if sunrise:
            return f"The sunrise in {location} is expected at {sunrise}."
        return f"Sunrise information is unavailable for {location}."

    if "sunset" in q_lower:
        if sunset:
            return f"The sunset in {location} is expected at {sunset}."
        return f"Sunset information is unavailable for {location}."

    # 7. General forecast summary
    date_str = f" on {date}" if date else ""
    cond_str = f" is {condition.lower()}" if condition else ""
    temp_parts = []
    if max_temp is not None:
        temp_parts.append(f"a high of {max_temp}°C")
    if min_temp is not None:
        temp_parts.append(f"a low of {min_temp}°C")
    if rain_chance is not None:
        temp_parts.append(f"a {rain_chance}% chance of rain")

    if condition and temp_parts:
        return f"The forecast for {location}{date_str}{cond_str}, with {', '.join(temp_parts)}."
    elif condition:
        return f"The forecast for {location}{date_str}{cond_str}."
    elif temp_parts:
        return f"The forecast for {location}{date_str} includes {', '.join(temp_parts)}."

    return f"Sorry, weather information is currently unavailable for {location}."


def format_weather_response(question: str, weather_data: dict) -> str:
    """Format weather data into a natural-language response using Groq API or Python fallback."""
    if not RESPONSE_GROQ_API_KEY:
        return _fallback_response(question, weather_data)

    try:
        client = Groq(api_key=RESPONSE_GROQ_API_KEY)
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"User question: {question}\n"
                        f"Weather data: {json.dumps(weather_data)}"
                    )
                }
            ],
            temperature=0.3
        )
        if response and response.choices:
            content = response.choices[0].message.content
            if content and content.strip():
                return content.strip()
    except Exception as e:
        logger.exception("Groq response formatter failed: %s", e)

    return _fallback_response(question, weather_data)


if __name__ == "__main__":
    print("=== Test 1: Full forecast data ===")
    q1 = "Give me the forecast for Hyderabad."
    d1 = {
        "location": "Hyderabad",
        "forecast": [
            {
                "date": "2026-09-13",
                "max_temp": 29.5,
                "min_temp": 23.4,
                "condition": "Cloudy",
                "rain_chance": 20,
                "sunrise": "06:00 AM",
                "sunset": "06:20 PM"
            }
        ]
    }
    print("Question:", q1)
    print("Response:", format_weather_response(q1, d1))

    print("\n=== Test 2: Partial forecast data ===")
    q2 = "What is the temperature in Hyderabad tomorrow?"
    d2 = {
        "location": "Hyderabad",
        "forecast": [
            {
                "date": "2026-09-14",
                "max_temp": 29.5,
                "min_temp": 23.4
            }
        ]
    }
    print("Question:", q2)
    print("Response:", format_weather_response(q2, d2))

    print("\n=== Test 3: Empty forecast list ===")
    q3 = "What is the forecast for Hyderabad?"
    d3 = {
        "location": "Hyderabad",
        "forecast": []
    }
    print("Question:", q3)
    print("Response:", format_weather_response(q3, d3))

    print("\n=== Test 4: High rain chance umbrella question ===")
    q4 = "Should I carry an umbrella in Hyderabad?"
    d4 = {
        "location": "Hyderabad",
        "forecast": [
            {
                "date": "2026-09-13",
                "max_temp": 28.0,
                "min_temp": 22.0,
                "condition": "Rainy",
                "rain_chance": 85,
                "sunrise": "06:00 AM",
                "sunset": "06:20 PM"
            }
        ]
    }
    print("Question:", q4)
    print("Response:", format_weather_response(q4, d4))

    print("\n=== Test 5: Low rain chance umbrella question ===")
    q5 = "Should I carry an umbrella in Hyderabad?"
    d5 = {
        "location": "Hyderabad",
        "forecast": [
            {
                "date": "2026-09-13",
                "max_temp": 29.5,
                "min_temp": 23.4,
                "condition": "Cloudy",
                "rain_chance": 20,
                "sunrise": "06:00 AM",
                "sunset": "06:20 PM"
            }
        ]
    }
    print("Question:", q5)
    print("Response:", format_weather_response(q5, d5))

    print("\n=== Test 6: Missing rain chance ===")
    q6 = "Should I carry an umbrella in Hyderabad?"
    d6 = {
        "location": "Hyderabad",
        "forecast": [
            {
                "date": "2026-09-13",
                "max_temp": 29.5,
                "min_temp": 23.4,
                "condition": "Cloudy"
            }
        ]
    }
    print("Question:", q6)
    print("Response:", format_weather_response(q6, d6))

