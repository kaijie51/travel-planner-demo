"""Weather via Open-Meteo (free, no API key). Forecasts only reach ~16 days ahead."""

from datetime import date, datetime, timedelta

import requests
import streamlit as st

WMO = {
    0: "☀️ Clear", 1: "🌤️ Mainly clear", 2: "⛅ Partly cloudy", 3: "☁️ Overcast",
    45: "🌫️ Fog", 48: "🌫️ Fog", 51: "🌦️ Light drizzle", 53: "🌦️ Drizzle", 55: "🌦️ Heavy drizzle",
    61: "🌧️ Light rain", 63: "🌧️ Rain", 65: "🌧️ Heavy rain", 71: "🌨️ Light snow", 73: "🌨️ Snow",
    75: "🌨️ Heavy snow", 80: "🌦️ Showers", 81: "🌧️ Heavy showers", 82: "⛈️ Violent showers",
    95: "⛈️ Thunderstorm", 96: "⛈️ Thunderstorm + hail", 99: "⛈️ Thunderstorm + hail",
}
WET_CODES = {51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99}


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def geocode(city: str):
    try:
        r = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en"},
            timeout=8,
        )
        res = r.json().get("results") or []
        if not res:
            return None
        g = res[0]
        return {"lat": g["latitude"], "lon": g["longitude"], "name": g["name"], "country": g.get("country", "")}
    except (requests.RequestException, ValueError, KeyError):
        return None


@st.cache_data(ttl=1800, show_spinner=False)
def forecast(city: str, start: date, days: int) -> dict:
    """Returns {'days': {iso_date: {...}}, 'source': str, 'note': str}."""
    retrieved = datetime.now().strftime("%d %b %Y, %H:%M")
    end = start + timedelta(days=days - 1)
    if start > date.today() + timedelta(days=15) or end < date.today():
        return {"days": {}, "source": "Open-Meteo", "note": "Trip dates are outside the 16-day forecast range; no forecast used."}
    g = geocode(city)
    if not g:
        return {"days": {}, "source": "Open-Meteo", "note": f"Could not locate '{city}' for weather."}
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": g["lat"], "longitude": g["lon"], "timezone": "auto",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "start_date": max(start, date.today()).isoformat(),
                "end_date": min(end, date.today() + timedelta(days=15)).isoformat(),
            },
            timeout=8,
        )
        d = r.json()["daily"]
    except (requests.RequestException, ValueError, KeyError):
        return {"days": {}, "source": "Open-Meteo", "note": "Weather service unavailable right now."}
    out = {}
    for i, day in enumerate(d["time"]):
        code = d["weather_code"][i]
        out[day] = {
            "summary": WMO.get(code, f"Code {code}"),
            "wet": code in WET_CODES or (d["precipitation_probability_max"][i] or 0) >= 60,
            "tmax": d["temperature_2m_max"][i],
            "tmin": d["temperature_2m_min"][i],
            "rain_prob": d["precipitation_probability_max"][i],
        }
    return {
        "days": out,
        "source": f"Open-Meteo forecast for {g['name']}, {g['country']}",
        "note": f"Retrieved {retrieved}. Forecasts change; check again before the day.",
    }
