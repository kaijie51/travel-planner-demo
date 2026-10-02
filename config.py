"""App-wide constants. Change APP_NAME here once the team picks a product name."""

APP_NAME = "Wayfare"  # placeholder product name
TAGLINE = "AI group itinerary planner: fair, transparent, and you stay in control"

MODEL = "claude-sonnet-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"

INTERESTS = ["nature", "culture", "food", "shopping", "nightlife", "adventure", "relaxation"]
INTEREST_LABELS = {
    "nature": "🌿 Nature",
    "culture": "🏛️ Culture & sightseeing",
    "food": "🍜 Food & cafes",
    "shopping": "🛍️ Shopping",
    "nightlife": "🌃 Nightlife",
    "adventure": "🧗 Active & adventure",
    "relaxation": "🧘 Relaxed exploring",
}

TRANSPORT_MODES = ["Walk", "Public transport", "Ride-hailing", "Drive"]
TRANSPORT_ICONS = {"Walk": "🚶", "Public transport": "🚇", "Ride-hailing": "🚕", "Drive": "🚗"}

PACE_LABELS = {1: "Very relaxed", 2: "Relaxed", 3: "Moderate", 4: "Active", 5: "Packed"}
CROWD_LABELS = {1: "Avoid crowds", 2: "Prefer quiet", 3: "Don't mind", 4: "Fine with busy", 5: "Love the buzz"}

# Itinerary variants generated in parallel; each is one Claude call.
STRATEGIES = [
    {
        "key": "balanced",
        "label": "⚖️ Balanced group",
        "instruction": (
            "FAIRNESS-FIRST. Maximise the weighted Nash social welfare of the group: every traveller "
            "should get at least one stop per day that strongly matches their top interests, and no "
            "traveller should be left with a much lower match than the others (scaled by their weight)."
        ),
    },
    {
        "key": "highlights",
        "label": "⭐ Highlights & efficient routing",
        "instruction": (
            "HIGHLIGHTS-FIRST. Prioritise the destination's strongest experiences for this group, with "
            "tight geographic clustering to minimise transit time. Fuller days are acceptable but must "
            "stay within the group's pace preference."
        ),
    },
    {
        "key": "local",
        "label": "🌱 Relaxed & local",
        "instruction": (
            "LOCAL & LOW-CROWD. Slower pace with buffer time. Favour lesser-known neighbourhoods, "
            "independent micro-merchants, hawkers and family-run places over crowded icons, and steer "
            "away from congested zones at peak hours."
        ),
    },
]
