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
         "interests": {"nature": 1, "culture": 3, "food": 5, "shopping": 5, "nightlife": 3, "adventure": 1, "relaxation": 2}},
        {"id": _id(), "name": "Arjun", "weight": 1.0, "pace": 3, "dietary": "vegetarian", "mobility": "",
         "interests": {"nature": 1, "culture": 2, "food": 4, "shopping": 5, "nightlife": 4, "adventure": 1, "relaxation": 2}},
        {"id": _id(), "name": "Sofia", "weight": 1.0, "pace": 2, "dietary": "", "mobility": "",
         "interests": {"nature": 2, "culture": 4, "food": 4, "shopping": 4, "nightlife": 1, "adventure": 0, "relaxation": 4}},
        {"id": _id(), "name": "Daniel", "weight": 1.0, "pace": 4, "dietary": "no pork", "mobility": "",
         "interests": {"nature": 5, "culture": 2, "food": 3, "shopping": 0, "nightlife": 1, "adventure": 5, "relaxation": 1}},
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

DEMO_SCRIPT = """
**Suggested 5-minute walkthrough**

1. **Trip & travellers.** The demo loads a Singapore trip for 4 friends. Three love shopping, Daniel loves hiking. Point out the per-person interest sliders and influence weights.
2. **Must-visits.** Show the *fixed* Night Safari booking (Day 2, 19:30) and a *flexible* hawker stop saved from TikTok. Import the Instagram reel to add Bukit Timah Hill.
3. **Privacy.** In the *Privacy & data* tab, show exactly what is sent: names become Traveller A–D, and the email and booking reference are removed.
4. **Generate.** Three strategies run in parallel. Compare them in the table: the fair group score (Nash welfare) vs. the plain average.
5. **Fairness.** Open the fairness panel. Daniel's hiking interest is still served. Increase Daniel's weight and regenerate to show how the balance shifts.
6. **Explainability.** Expand a stop to see its computed score breakdown. Ask *"Why this instead of…?"* (e.g. Gardens by the Bay vs Sentosa) to get the deciding factor and counterfactual.
7. **Human in the loop.** Swap a stop, remove one, switch a transport mode. Costs and fairness update instantly.
8. **Live replan.** "Heavy rain from 2pm, we're near Orchard". Review the proposed changes before accepting.
9. **Confirm** the itinerary and download it.
"""
