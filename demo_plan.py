"""A ready-made itinerary for the Singapore demo, so the Itineraries page has a plan without an API call.
Same shape as Claude's structured output (schemas.ItineraryOption); dates follow the demo's start date.
Scores are not stored here: the app computes them from the stop attributes like any generated plan."""

from datetime import date, timedelta

HOTEL = (1.3008, 103.8559)  # Bugis MRT


def _leg(mode: str, mins: int, cost: float, details: str) -> dict:
    return {"mode": mode, "duration_min": mins, "cost": cost, "details": details}


def _attrs(nature=0.0, culture=0.0, food=0.0, shopping=0.0, nightlife=0.0, adventure=0.0, relaxation=0.0) -> dict:
    return {"nature": nature, "culture": culture, "food": food, "shopping": shopping,
            "nightlife": nightlife, "adventure": adventure, "relaxation": relaxation}


def _stop(name, kind, start, end, area, lat, lon, description, cost, crowd, indoor, attrs, why, legs,
          anchor=False, gem=False, booking="Walk-in", confidence="high", caution="") -> dict:
    return {"name": name, "kind": kind, "start_time": start, "end_time": end, "area": area, "lat": lat, "lon": lon,
            "description": description, "est_cost_per_person": cost, "crowd_level": crowd, "indoor": indoor,
            "is_anchor": anchor, "hidden_gem": gem, "booking_info": booking, "info_confidence": confidence,
            "caution": caution, "attributes": attrs, "why": why, "transport_to_next": legs}


def _day1(d: date) -> dict:
    return {
        "day_number": 1, "date": d.isoformat(), "theme": "Hawker breakfast, Southern Ridges and Orchard",
        "from_hotel": _leg("Public transport", 20, 1.8, "MRT Downtown Line to Chinatown, then 10 min walk"),
        "stops": [
            _stop("Tiong Bahru Market (chwee kueh stall)", "meal", "09:00", "10:00", "Tiong Bahru", 1.2850, 103.8325,
                  "The group's saved hawker gem: chwee kueh and kopi before the 10am rush, then a stroll past indie bookshops.",
                  8, "moderate", True, _attrs(nature=0.2, culture=0.9, food=1.0, shopping=0.7, relaxation=0.6),
                  ["Your must-visit", "Before the 10am rush", "Vegetarian & pork-free stalls"],
                  [_leg("Ride-hailing", 10, 3.5, "Grab to Marang Trail at the foot of Mount Faber"),
                   _leg("Public transport", 20, 1.5, "Bus 124 then walk to Marang Trail")],
                  anchor=True, gem=True),
            _stop("Southern Ridges: Marang Trail to Henderson Waves", "activity", "10:30", "12:15", "Mount Faber",
                  1.2763, 103.8154,
                  "Forest steps up Mount Faber, then canopy walkways with city and harbour views to the Henderson Waves bridge.",
                  0, "low", False,
                  _attrs(nature=1.0, culture=0.4, food=0.1, shopping=0.1, nightlife=0.1, adventure=0.7, relaxation=0.8),
                  ["Hiking & nature interest", "Free", "Quiet on weekday mornings"],
                  [_leg("Walk", 15, 0, "Back along the ridge to Faber Peak")], gem=True),
            _stop("Faber Peak hilltop lunch", "meal", "12:30", "13:45", "Mount Faber", 1.2715, 103.8195,
                  "Lunch with harbour views at the cable car station, local and vegetarian dishes, then the cable car down.",
                  30, "moderate", True,
                  _attrs(nature=0.8, culture=0.4, food=0.9, shopping=0.3, nightlife=0.4, adventure=0.3, relaxation=0.8),
                  ["Views for everyone", "Vegetarian & pork-free dishes", "Cable car ride"],
                  [_leg("Public transport", 25, 1.8, "Cable car to HarbourFront, then MRT Circle Line to Orchard"),
                   _leg("Ride-hailing", 15, 4.0, "Grab to ION Orchard")],
                  booking="Cable car tickets online (about SGD 35 return, included in cost)", confidence="medium",
                  caution="Cable car fares change; check the current price."),
            _stop("ION Orchard & Emerald Hill", "activity", "14:15", "17:30", "Orchard Road", 1.3040, 103.8318,
                  "Flagship malls and the local-designer floor at Design Orchard, then the Peranakan terraces of Emerald Hill.",
                  60, "moderate", True,
                  _attrs(nature=0.1, culture=0.6, food=0.7, shopping=1.0, nightlife=0.4, relaxation=0.4),
                  ["Top shopping interest", "Indoor in the afternoon heat", "Local designers"],
                  [_leg("Public transport", 15, 1.6, "MRT Downtown Line to Bugis")]),
            _stop("Kampong Glam dinner & evening", "meal", "18:30", "21:30", "Kampong Glam", 1.3006, 103.8587,
                  "Halal Middle-Eastern and Malay dinner on Arab Street, then Haji Lane's indie boutiques and small bars.",
                  35, "moderate", False,
                  _attrs(culture=0.9, food=1.0, shopping=0.9, nightlife=0.9, relaxation=0.5),
                  ["Shopping & nightlife", "Pork-free, vegetarian mezze", "5 min walk to hotel"], [],
                  gem=True),
        ],
        "to_hotel": _leg("Walk", 8, 0, "Along Rochor Road to Bugis"),
        "walking_km": 5.0,
        "pace_note": "Moderate: the hike is done before midday, and the afternoon is indoors.",
        "wet_weather_backup": "Skip the ridge walk and ride the cable car to Sentosa's indoor attractions, then on to Orchard.",
    }


