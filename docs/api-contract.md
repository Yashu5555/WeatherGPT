# WeatherGPT API Contract

## 1. Purpose

This document defines how WeatherGPT components exchange data.

The goal is to ensure that the Weather Data Service, Backend, AI module and Frontend can work together consistently.

## 2. Weather Data Format

The Weather Data Service should provide weather information in a structured format.

Example:

{
  "location": "Hyderabad",
  "temperature": 29,
  "humidity": 78,
  "wind_speed": 12,
  "condition": "Cloudy"
}

## 3. Weather Data Fields

| Field | Description |
|---|---|
| location | Requested location |
| temperature | Current temperature |
| humidity | Humidity percentage |
| wind_speed | Wind speed |
| condition | Current weather condition |

## 4. Backend Request

The frontend sends a request to the backend.

Example:

{
  "message": "What is the weather in Hyderabad?"
}

## 5. Backend Response

The backend returns a response to the frontend.

Example:

{
  "message": "The current weather in Hyderabad is 29°C with cloudy conditions and 78% humidity.",
  "weather": {
    "location": "Hyderabad",
    "temperature": 29,
    "humidity": 78,
    "wind_speed": 12,
    "condition": "Cloudy"
  }
}

## 6. AI/NLP Information

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

## 7. Important Rule

The AI module must not invent weather information.

Weather information must come from an actual weather or meteorological data source.

The AI module is responsible for understanding the user's question and explaining retrieved weather information.
