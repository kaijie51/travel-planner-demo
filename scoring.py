"""Transparent, deterministic scoring. Claude proposes stops and tags each with interest
attributes; every number shown in the fairness panel and score breakdowns is computed here,
in plain Python, from those attributes and the travellers' own settings."""

import math

from config import INTERESTS
from privacy import normalised_weights

CROWD_RANK = {"low": 1, "moderate": 3, "high": 5}


def stop_match(pref: dict, attrs: dict) -> float:
    """How well a stop matches one traveller: attribute strength averaged over what they care about."""
    total = sum(pref.get(d, 0) for d in INTERESTS)
    if total == 0:
        return 0.5
    return sum(pref.get(d, 0) * attrs.get(d, 0.0) for d in INTERESTS) / total


def scored_stops(option: dict):
    for day in option["days"]:
        for stop in day["stops"]:
            if stop["kind"] != "rest":
                yield day, stop


def traveller_satisfaction(option: dict, travellers: list[dict]) -> list[float]:
    stops = [s for _, s in scored_stops(option)]
    if not stops:
        return [0.0 for _ in travellers]
    return [sum(stop_match(t["interests"], s["attributes"]) for s in stops) / len(stops) for t in travellers]


def group_metrics(option: dict, travellers: list[dict]) -> dict:
    sats = traveller_satisfaction(option, travellers)
    w = normalised_weights(travellers)
    n = len(sats)
    weighted_avg = sum(wi * s for wi, s in zip(w, sats))
    jain = (sum(sats) ** 2) / (n * sum(s * s for s in sats)) if n and any(sats) else 0.0
    # Weighted Nash social welfare (weighted geometric mean): high only if nobody is left behind.
    nsw = math.exp(sum(wi * math.log(max(s, 1e-3)) for wi, s in zip(w, sats))) if n else 0.0
    return {
        "satisfaction": sats,
        "weights": w,
        "weighted_avg": weighted_avg,
        "min": min(sats) if sats else 0.0,
        "gap": (max(sats) - min(sats)) if sats else 0.0,
        "jain": jain,
        "nsw": nsw,
    }


def group_match(stop: dict, travellers: list[dict]) -> float:
    w = normalised_weights(travellers)
    return sum(wi * stop_match(t["interests"], stop["attributes"]) for wi, t in zip(w, travellers))


def top_interests_served(stop: dict, travellers: list[dict], k: int = 2) -> list[str]:
    w = normalised_weights(travellers)
    group_pref = {d: sum(wi * t["interests"].get(d, 0) for wi, t in zip(w, travellers)) for d in INTERESTS}
    ranked = sorted(INTERESTS, key=lambda d: stop["attributes"].get(d, 0) * (group_pref[d] + 0.5), reverse=True)
    return [d for d in ranked[:k] if stop["attributes"].get(d, 0) >= 0.4]


def chosen_leg(stop: dict) -> dict | None:
    legs = stop.get("transport_to_next") or []
    if not legs:
        return None
    return legs[min(stop.get("_mode_idx", 0), len(legs) - 1)]


def day_cost(day: dict) -> float:
    cost = day["from_hotel"]["cost"] + day["to_hotel"]["cost"]
    for s in day["stops"]:
        cost += s["est_cost_per_person"]
        leg = chosen_leg(s)
        if leg:
            cost += leg["cost"]
    return cost


def day_transit_min(day: dict) -> int:
    mins = day["from_hotel"]["duration_min"] + day["to_hotel"]["duration_min"]
    for s in day["stops"]:
        leg = chosen_leg(s)
        if leg:
            mins += leg["duration_min"]
    return mins


def day_intensity(day: dict) -> float:
    """Rough 1-5 intensity: activity count, walking distance and active stops."""
    acts = sum(1 for s in day["stops"] if s["kind"] == "activity")
    active = sum(s["attributes"].get("adventure", 0) for s in day["stops"])
    return max(1.0, min(5.0, 0.6 * acts + 0.25 * day.get("walking_km", 0) + 0.5 * active))


def option_summary(option: dict, travellers: list[dict]) -> dict:
    m = group_metrics(option, travellers)
    stops = [s for d in option["days"] for s in d["stops"]]
    return {
        **m,
        "total_cost": sum(day_cost(d) for d in option["days"]),
        "transit_min": sum(day_transit_min(d) for d in option["days"]),
        "walking_km": sum(d.get("walking_km", 0) for d in option["days"]),
        "n_stops": len(stops),
        "hidden_gems": sum(1 for s in stops if s.get("hidden_gem")),
        "high_crowd": sum(1 for s in stops if s["crowd_level"] == "high"),
        "max_intensity": max((day_intensity(d) for d in option["days"]), default=0),
    }


def pace_flags(option: dict, travellers: list[dict]) -> list[str]:
    """Group-level pace warnings. Deliberately does not name who the day is too intense for."""
    flags = []
    for d in option["days"]:
        intensity = day_intensity(d)
        too_much = sum(1 for t in travellers if intensity > t["pace"] + 1.0)
        if too_much:
            flags.append(
                f"Day {d['day_number']} (intensity {intensity:.1f}/5) may be more intense than "
                f"{too_much} member(s) of the group prefer. Consider removing a stop."
            )
    return flags


def stop_breakdown(stop: dict, prev_leg: dict | None, travellers: list[dict], trip: dict) -> list[tuple[str, str]]:
    """Readable score breakdown computed from ranking inputs (shown under each stop)."""
    rows = [("Group preference match", f"{group_match(stop, travellers) * 100:.0f}%")]
    served = top_interests_served(stop, travellers)
    if served:
        rows.append(("Interests served", ", ".join(served)))
    per_day = trip["budget"] / max(len(trip["dates"]), 1)
    rows.append(("Cost", f"{trip['currency']} {stop['est_cost_per_person']:.0f} pp (daily budget ≈ {per_day:.0f})"))
    if prev_leg:
        rows.append(("Travel from previous", f"{prev_leg['duration_min']} min by {prev_leg['mode'].lower()}"))
    tol = trip["crowd_tolerance"]
    crowd_ok = CROWD_RANK[stop["crowd_level"]] <= tol + 1
    rows.append(("Crowds", f"{stop['crowd_level']} ({'fits' if crowd_ok else 'above'} your crowd tolerance)"))
    return rows
