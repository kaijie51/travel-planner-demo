"""Preset Singapore group trip for live demos. Dates start a week from today so the weather
forecast is real. The group is deliberately unbalanced (3 shoppers, 1 hiker) to show fairness."""

import uuid
from datetime import date, timedelta


def _id() -> str:
    return uuid.uuid4().hex[:8]


def demo_state() -> dict:
    start = date.today() + timedelta(days=7)
    trip = {
        "destination": "Singapore",
        "start_date": start,
        "num_days": 3,
        "day_start": "09:00",
        "day_end": "22:00",
        "budget": 450,
        "currency": "SGD",
        "transport_modes": ["Walk", "Public transport", "Ride-hailing"],
        "accommodation": "Hotel near Bugis MRT",
        "crowd_tolerance": 2,
        "dietary": "",
        "notes": "First time in Singapore for most of the group. Contact Mei at mei.tan@example.com for bookings.",
    }
    travellers = [
        {"id": _id(), "name": "Mei", "weight": 1.0, "pace": 3, "dietary": "", "mobility": "",
         "interests": {"nature": 3, "culture": 3, "food": 5, "shopping": 4, "nightlife": 1, "adventure": 0, "relaxation": 4}},
        {"id": _id(), "name": "Arjun", "weight": 1.0, "pace": 3, "dietary": "vegetarian", "mobility": "",
         "interests": {"nature": 2, "culture": 3, "food": 5, "shopping": 4, "nightlife": 2, "adventure": 0, "relaxation": 3}},
        {"id": _id(), "name": "Sofia", "weight": 1.0, "pace": 2, "dietary": "", "mobility": "",
         "interests": {"nature": 3, "culture": 4, "food": 5, "shopping": 4, "nightlife": 0, "adventure": 0, "relaxation": 5}},
        {"id": _id(), "name": "Daniel", "weight": 1.0, "pace": 4, "dietary": "no pork", "mobility": "",
         "interests": {"nature": 5, "culture": 3, "food": 4, "shopping": 1, "nightlife": 1, "adventure": 1, "relaxation": 4}},
    ]
    anchors = [
        {"id": _id(), "name": "Night Safari (pre-booked tickets)", "kind": "fixed",
         "date": (start + timedelta(days=1)).isoformat(), "time": "19:30", "duration_min": 150,
         "note": "Tickets already bought, booking ref K7XQ29M", "source_url": ""},
        {"id": _id(), "name": "Tiong Bahru Market (chwee kueh stall)", "kind": "flexible",
         "date": "", "time": "", "duration_min": 60,
         "note": "Saved from a TikTok: 'hidden hawker gem, go before 10am'",
         "source_url": "https://www.tiktok.com/@sgfoodie/video/7300000000000000000"},
    ]
    return {"trip": trip, "travellers": travellers, "anchors": anchors}


DEMO_LINK = {
    "url": "https://www.instagram.com/reel/C9xAbCdEfGh/?igsh=MTc4bWx6dGQ",
    "caption": "Sunrise hike up Bukit Timah Hill 🌄 only 30 min to the summit, so many monkeys! #singapore #hiking",
}
