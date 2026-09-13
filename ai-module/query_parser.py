
import json
import re


def parse_weather_query(query: str) -> dict:
    """Parse a natural-language weather question into structured JSON."""

    if not query or not query.strip():
        return {"error": "Empty question provided."}

    text = query.strip()
    lower = text.lower()

    # 1. Check domain relevance
    weather_keywords = [
        "weather", "forecast", "temp", "temperature",
        "rain", "raining", "rainfall", "snow", "snowing",
        "climate", "sunny", "sunshine", "clear", "clear sky",
        "cloud", "clouds", "cloudy", "overcast",
        "wind", "windy", "breeze", "breezy",
        "humidity", "humid", "hot", "cold", "warm",
        "umbrella", "raincoat", "jacket", "coat",
        "sunscreen", "picnic", "outdoor", "outside",
        "drive", "travel", "about"
    ]

    if not any(w in lower for w in weather_keywords):
        return {
            "error": "Unsupported or unclear question. Please ask a weather-related query."
        }

    # 2. Extract number of days
    days = 1

    days_match = re.search(
        r"\b(?:for|next)?\s*(\d+)\s*(?:day|days)\b",
        lower
    )

    if days_match:
        days = int(days_match.group(1))
    elif re.search(r"\b(?:next|for)\s+(?:one|a)\s+week\b", lower):
        days = 7
    elif re.search(r"\bnext\s+week\b", lower):
        days = 7

    # 3. Stop words
    stop_words = {
        "in", "at", "for", "of", "near", "around", "to", "on",
        "the", "a", "an", "is", "be", "are",
        "what", "how", "tell", "me", "will", "it",
        "weather", "forecast", "temperature", "temp", "climate",
        "today", "tonight", "tomorrow", "tommorow",
        "day", "after", "next", "week", "weeks",
        "this", "evening", "morning", "afternoon",
        "rain", "raining", "rainfall", "sunny", "sunshine",
        "clear", "sky", "cloudy", "cloud", "clouds", "overcast",
        "snow", "snowing",
        "wind", "windy", "breeze", "breezy",
        "humidity", "humid", "hot", "cold", "warm",
        "umbrella", "raincoat", "jacket", "coat",
        "sunscreen", "picnic", "outdoor", "outside",
        "drive", "travel", "should", "i", "carry",
        "need", "take", "wear", "bring", "plan",
        "can", "could", "would", "good", "about",
        "going", "be", "do", "does", "is", "will"
    }

    # 4. Clean query
    clean_text = re.sub(r"[?.!,;:]", " ", text)

    # Remove duration expressions
    clean_text = re.sub(
        r"\b(?:for|next)?\s*(?:\d+|one|a)\s*(?:day|days|week|weeks)\b",
        " ",
        clean_text,
        flags=re.IGNORECASE
    )

    # Remove multi-word time expressions
    clean_text = re.sub(
        r"\bday\s+after\s+tomorrow\b",
        " ",
        clean_text,
        flags=re.IGNORECASE
    )

    # 5. Extract location
    location = None

    def clean_location(value):
        words = [
            w for w in value.split()
            if w.lower() not in stop_words and not w.isdigit()
        ]
        if words:
            return " ".join(words).title()
        return None

    # Location after in / at / near / around / to / about
    prep_match = re.search(
        r"\b(?:in|at|near|around|to|about)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+){0,4})",
        clean_text,
        re.IGNORECASE
    )

    if prep_match:
        location = clean_location(prep_match.group(1))

    # Location before weather-related words
    if not location:
        direct_match = re.search(
            r"^\s*([a-zA-Z]+(?:\s+[a-zA-Z]+){0,4})\s+"
            r"(?:weather|forecast|temp|temperature|climate|rain|snow|wind|humidity)\b",
            clean_text,
            re.IGNORECASE
        )

        if direct_match:
            location = clean_location(direct_match.group(1))

    # Fallback: remaining meaningful words
    if not location:
        words = [
            w for w in clean_text.split()
            if w.lower() not in stop_words
            and not w.isdigit()
        ]

        if words:
            location = " ".join(words).title()

    # 6. Detect intent

    # Rain-related queries
        # 6. Detect intent
    # Only 2 intents:
    # current_weather
    # weather_forecast

    forecast_keywords = [
        # Forecast / prediction
        "forecast", "prediction", "predict",
        "will it", "going to", "expected",

        # Future / time
        "tomorrow", "tonight",
        "day after tomorrow",
        "this evening", "this morning",
        "this afternoon", "next", "upcoming",

        # Planning / future activities
        "picnic", "outdoor", "outside",
        "drive", "travel", "trip", "journey",
        "plan", "planning", "wear",
        "what should i wear", "what to wear",
        "should i carry", "do i need",
        "is it a good day", "good for"
    ]

    current_weather_keywords = [
        # Rain
        "rain", "raining", "rainfall", "rainy",
        "drizzle", "drizzling", "shower", "showers",
        "precipitation", "chance of rain", "rain chance",
        "wet", "umbrella", "raincoat", "downpour",
        "heavy rain", "light rain",

        # Sunny
        "sunny", "sunshine", "sun", "bright",
        "clear", "clear sky", "clear skies",
        "sunny weather", "bright sky", "no clouds",
        "cloudless",

        # Cloud
        "cloudy", "cloud", "clouds", "overcast",
        "cloud cover", "cloudy weather",
        "grey sky", "gray sky", "mostly cloudy",
        "partly cloudy",

        # Temperature
        "temperature", "temp", "degree", "degrees",
        "hot", "cold", "warm", "cool",
        "heat", "how hot", "how cold",
        "temperature today", "temperature now",
        "maximum temperature", "minimum temperature",
        "highest temperature", "lowest temperature",

        # Humidity
        "humidity", "humid", "moisture",
        "muggy", "damp", "relative humidity",
        "humidity level", "humidity percentage",

        # Wind
        "wind", "windy", "winds",
        "breeze", "breezy", "gust", "gusts",
        "wind speed", "wind direction",
        "strong wind", "high winds",
        "windy weather", "how strong is the wind"
    ]

    if days > 1:
        intent = "weather_forecast"

    elif any(word in lower for word in forecast_keywords):
        intent = "weather_forecast"

    else:
        intent = "current_weather"

    return {
        
        "intent": intent,
        "location": location,
        "days": days
    }


