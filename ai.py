"""All Claude API calls. Every call takes only the de-identified payload built in privacy.py
and returns a validated Pydantic object (structured outputs), never free-form text."""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

import anthropic
import streamlit as st

import schemas
from config import FALLBACK_BETA, MODEL


class AIError(Exception):
    pass


def get_secret(name: str) -> str | None:
    try:
        value = st.secrets.get(name)
    except Exception:  # no secrets.toml at all
        value = None
    return value or os.environ.get(name)


def get_api_key() -> str | None:
    return get_secret("ANTHROPIC_API_KEY")


@st.cache_resource(show_spinner=False)
def _client(key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=key, max_retries=2)


def client() -> anthropic.Anthropic:
    key = get_api_key()
    if not key:
        raise AIError("No ANTHROPIC_API_KEY configured. Add it to .streamlit/secrets.toml (local) or the app's Secrets (Streamlit Cloud).")
    return _client(key)


SYSTEM = """You are the planning engine of a group travel itinerary app. You receive a de-identified
trip request as JSON and must return a structured itinerary.

Hard rules:
- FIXED must-visits keep their exact date and start time. Build the rest of that day around them.
- FLEXIBLE must-visits must appear somewhere in the trip.
- Every day starts from and ends at the accommodation, within the daily window.
- Respect group dietary and accessibility requirements at every meal and stop.
- Use only the allowed transport modes. Keep total cost per person within the budget.
- Include lunch and dinner as 'meal' stops at sensible times, plus a short 'rest' stop when the pace is relaxed.
- Respect the group's pace: do not over-pack days, avoid unnecessary back-and-forth travel.
- Respect crowd tolerance: schedule popular places at quieter times, and prefer good independent
  local businesses over congested tourist traps when they fit.
- If the forecast for a day is wet, favour indoor stops that day.

Fairness: each traveller (alias + influence_weight + interests) must be meaningfully served. A
minority interest must not be dropped just because most of the group prefers something else.
Higher-weight travellers can get somewhat more of their preferences, never all of it.

Privacy: never refer to an individual traveller in any text. Say "the group" (e.g. "meets the
group's accessibility requirement"), not "Traveller B has limited mobility".

Honesty: details come from your general knowledge, not live data. Set info_confidence honestly, use
'low' plus a caution for anything uncertain (new events, little-documented trails, possibly
closed venues). Do not invent precise facts you are unsure of; prefer well-established places.
Coordinates are approximate. Keep descriptions short."""


def _parse(output_format, user: str, effort: str, max_tokens: int = 20000, c: anthropic.Anthropic | None = None):
    c = c or client()
    kwargs = dict(
        model=MODEL,
        max_tokens=max_tokens,
        system=SYSTEM,
        messages=[{"role": "user", "content": user}],
        output_format=output_format,
        output_config={"effort": effort},
    )
    t0 = time.time()
    try:
        try:
            resp = c.beta.messages.parse(betas=[FALLBACK_BETA], fallbacks="default", **kwargs)
        except anthropic.BadRequestError as e:
            if "fallback" not in str(e).lower():
                raise
            resp = c.beta.messages.parse(**kwargs)
    except anthropic.AuthenticationError:
        raise AIError("The API key was rejected. Check ANTHROPIC_API_KEY in your secrets.")
    except anthropic.RateLimitError:
        raise AIError("Rate limited by the API. Wait a few seconds and try again.")
    except anthropic.APIStatusError as e:
        raise AIError(f"Claude API error ({e.status_code}): {e.message}")
    except anthropic.APIConnectionError:
        raise AIError("Could not reach the Claude API. Check your internet connection.")

    if resp.stop_reason == "refusal":
        raise AIError("The model declined this request. Try rephrasing it.")
    if resp.stop_reason == "max_tokens":
        raise AIError("The response was too long. Try fewer days or fewer options.")
    if resp.parsed_output is None:
        raise AIError("The model returned an unexpected format. Please try again.")
    meta = {
        "model": resp.model,
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
        "seconds": round(time.time() - t0, 1),
    }
    return resp.parsed_output, meta


