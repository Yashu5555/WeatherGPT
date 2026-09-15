import json
import os
import re
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


SYSTEM_PROMPT = """
You are the query parser for WeatherGPT.

Your ONLY job is to understand the user's weather question and return
a structured JSON object.

You MUST NOT answer the weather question.
You MUST NOT invent weather values.

Use only these intents:
- "current_weather"
- "weather_forecast"

Rules:

1. Current weather questions use current_weather.

Examples:
"Is it hot outside in Hyderabad?"
"What is the weather in Hyderabad?"
"How windy is it right now in Hyderabad?"
"Should I use sunscreen today in Hyderabad?"

Return:
{
    "intent": "current_weather",
    "location": "Hyderabad",
    "date": "today"
}

2. Future weather questions use weather_forecast.

Examples:
"Will it rain tomorrow in Hyderabad?"
"Do I need a jacket tonight in Hyderabad?"
"Will it rain this weekend in Hyderabad?"

3. "after N days" means one specific future day.

Example:
"What will the weather be like after 5 days in Hyderabad?"

Return:
{
    "intent": "weather_forecast",
    "location": "Hyderabad",
    "date": "after_days",
    "days": 5
}

4. "next N days" or "for N days" means a multi-day forecast.

Example:
"What will the weather be like for the next 5 days in Hyderabad?"

Return:
{
    "intent": "weather_forecast",
    "location": "Hyderabad",
    "days": 5
}

5. "this weekend" must return date "this_weekend".

6. "tonight" must return date "tonight".

7. "tomorrow" must return date "tomorrow".

8. "day after tomorrow" must return date "day after tomorrow".

9. Questions about temperature, rain, humidity, wind, clouds,
sunshine, sunscreen, UV, umbrellas, jackets, picnics, travel,
etc. do NOT create new intents.

10. Words such as "hot", "cold", "windy", "humid", "sunny",
"cloudy", "rainy" and "outside" do NOT automatically mean
future weather.

11. If location is missing, return:
{
    "error": "Location not found in the question."
}

12. If unrelated to weather, return:
{
    "error": "This question is not related to weather."
}

Return ONLY valid JSON.
"""


def _clean_and_parse_json(
    content: str
) -> Optional[Dict[str, Any]]:

    if not content:
        return None

    cleaned = content.strip()

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

    if not isinstance(result, dict):
        return None

    if "error" in result:

        if result["error"] in {
            "Location not found in the question.",
            "This question is not related to weather."
        }:
            return {"error": result["error"]}

        return None

    intent = result.get("intent")

    if intent not in {
        "current_weather",
        "weather_forecast"
    }:
        return None

    location = result.get("location")

    if not isinstance(location, str) or not location.strip():
        return None

    location = location.strip().title()

    if "days" in result:

        days = result["days"]

        if not isinstance(days, int) or isinstance(days, bool):
            return None

        if days < 1 or days > 14:
            return None

        if result.get("date") == "after_days":
            return {
                "intent": "weather_forecast",
                "location": location,
                "date": "after_days",
                "days": days
            }

        return {
            "intent": "weather_forecast",
            "location": location,
            "days": days
        }

    date = result.get("date")

    if not isinstance(date, str):
        return None

    date = date.strip().lower()

    allowed_dates = {
        "today",
        "tonight",
        "tomorrow",
        "day after tomorrow",
        "this_weekend",
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
        "location": location,
        "date": date
    }


def _parse_with_groq(
    query: str
) -> Optional[Dict[str, Any]]:

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