def _day2(d: date) -> dict:
    return {
        "day_number": 2, "date": d.isoformat(), "theme": "Botanic Gardens, Dempsey and the Night Safari",
        "from_hotel": _leg("Public transport", 25, 1.8, "MRT Downtown Line to Botanic Gardens"),
        "stops": [
            _stop("Singapore Botanic Gardens & National Orchid Garden", "activity", "09:15", "11:45", "Tanglin",
                  1.3138, 103.8159,
                  "UNESCO-listed gardens: rainforest trail, swan lake and the orchid garden's thousands of hybrids.",
                  15, "low", False,
                  _attrs(nature=1.0, culture=0.8, food=0.3, shopping=0.4, adventure=0.2, relaxation=0.9),
                  ["Nature interest", "Easy paths for the whole group", "Quiet in the morning"],
                  [_leg("Ride-hailing", 8, 3.0, "Grab to Dempsey Road"),
                   _leg("Walk", 20, 0, "Via the Tanglin Gate and Cluny Road")],
                  booking="Gardens free; Orchid Garden tickets at the gate", confidence="high"),
            _stop("Dempsey Hill lunch", "meal", "12:00", "13:30", "Dempsey", 1.3049, 103.8106,
                  "Colonial barracks turned garden restaurants and boutiques; long lunch on a leafy terrace.",
                  35, "low", False,
                  _attrs(nature=0.7, culture=0.5, food=1.0, shopping=0.7, nightlife=0.4, relaxation=0.9),
                  ["Garden setting", "Vegetarian & pork-free choices", "Boutiques next door"],
                  [_leg("Ride-hailing", 15, 4.0, "Grab back to the hotel")], gem=True),
            _stop("Rest at the hotel", "rest", "14:00", "16:45", "Bugis", 1.3008, 103.8559,
                  "Pool, nap or a short shop at Bugis Street: the evening runs late.",
                  0, "low", True, _attrs(relaxation=1.0, shopping=0.3),
                  ["Recharge before a late night"],
                  [_leg("Ride-hailing", 30, 7.0, "Grab to Mandai Wildlife Reserve")]),
            _stop("Ulu Ulu Safari Restaurant", "meal", "17:30", "19:00", "Mandai", 1.4021, 103.7883,
                  "Laksa, satay and vegetarian dishes in a rainforest-themed dining hall at the Night Safari entrance.",
                  25, "moderate", True,
                  _attrs(nature=0.7, culture=0.4, food=0.9, shopping=0.3, nightlife=0.5, relaxation=0.5),
                  ["Right at the Night Safari", "Vegetarian & pork-free dishes"],
                  [_leg("Walk", 5, 0, "To the Night Safari gate")], confidence="medium"),
            _stop("Night Safari (pre-booked tickets)", "activity", "19:30", "22:00", "Mandai", 1.4021, 103.7880,
                  "The group's booked night zoo: tram ride, the Leopard and Fishing Cat trails, and the Creatures of the Night show.",
                  0, "moderate", False,
                  _attrs(nature=1.0, culture=0.6, food=0.3, shopping=0.4, nightlife=0.9, adventure=0.5, relaxation=0.4),
                  ["Your fixed booking", "Already paid", "Nature after dark"], [],
                  anchor=True, booking="Tickets already bought"),
        ],
        "to_hotel": _leg("Ride-hailing", 30, 7.0, "Grab back to Bugis; book from the taxi stand at the exit"),
        "walking_km": 5.0,
        "pace_note": "Easy garden morning, then a long hotel break so the late Night Safari isn't tiring.",
        "wet_weather_backup": "Swap the gardens for the covered Orchid Garden and Dempsey's indoor cafés; the Safari runs in light rain.",
    }


