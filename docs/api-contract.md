# WeatherGPT API Contract

## 1. Purpose

This document defines how WeatherGPT components exchange data.

The goal is to ensure that the Weather Data Service, Backend, AI module and Frontend can work together consistently.

---

## 2. Current Weather Data

The Weather Data Service provides current weather information in a structured format.

Example:

{
  "location": "Hyderabad",
  "temperature": 29.4,
  "humidity": 78,
  "condition": "Cloudy",
  "wind_speed": 12.0,
  "rain_chance": 20,
  "feeling_like": 31.2
}

---

## 3. Current Weather Fields

| Field | Description |
|---|---|
| location | Requested location |
| temperature | Current temperature in °C |
| humidity | Humidity percentage |
| condition | Current weather condition |
| wind_speed | Wind speed in km/h |
| rain_chance | Chance of rain in percentage |
| feeling_like | Feels-like temperature in °C |

---

## 4. Forecast Data

The Weather Data Service provides forecast information for the requested number of days.

Example:

{
  "location": "Hyderabad",
  "forecast": [
    {
      "date": "2026-09-12",
      "max_temp": 30.5,
      "min_temp": 24.1,
      "condition": "Partly cloudy",
      "rain_chance": 30,
      "sunrise": "06:02 AM",
      "sunset": "06:20 PM"
    }
  ]
}

---

## 5. Forecast Fields

| Field | Description |
|---|---|
| location | Requested location |
| date | Forecast date |
| max_temp | Maximum temperature in °C |
| min_temp | Minimum temperature in °C |
| condition | Expected weather condition |
| rain_chance | Chance of rain in percentage |
| sunrise | Sunrise time |
| sunset | Sunset time |

---

## 6. Backend Request

The frontend sends a request to the backend.

Example:

{
  "message": "What is the weather in Hyderabad?"
}

For forecast queries, the request may contain information such as:

{
  "message": "What will the weather be tomorrow in Hyderabad?"
}

---

## 7. Backend Response

The backend returns a response to the frontend.

Example:

{
  "message": "The current weather in Hyderabad is 29.4°C with cloudy conditions and 78% humidity.",
  "weather": {
    "location": "Hyderabad",
    "temperature": 29.4,
    "humidity": 78,
    "condition": "Cloudy",
    "wind_speed": 12.0,
    "rain_chance": 20,
    "feeling_like": 31.2
  }
}

For forecast requests, the backend can return the forecast data retrieved from the Weather Data Service.

---

## 8. AI/NLP Information

The AI module should identify information from the user's question.

Example:

User:

"What will the weather be tomorrow in Hyderabad?"

AI/NLP output:

{
  "intent": "forecast",
  "location": "Hyderabad",
  "time": "tomorrow"
}

The backend then uses this information to request the appropriate weather data.

---

## 9. Error Handling

The Weather Data Service may return structured error messages when a request cannot be completed.

Examples:

{
  "error": "Location not found"
}

{
  "error": "Weather API key is invalid"
}

{
  "error": "Unable to connect to weather service"
}

The backend should handle these errors and provide an appropriate response to the user.

---

## 10. Important Rule

The AI module must not invent weather information.

Weather information must come from an actual weather or meteorological data source.

The AI module is responsible for understanding the user's question and explaining retrieved weather information.