def _parse_rule_based(
    query: str
) -> Dict[str, Any]:

    if not query or not query.strip():
        return {
            "error": "Empty question provided."
        }

    text = query.strip()

    text = re.sub(
        r"\btommorow\b",
        "tomorrow",
        text,
        flags=re.IGNORECASE
    )

    lower = text.lower()

    # Weather relevance
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
        "sunscreen",
        "uv",
        "ultraviolet",
        "sun protection",
        "sunburn",
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

    if not any(
        word in lower for word in weather_keywords
    ):
        return {
            "error": "This question is not related to weather."
        }

    # "after N days" MUST be checked first
    after_days_match = re.search(
        r"\bafter\s+(\d+)\s*days?\b",
        lower
    )

    if after_days_match:

        days = int(after_days_match.group(1))

        if days < 1 or days > 14:
            return {
                "error":
                "Forecast is currently supported for up to 14 days."
            }

    else:

        # Only "next N days" / "for N days"
        days_match = re.search(
            r"\b(?:for\s+|next\s+)(\d+)\s*days?\b",
            lower
        )

        days = None

        if days_match:

            days = int(days_match.group(1))

            if days < 1 or days > 14:
                return {
                    "error":
                    "Forecast is currently supported for up to 14 days."
                }

    # Dates
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
        + "|".join(
            re.escape(x)
            for x in date_patterns
        )
        + r")\b"
    )

    date_match = re.search(
        date_regex,
        lower
    )

    date = (
        date_match.group(1)
        if date_match
        else "today"
    )

    # Clean text for location extraction
    clean_text = re.sub(
        r"\bafter\s+\d+\s*days?\b",
        " ",
        text,
        flags=re.IGNORECASE
    )

    clean_text = re.sub(
        r"\b(?:for\s+|next\s+)\d+\s*days?\b",
        " ",
        clean_text,
        flags=re.IGNORECASE
    )

    clean_text = re.sub(
        date_regex,
        " ",
        clean_text,
        flags=re.IGNORECASE
    )

    clean_text = re.sub(
        r"\bthis\s+weekend\b",
        " ",
        clean_text,
        flags=re.IGNORECASE
    )

    clean_text = re.sub(
        r"[?.!,;:]",
        " ",
        clean_text
    )

    # Words that should NOT become part of location
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
        "cool", "should", "i", "carry", "umbrella",
        "can", "you", "please", "current", "currently",
        "right", "now", "moment", "present", "check",
        "there", "going", "to", "be", "day", "next",
        "week", "good", "plan", "planning", "travel",
        "trip", "drive", "outside", "outdoor", "picnic",
        "use", "sunscreen", "uv", "ultraviolet",
        "jacket", "need"
    }

    def clean_location(
        value: str
    ) -> Optional[str]:

        words = []

        for word in value.split():

            cleaned_word = word.strip("'\"")

            if (
                cleaned_word
                and cleaned_word.lower()
                not in stop_words
                and not cleaned_word.isdigit()
            ):
                words.append(cleaned_word)

        if words:
            return " ".join(words).title()

        return None

    location = None

    # Possessive
    possessive_match = re.search(
        r"\b([a-zA-Z]+(?:\s+[a-zA-Z]+){0,4})['’]s\b",
        clean_text
    )

    if possessive_match:

        location = clean_location(
            possessive_match.group(1)
        )

    # Preposition
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

    # Direct pattern
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

    # Fallback
    if not location:

        words = []

        for word in clean_text.split():

            cleaned_word = word.strip("'\"")

            if (
                cleaned_word
                and cleaned_word.lower()
                not in stop_words
                and not cleaned_word.isdigit()
            ):
                words.append(cleaned_word)

        if words:
            location = " ".join(words).title()

    if not location:

        return {
            "error": "Location not found in the question."
        }

    # Intent
    if after_days_match:

        return {
            "intent": "weather_forecast",
            "location": location,
            "date": "after_days",
            "days": days
        }

    if days is not None:

        return {
            "intent": "weather_forecast",
            "location": location,
            "days": days
        }

    if "this weekend" in lower:

        return {
            "intent": "weather_forecast",
            "location": location,
            "date": "this_weekend"
        }

    future_keywords = [
        "tomorrow",
        "tonight",
        "day after tomorrow",
        "upcoming",
        "will it",
        "going to",
        "expected",
        "forecast",
        "prediction",
        "predict",
        "travel",
        "trip",
        "drive",
        "plan",
        "planning"
    ]

    if any(
        word in lower
        for word in future_keywords
    ):

        return {
            "intent": "weather_forecast",
            "location": location,
            "date": date
        }

    return {
        "intent": "current_weather",
        "location": location,
        "date": "today"
    }


def parse_weather_query(
    query: str
) -> Dict[str, Any]:

    groq_result = _parse_with_groq(query)

    if groq_result is not None:
        return groq_result

    return _parse_rule_based(query)


if __name__ == "__main__":

    test_queries = [
        "Is it hot outside in Hyderabad?",
        "What will the weather be like after 5 days in Hyderabad?",
        "What will the weather be like for the next 5 days in Hyderabad?",
        "Do I need a jacket tonight in Hyderabad?",
        "Is it going to rain this weekend in Hyderabad?"
    ]

    for query in test_queries:

        print(f"\nQuery: {query}")

        result = parse_weather_query(query)

        print(
            "Result:",
            json.dumps(
                result,
                indent=2
            )
        )