def _day3(d: date) -> dict:
    return {
        "day_number": 3, "date": d.isoformat(), "theme": "Jewel Changi, Gardens by the Bay and the bay at night",
        "from_hotel": _leg("Public transport", 35, 2.0, "MRT Downtown Line to Expo, then East-West Line to Changi Airport"),
        "stops": [
            _stop("Jewel Changi: Rain Vortex & Canopy Park", "activity", "10:00", "12:30", "Changi", 1.3601, 103.9897,
                  "The world's tallest indoor waterfall inside a forest valley, with Canopy Park nets and mazes plus 280 shops.",
                  25, "moderate", True,
                  _attrs(nature=0.9, culture=0.4, food=0.8, shopping=1.0, nightlife=0.3, adventure=0.5, relaxation=0.7),
                  ["Nature & shopping in one place", "Indoor", "Free waterfall"],
                  [_leg("Walk", 5, 0, "Down to the basement food hall")],
                  booking="Canopy Park tickets online (included in cost)", confidence="medium",
                  caution="Busiest in the evening and at weekends; the light show is at night."),
            _stop("Jewel food hall lunch", "meal", "12:30", "13:30", "Changi", 1.3601, 103.9897,
                  "Singapore hawker classics and international counters under one roof, with a view of the Rain Vortex.",
                  15, "moderate", True,
                  _attrs(nature=0.6, culture=0.3, food=1.0, shopping=0.7, relaxation=0.6),
                  ["Vegetarian & pork-free counters", "No extra travel"],
                  [_leg("Public transport", 35, 2.0, "MRT East-West Line back to Bugis")]),
            _stop("Rest at the hotel", "rest", "14:15", "16:45", "Bugis", 1.3008, 103.8559,
                  "Break before the evening.",
                  0, "low", True, _attrs(relaxation=1.0),
                  ["Rest before the evening"],
                  [_leg("Public transport", 15, 1.5, "MRT Downtown Line to Bayfront")]),
            _stop("Gardens by the Bay: Cloud Forest & Garden Rhapsody", "activity", "17:15", "20:00", "Marina Bay",
                  1.2816, 103.8636,
                  "Misty indoor mountain and waterfall, the OCBC Skyway between the Supertrees, then the free light show.",
                  32, "moderate", True,
                  _attrs(nature=1.0, culture=0.7, food=0.3, shopping=0.4, nightlife=0.7, adventure=0.4, relaxation=0.8),
                  ["Nature for everyone", "Indoor if it rains", "Free light show"],
                  [_leg("Walk", 10, 0, "Through the gardens to Satay by the Bay")],
                  booking="Buy Cloud Forest tickets online", confidence="medium",
                  caution="Light show times can change; check the 19:45 slot on the day."),
            _stop("Satay by the Bay", "meal", "20:15", "21:45", "Marina Bay", 1.2820, 103.8690,
                  "Open-air hawker centre on the water: chicken and mutton satay, vegetarian stalls and cold drinks.",
                  25, "moderate", False,
                  _attrs(nature=0.6, culture=0.5, food=1.0, shopping=0.1, nightlife=0.8, relaxation=0.7),
                  ["Farewell dinner", "Pork-free satay", "Waterfront at night"], [], gem=True),
        ],
        "to_hotel": _leg("Ride-hailing", 15, 4.0, "Grab back to Bugis"),
        "walking_km": 5.0,
        "pace_note": "Moderate, with an afternoon hotel break before the evening at the Gardens.",
        "wet_weather_backup": "Jewel and the Cloud Forest are indoors; if it pours, skip the Skyway and eat at Marina Bay Sands.",
    }


def demo_option(start: date) -> dict:
    return {
        "title": "Something for everyone: ridges, markets and the Night Safari",
        "summary": ("Three days built on places that serve several interests at once, so the hikers and the shoppers "
                    "both get something at almost every stop. Walks run early to beat the heat, afternoons are indoors "
                    "or at rest, and the booked Night Safari is the centrepiece."),
        "hotel_lat": HOTEL[0], "hotel_lon": HOTEL[1],
        "days": [_day1(start), _day2(start + timedelta(days=1)), _day3(start + timedelta(days=2))],
        "tradeoffs": [
            {"chosen": "Southern Ridges & Faber Peak", "alternative": "Sentosa",
             "deciding_factor": "Free, quiet in the morning and serves the group's nature interest, where Sentosa is costly and crowded.",
             "counterfactual": "Raising crowd tolerance to 4 and the budget would favour Sentosa."},
            {"chosen": "Jewel Changi", "alternative": "Little India & Mustafa Centre",
             "deciding_factor": "Serves shopping and nature together, so no one in the group sits out the morning.",
             "counterfactual": "Dropping the nature interest across the group would make Little India's shopping the better fit."},
            {"chosen": "Rest at the hotel", "alternative": "Bird Paradise",
             "deciding_factor": "Keeps Day 2 within the group's pace before a late Night Safari.",
             "counterfactual": "Setting everyone's pace to Active (4) would fit Bird Paradise in."},
            {"chosen": "Kampong Glam evening", "alternative": "Clarke Quay bars",
             "deciding_factor": "Serves shopping and nightlife together and is a short walk from the hotel.",
             "counterfactual": "Raising the nightlife interest across the group would shift the evening to Clarke Quay."},
        ],
        "group_balance_note": ("Most stops combine nature with food, shopping or nightlife, so the group's majority and "
                               "minority interests are served together rather than taking turns. Every meal has "
                               "vegetarian and pork-free choices, and each day stays within the group's pace."),
        "warnings": [],
    }
