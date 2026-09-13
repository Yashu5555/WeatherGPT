import json
import os
import re
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


SYSTEM_PROMPT = """
You are the query parser for WeatherGPT.

Your ONLY job is to understand the user's weather question and convert it
into a structured JSON object.

You MUST NOT answer the weather question.
You MUST NOT invent or predict weather values.
You MUST NOT provide temperature, rainfall, humidity, wind or any other
weather data.

Use ONLY these two intents:
- "current_weather" : current conditions or today's weather
- "weather_forecast" : future weather, tomorrow, a future date, or
  multi-day forecasts

Extract:
1. intent
2. location
3. date OR days

Rules:

- For current weather:
{
    "intent": "current_weather",
    "location": "Hyderabad",
    "date": "today"
}

- For future single-day weather:
{
    "intent": "weather_forecast",
    "location": "Hyderabad",
    "date": "tomorrow"
}

- For a multi-day forecast:
{
    "intent": "weather_forecast",
    "location": "Chennai",
    "days": 3
}

- Questions about rain, temperature, humidity, wind, clouds, sunshine,
  umbrellas, jackets, travel, picnics, etc. do NOT create new intents.
  They must use either current_weather or weather_forecast.

- If the user says "tonight", use:
  "date": "tonight"

- If the user says "today", use:
  "date": "today"

- If the user says "tomorrow", use:
  "date": "tomorrow"

- If the user says "day after tomorrow", use:
  "date": "day after tomorrow"

- If the user asks for a number of days, return an integer in "days".

- If the location is missing, return:
{
    "error": "Location not found in the question."
}

- If the question is unrelated to weather, return:
{
    "error": "This question is not related to weather."
}

- Return ONLY valid JSON.
- Do NOT return markdown.
- Do NOT return explanations.
"""


def _clean_and_parse_json(content: str) -> Optional[Dict[str, Any]]:
    """Convert the LLM response into a Python dictionary."""

    if not content:
        return None

    cleaned = content.strip()

    # Remove markdown code fences if the model returns them
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    try:
        data = json.loads(cleaned)

        if isinstance(data, dict):
            return data

    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    return None


