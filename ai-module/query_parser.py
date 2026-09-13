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
        "weather", "forecast", "temp", "temperature", "rain", "raining",
        "rainfall", "snow", "climate", "sunny", "sunshine", "clear sky",
        "cloud", "clouds", "cloudy", "overcast", "wind", "windy",
        "humidity", "humid", "hot", "cold", "warm"
    ]
    if not any(w in lower for w in weather_keywords) and not re.search(r"\b(hot|cold|warm|raining|snowing)\b", lower):
        return {"error": "Unsupported or unclear question. Please ask a weather-related query."}

    # 2. Extract date (defaults to 'today')
    date = "today"
    date_patterns = [
        "day after tomorrow", "tomorrow", "today", "tonight", "yesterday",
        "this weekend", "next week", "monday", "tuesday", "wednesday",
        "thursday", "friday", "saturday", "sunday"
    ]
    date_match = re.search(r"\b(" + "|".join(date_patterns) + r")\b", lower)
    date_span = None
    if date_match:
        date = date_match.group(1)
        date_span = date_match.span()
    else:
        # Check specific calendar dates (e.g., "15th September" or "2026-09-15")
        cal_match = re.search(r"\b\d{1,2}(?:st|nd|rd|th)?\s+[a-z]+|\b\d{4}-\d{2}-\d{2}\b", lower)
        if cal_match:
            date = text[cal_match.start():cal_match.end()]
            date_span = cal_match.span()

    # 3. Extract location
    clean_text = (text[:date_span[0]] + " " + text[date_span[1]:]) if date_span else text
    clean_text = re.sub(r"[?.!,;:]", " ", clean_text)
    stop_words = {
        "in", "at", "for", "of", "near", "around", "the", "a", "an", "is", "be",
        "are", "what", "how", "tell", "me", "will", "it", "weather", "forecast",
        "temperature", "temp", "today", "tomorrow", "rain", "raining", "sunny",
        "cloudy", "clouds", "wind", "windy", "humidity", "humid", "hot", "cold"
    }

    location = None
    prep_match = re.search(r"\b(?:in|at|for|of|near|around)\s+([a-zA-Z\s.'-]+)", clean_text, re.IGNORECASE)
    if prep_match:
        words = [w for w in prep_match.group(1).split() if w.lower() not in stop_words]
        if words:
            location = " ".join(words).title()

    if not location:
        direct_match = re.search(r"^\s*([a-zA-Z\s.'-]+?)\s+(?:weather|forecast|temp|temperature|climate|rain|snow|wind|humidity)\b", clean_text, re.IGNORECASE)
        if direct_match:
            words = [w for w in direct_match.group(1).split() if w.lower() not in stop_words]
            if words:
                location = " ".join(words).title()

    if not location:
        return {"error": "Location not found in the question."}

    # 4. Detect specific weather-condition intents before general forecast
    if any(w in lower for w in ["rain", "raining", "rainfall", "chance of rain", "drizzle"]):
        intent = "rain_forecast"
    elif any(w in lower for w in ["sunny", "sunshine", "clear sky", "clear skies"]):
        intent = "sunny_weather"
    elif any(w in lower for w in ["cloudy", "clouds", "cloud", "overcast"]):
        intent = "cloudy_weather"
    elif any(w in lower for w in ["temperature", "temp", "how hot", "how cold", "hot", "cold"]):
        intent = "temperature"
    elif any(w in lower for w in ["humidity", "humid"]):
        intent = "humidity"
    elif any(w in lower for w in ["wind", "windy", "breeze", "breezy"]):
        intent = "wind"
    elif date != "today" or any(w in lower for w in ["forecast", "will it", "going to", "next"]):
        intent = "weather_forecast"
    else:
        intent = "current_weather"

    return {
        "intent": intent,
        "location": location,
        "date": date
    }


if __name__ == "__main__":
    # Test Cases
    test_queries = [
        "What is the weather in Hyderabad tomorrow?",
        "Will it rain in Delhi tomorrow?",
        "Will it be sunny in Mumbai today?",
        "Will it be cloudy in Chennai tomorrow?"
    ]
    for q in test_queries:
        print(f"Query : {q}")
        print(f"Result: {json.dumps(parse_weather_query(q), indent=4)}\n")

    user_input = input("Enter your weather question: ")
    if user_input.strip():
        print(json.dumps(parse_weather_query(user_input), indent=4))