if __name__ == "__main__":
    test_queries = [
        "What is the weather in Hyderabad tonight?",
        "Will it rain in Hyderabad tonight?",
        "Weather Hyderabad tonight",
        "Hyderabad weather tonight",
        "Weather in Hyderabad tomorrow",
        "Weather Hyderabad day after tomorrow",
        "Weather Hyderabad next week",
        "Weather Hyderabad for one week",
        "5 day forecast Hyderabad",
        "7 days forecast in Hyderabad",
        "Weather in New York City tomorrow",
        "Weather in Rio de Janeiro tomorrow",
        "Weather in Los Angeles tonight",
        "What about Hyderabad tonight?",
        "What's Hyderabad weather tonight?",
        "Should I carry an umbrella in Hyderabad tonight?",
        "Should I wear a jacket in Hyderabad tonight?",
        "Is it clear in Hyderabad tonight?",
        "Temperature Hyderabad tonight",
        "Humidity in Hyderabad tonight",
        "Wind in Hyderabad tonight",
        "Can I travel to Mumbai tomorrow?",
        "Can I plan a picnic in Pune tomorrow?"
    ]

    for q in test_queries:
        print(f"Query : {q}")
        print(f"Result: {json.dumps(parse_weather_query(q), indent=4)}\n")

    user_input = input("Enter your weather question: ")
    if user_input.strip():
        print(json.dumps(parse_weather_query(user_input), indent=4))
