from datetime import datetime

import requests


class WeatherService:
    """Service for fetching detailed weekly weather forecasts using Open-Meteo."""

    GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    # Open-Meteo weather code meanings (condensed)
    WEATHER_CODE_MAP = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }

    def __init__(self, forecast_days: int = 7):
        self.forecast_days = forecast_days

    def geocode_location(self, location: str) -> dict:
        """Convert a place name into latitude/longitude using Open-Meteo Geocoding API."""
        resp = requests.get(
            self.GEO_URL, params={"name": location, "count": 1}, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        if "results" in data and data["results"]:
            result = data["results"][0]
            return {
                "lat": result["latitude"],
                "lon": result["longitude"],
                "name": result["name"],
                "country": result["country"],
            }
        raise ValueError(f"Location not found: {location}")

    def fetch_weekly_weather_forecast(self, lat: float, lon: float) -> dict:
        """
        Get 7-day forecasts from Open-Meteo including highs, lows, precipitation, and condition.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": (
                "temperature_2m_max,temperature_2m_min,"
                "precipitation_sum,rain_sum,snowfall_sum,weathercode"
            ),
            "forecast_days": self.forecast_days,
            "timezone": "auto",
        }
        resp = requests.get(self.FORECAST_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        daily = data.get("daily", {})

        days = daily.get("time", [])
        highs = daily.get("temperature_2m_max", [])
        lows = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_sum", [])
        rain = daily.get("rain_sum", [])
        snow = daily.get("snowfall_sum", [])
        codes = daily.get("weathercode", [])

        weather_summary = []
        for i, day in enumerate(days):
            code = codes[i]
            condition = self.WEATHER_CODE_MAP.get(code, "Unknown")
            weather_summary.append(
                {
                    "day": day,
                    "condition": condition,
                    "high_temp_c": highs[i],
                    "low_temp_c": lows[i],
                    "precipitation_mm": precip[i],
                    "rain_mm": rain[i],
                    "snow_mm": snow[i],
                }
            )

        return {"weather_summary": weather_summary}

    def get_weekly_forecast(self, location: str, target_week: date) -> dict:
        """High-level method: geocode + fetch + summarize forecast."""
        geo = self.geocode_location(location)
        forecast = self.fetch_weekly_weather_forecast(geo["lat"], geo["lon"])
        return {
            "location": {"name": geo["name"], "country": geo["country"]},
            **forecast,
        }