def _validate_llm_result(
    result: Optional[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Validate the JSON returned by the LLM before passing it
    to the backend.
    """

    if not isinstance(result, dict):
        return None

    # Valid error responses
    if "error" in result:
        if result["error"] in {
            "Location not found in the question.",
            "This question is not related to weather."
        }:
            return {"error": result["error"]}

        return None

    # Validate intent
    intent = result.get("intent")

    if intent not in {"current_weather", "weather_forecast"}:
        return None

    # Validate location
    location = result.get("location")

    if not isinstance(location, str) or not location.strip():
        return None

    location = location.strip()

    # Validate multi-day forecast
    if "days" in result:

        days = result["days"]

        if not isinstance(days, int) or isinstance(days, bool):
            return None

        if days < 1 or days > 14:
            return None

        return {
            "intent": "weather_forecast",
            "location": location,
            "days": days
        }

    # Validate date
    date = result.get("date")

    if not isinstance(date, str) or not date.strip():
        return None

    date = date.strip().lower()

    allowed_dates = {
        "today",
        "tonight",
        "tomorrow",
        "day after tomorrow",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday"
    }

    if date not in allowed_dates:
        return None

    return {
        "intent": intent,
        "location": location.title(),
        "date": date
    }


def _parse_with_groq(query: str) -> Optional[Dict[str, Any]]:
    """Parse the weather query using Groq LLM."""

    if not GROQ_API_KEY:
        return None

    try:
        from groq import Groq

        client = Groq(api_key=GROQ_API_KEY)

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content

        result = _clean_and_parse_json(content)

        return _validate_llm_result(result)

    except Exception as e:
        print(f"Groq parser unavailable: {e}")
        return None


def _parse_rule_based(query: str) -> Dict[str, Any]:
    """Fallback parser used when the Groq API is unavailable."""

    if not query or not query.strip():
        return {
            "error": "Empty question provided."
        }

    text = query.strip()

    # Fix common spelling mistake
    text = re.sub(
        r"\btommorow\b",
        "tomorrow",
        text,
        flags=re.IGNORECASE
    )

    lower = text.lower()

    # 1. Check weather relevance
    weather_keywords = [
        "weather",
        "forecast",
        "temperature",
        "temp",
        "rain",
        "raining",
        "rainfall",
        "rainy",
        "snow",
        "snowing",
        "climate",
        "sunny",
        "sunshine",
        "clear",
        "cloud",
        "clouds",
        "cloudy",
        "overcast",
        "wind",
        "windy",
        "breeze",
        "humidity",
        "humid",
        "hot",
        "cold",
        "warm",
        "cool",
        "umbrella",
        "raincoat",
        "jacket",
        "storm",
        "shower",
        "picnic",
        "outdoor",
        "outside",
        "travel",
        "trip",
        "drive"
    ]

    if not any(word in lower for word in weather_keywords):
        return {
            "error": "This question is not related to weather."
        }

    # 2. Extract number of days
    days = None

    days_match = re.search(
        r"\b(?:for\s+|next\s+)?(\d+)\s*days?\b",
        lower
    )

    if days_match:
        days = int(days_match.group(1))

        if days < 1 or days > 14:
            return {
                "error": "Forecast is currently supported for up to 14 days."
            }

    # 3. Extract date
    date_patterns = [
        "day after tomorrow",
        "tomorrow",
        "today",
        "tonight",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday"
    ]

    date_regex = (
        r"\b("
        + "|".join(re.escape(x) for x in date_patterns)
        + r")\b"
    )

    date_match = re.search(
        date_regex,
        lower
    )

    date = date_match.group(1) if date_match else "today"

    # 4. Clean text before location extraction
    clean_text = re.sub(
        r"\b(?:for\s+|next\s+)?"
        r"(?:\d+)\s*days?\b",
        " ",
        text,
        flags=re.IGNORECASE
    )

    clean_text = re.sub(
        date_regex,
        " ",
        clean_text,
        flags=re.IGNORECASE
    )

    clean_text = re.sub(
        r"[?.!,;:]",
        " ",
        clean_text
    )

    # 5. Stop words
    stop_words = {
        "in", "at", "near", "around", "for", "of",
        "the", "a", "an", "is", "are", "was", "were",
        "what", "whats", "what's", "how", "hows", "how's",
        "where", "wheres", "where's",
        "tell", "me", "show", "give", "will", "it",
        "its", "it's", "weather", "forecast",
        "temperature", "temp", "rain", "raining",
        "rainfall", "rainy", "sunny", "sunshine",
        "cloud", "clouds", "cloudy", "wind", "windy",
        "humidity", "humid", "hot", "cold", "warm",
        "cool", "today", "tomorrow", "should",
        "i", "carry", "umbrella", "can", "you",
        "please", "current", "currently", "check",
        "is", "there", "going", "to", "be",
        "day", "next", "week", "good",
        "for", "plan", "planning", "travel",
        "trip", "drive", "outside", "outdoor"
    }

    def clean_location(value: str) -> Optional[str]:
        words = []

        for word in value.split():
            cleaned_word = word.strip("'\"")

            if (
                cleaned_word
                and cleaned_word.lower() not in stop_words
                and not cleaned_word.isdigit()
            ):
                words.append(cleaned_word)

        if words:
            return " ".join(words).title()

        return None

    location = None

    # 6. Possessive pattern
    # Example: "Chennai's forecast"
    possessive_match = re.search(
        r"\b([a-zA-Z]+(?:\s+[a-zA-Z]+){0,4})['’]s\b",
        clean_text
    )

    if possessive_match:
        location = clean_location(
            possessive_match.group(1)
        )

    # 7. Preposition pattern
    # Example: "weather in Hyderabad"
    if not location:
        prep_match = re.search(
            r"\b(?:in|at|near|around)\s+"
            r"([a-zA-Z]+(?:\s+[a-zA-Z]+){0,4})",
            clean_text,
            re.IGNORECASE
        )

        if prep_match:
            location = clean_location(
                prep_match.group(1)
            )

    # 8. Direct pattern
    # Example: "Hyderabad weather"
    if not location:
        direct_match = re.search(
            r"^\s*"
            r"([a-zA-Z]+(?:\s+[a-zA-Z]+){0,4})"
            r"\s+"
            r"(?:weather|forecast|temp|temperature)\b",
            clean_text,
            re.IGNORECASE
        )

        if direct_match:
            location = clean_location(
                direct_match.group(1)
            )

    # 9. Fallback location extraction
    if not location:
        words = []

        for word in clean_text.split():
            cleaned_word = word.strip("'\"")

            if (
                cleaned_word
                and cleaned_word.lower() not in stop_words
                and not cleaned_word.isdigit()
            ):
                words.append(cleaned_word)

        if words:
            location = " ".join(words).title()

    # 10. Location missing
    if not location:
        return {
            "error": "Location not found in the question."
        }

    # 11. Determine intent
    future_keywords = [
        "tomorrow",
        "tonight",
        "day after tomorrow",
        "next",
        "upcoming",
        "will it",
        "going to",
        "expected",
        "forecast",
        "prediction",
        "predict",
        "picnic",
        "travel",
        "trip",
        "drive",
        "outdoor",
        "outside",
        "plan",
        "planning"
    ]

    if (
        days is not None
        or any(word in lower for word in future_keywords)
    ):
        return {
            "intent": "weather_forecast",
            "location": location,
            "days": days if days is not None else 1
        }

    return {
        "intent": "current_weather",
        "location": location,
        "date": date
    }


def parse_weather_query(query: str) -> Dict[str, Any]:
    """
    Parse a weather question using Groq first,
    then fall back to rule-based parsing.
    """

    # Try LLM parser first
    groq_result = _parse_with_groq(query)

    if groq_result is not None:
        return groq_result

    # Fallback
    return _parse_rule_based(query)


if __name__ == "__main__":

    test_queries = [
        "What's the weather in Hyderabad?",
        "What's the temperature in Mumbai?",
        "Will it rain in Delhi tomorrow?",
        "What's the weather in Hyderabad tonight?",
        "Give me Chennai's forecast for 3 days.",
        "Weather in New York City tomorrow",
        "Should I carry an umbrella in Hyderabad tomorrow?",
        "Should I use sunscreen today in Hyderabad?",
        "Weather Hyderabad",
        "Hyderabad weather",
        "Weather Hyderabad for 7 days",
        "Hello",
        "What's the weather?"
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")

        result = parse_weather_query(query)

        print(
            "Result:",
            json.dumps(result, indent=2)
        )
