"""De-identification layer: the only path from user data to the AI provider.

"AI sees the trips, but never the people." Only an allowlist of fields is sent; names become
Traveller A/B/...; emails, phone numbers and booking references are stripped from free text;
individual dietary/mobility needs are merged to group level so explanations can't single anyone out.
"""

import re
from urllib.parse import urlsplit, urlunsplit

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"\+?\d[\d\s-]{6,}\d")
# Booking-reference-like tokens: 6-10 uppercase letters/digits containing at least one of each.
BOOKING_REF = re.compile(r"\b(?=[A-Z0-9]*\d)(?=[A-Z0-9]*[A-Z])[A-Z0-9]{6,10}\b")


def aliases(travellers: list[dict]) -> dict[str, str]:
    return {t["id"]: f"Traveller {chr(65 + i)}" for i, t in enumerate(travellers)}


def scrub(text: str, travellers: list[dict], log: list[str], field: str) -> str:
    if not text:
        return ""
    out = text
    # Identifiers first, so a name inside an email address doesn't break the email match.
    for pattern, label in ((EMAIL, "email"), (PHONE, "phone number"), (BOOKING_REF, "booking reference")):
        if pattern.search(out):
            out = pattern.sub(f"[{label} removed]", out)
            log.append(f"{field}: removed {label}")
    alias = aliases(travellers)
    for t in travellers:
        name = (t.get("name") or "").strip()
        if len(name) >= 2 and re.search(rf"\b{re.escape(name)}\b", out, re.IGNORECASE):
            out = re.sub(rf"\b{re.escape(name)}\b", alias[t["id"]], out, flags=re.IGNORECASE)
            log.append(f"{field}: replaced a traveller name with '{alias[t['id']]}'")
    return out


def clean_url(url: str) -> str:
    """Drop query strings and fragments (tracking IDs, share tokens)."""
    try:
        parts = urlsplit(url.strip())
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    except ValueError:
        return ""


def _split_needs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"[,;/\n]", text or "") if p.strip()]


def build_payload(trip: dict, travellers: list[dict], anchors: list[dict], personalise: bool):
    """Return (payload_sent_to_ai, redaction_log)."""
    log: list[str] = []
    alias = aliases(travellers)

    dietary = sorted({n.lower() for t in travellers for n in _split_needs(t.get("dietary", ""))})
    dietary += [n.lower() for n in _split_needs(trip.get("dietary", "")) if n.lower() not in dietary]
    mobility = sorted({scrub(n, travellers, log, "accessibility") for t in travellers for n in _split_needs(t.get("mobility", ""))})
    if any(t.get("dietary") for t in travellers):
        log.append("Dietary needs merged to group level (not attributed to individuals)")
    if mobility:
        log.append("Accessibility needs merged to group level (not attributed to individuals)")

    payload = {
        "destination": trip["destination"],
        "dates": trip["dates"],
        "daily_window": {"start": trip["day_start"], "end": trip["day_end"]},
        "budget_per_person_for_trip": trip["budget"],
        "currency": trip["currency"],
        "allowed_transport_modes": trip["transport_modes"],
        "accommodation_area": scrub(trip["accommodation"], travellers, log, "accommodation"),
        "crowd_tolerance_1to5": trip["crowd_tolerance"],
        "group_dietary_requirements": dietary,
        "group_accessibility_requirements": mobility,
        "extra_notes": scrub(trip.get("notes", ""), travellers, log, "trip notes"),
        "must_visits": [
            {
                "name": scrub(a["name"], travellers, log, "must-visit name"),
                "type": "FIXED (exact date/time, non-negotiable)" if a["kind"] == "fixed" else "FLEXIBLE (any day, must be included)",
                **({"date": a["date"], "start_time": a["time"]} if a["kind"] == "fixed" else {}),
                "duration_min": a["duration_min"],
                "note": scrub(a.get("note", ""), travellers, log, "must-visit note"),
            }
            for a in anchors
        ],
    }
    if any(a.get("note") or a.get("source_url") for a in anchors):
        log.append("Imported link URLs are not sent; only the extracted place name is")

    if personalise:
        payload["travellers"] = [
            {
                "alias": alias[t["id"]],
                "influence_weight": round(w, 3),
                "interests_0to5": t["interests"],
                "pace_1to5": t["pace"],
            }
            for t, w in zip(travellers, normalised_weights(travellers))
        ]
        log.append(f"{len(travellers)} traveller name(s) replaced with aliases (Traveller A, B, ...)")
    else:
        payload["travellers"] = "Personalisation is OFF: plan for a generic visitor with balanced interests."
        log.append("Personalisation off: no individual preference profiles sent")
    log.append("Never sent: names, emails, booking references, account IDs, exact hotel address")
    return payload, log


def normalised_weights(travellers: list[dict]) -> list[float]:
    raw = [max(float(t.get("weight", 1.0)), 0.0) for t in travellers]
    total = sum(raw)
    if total == 0:
        return [1 / len(travellers)] * len(travellers) if travellers else []
    return [r / total for r in raw]