def _j(obj) -> str:
    return json.dumps(obj, indent=1, ensure_ascii=False)


def generate_options(payload: dict, weather: dict, strategies: list[dict], effort: str):
    """Generate one itinerary per strategy, in parallel. Returns list of (strategy, option_dict | error_str, meta)."""
    c = client()  # resolve in the main thread; worker threads have no Streamlit context
    weather_txt = _j(weather["days"]) if weather["days"] else "No forecast available."

    def one(strategy):
        user = (
            f"TRIP REQUEST (de-identified):\n{_j(payload)}\n\n"
            f"WEATHER FORECAST BY DATE:\n{weather_txt}\n\n"
            f"PLANNING STRATEGY FOR THIS VARIANT: {strategy['instruction']}\n\n"
            f"Plan every date in the request. Title the option to reflect the strategy."
        )
        try:
            opt, meta = _parse(schemas.ItineraryOption, user, effort, c=c)
            return strategy, opt.model_dump(), meta
        except AIError as e:
            return strategy, str(e), None

    with ThreadPoolExecutor(max_workers=len(strategies)) as pool:
        return list(pool.map(one, strategies))


def extract_link(url: str, caption: str, destination: str):
    user = (
        "A user pasted a social media / web link they saw while researching the trip. Identify the single "
        "place or activity it refers to, using the URL path and the caption text only (you cannot open the link). "
        "If it is ambiguous, set found=false or confidence='low' and explain in notes.\n\n"
        f"Trip destination: {destination}\nURL: {url or '(none)'}\nCaption / description: {caption or '(none)'}"
    )
    return _parse(schemas.ExtractedPlace, user, "low", 4000)


def swap_alternatives(payload: dict, day: dict, stop: dict):
    user = (
        f"TRIP REQUEST (de-identified):\n{_j(payload)}\n\nTHE DAY AS PLANNED:\n{_j(day)}\n\n"
        f"The group wants to replace '{stop['name']}' ({stop['start_time']}-{stop['end_time']}). Suggest 3 "
        "alternatives that fit the same time slot and route, are not already in the day, and serve the group. "
        "Each alternative's transport_to_next should reach the stop that currently follows it."
    )
    return _parse(schemas.SwapResult, user, "low", 12000)


def explain_contrast(payload: dict, day: dict, stop: dict, alternative: str):
    user = (
        f"TRIP REQUEST (de-identified):\n{_j(payload)}\n\nTHE DAY AS PLANNED:\n{_j(day)}\n\n"
        f"The user asks: why '{stop['name']}' instead of '{alternative}'? Compare them on the criteria the user set "
        "(time slot fit, travel time, cost vs budget, group interests, crowds, weather, accessibility). Name the "
        "single deciding factor, and a concrete counterfactual: what setting change would make the alternative win."
    )
    return _parse(schemas.ContrastiveExplanation, user, "low", 6000)


def replan_day(payload: dict, weather: dict, day: dict, event: str, now_time: str):
    user = (
        f"TRIP REQUEST (de-identified):\n{_j(payload)}\n\nWEATHER: {_j(weather['days']) if weather['days'] else 'n/a'}\n\n"
        f"CURRENT PLAN FOR THIS DAY:\n{_j(day)}\n\n"
        f"LIVE UPDATE at {now_time}: \"{event}\"\n\n"
        "Re-plan this day from that time onwards. Keep stops before that time unchanged, keep FIXED must-visits, "
        "change as little as needed, and list each change in change_summary."
    )
    return _parse(schemas.ReplanResult, user, "low", 16000)


def explore(destination: str, tags: list[str], payload: dict):
    user = (
        f"Destination: {destination}\nTags requested: {', '.join(tags)}\n"
        f"Group context (de-identified): dietary={payload['group_dietary_requirements']}, "
        f"crowd_tolerance={payload['crowd_tolerance_1to5']}, budget={payload['budget_per_person_for_trip']} {payload['currency']}\n\n"
        "List 8 places matching these tags. At least half should be lesser-known local spots (hidden_gem=true) "
        "rather than the most famous attractions."
    )
    return _parse(schemas.ExploreResult, user, "low", 8000)
