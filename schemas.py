"""Structured-output schemas. Claude must answer in exactly these shapes, so the app never
renders free-form model output (data containment)."""

from typing import Literal

from pydantic import BaseModel, Field

Mode = Literal["Walk", "Public transport", "Ride-hailing", "Drive"]


class Attributes(BaseModel):
    """How strongly a stop serves each interest dimension, 0.0-1.0."""

    nature: float
    culture: float
    food: float
    shopping: float
    nightlife: float
    adventure: float
    relaxation: float


class TransportOption(BaseModel):
    mode: Mode
    duration_min: int
    cost: float = Field(description="Cost per person in the trip currency")
    details: str = Field(description="Short route detail, e.g. 'MRT Downtown Line, 4 stops'")


class Stop(BaseModel):
    name: str
    kind: Literal["activity", "meal", "rest"]
    start_time: str = Field(description="HH:MM, 24h")
    end_time: str = Field(description="HH:MM, 24h")
    area: str
    lat: float = Field(description="Approximate latitude")
    lon: float = Field(description="Approximate longitude")
    description: str = Field(description="One sentence, max 25 words")
    est_cost_per_person: float
    crowd_level: Literal["low", "moderate", "high"] = Field(description="Expected crowd at the scheduled time")
    indoor: bool
    is_anchor: bool = Field(description="True only for the user's locked must-visits")
    hidden_gem: bool = Field(description="True for lesser-known / independent local places")
    booking_info: str = Field(description="How to book / ticket price info, or 'Walk-in'")
    info_confidence: Literal["high", "medium", "low"] = Field(
        description="Confidence in the factual details (hours, price, safety) of this stop"
    )
    caution: str = Field(description="Safety or data-gap caveat; empty string if none")
    attributes: Attributes
    why: list[str] = Field(description="2-4 short criteria chips, e.g. 'Within budget', 'Indoor: rain forecast'")
    transport_to_next: list[TransportOption] = Field(
        description="1-3 options to reach the NEXT stop, recommended option first; empty for the last stop"
    )


class Day(BaseModel):
    day_number: int
    date: str
    theme: str
    from_hotel: TransportOption = Field(description="Getting from accommodation to the first stop")
    stops: list[Stop]
    to_hotel: TransportOption = Field(description="Getting from the last stop back to accommodation")
    walking_km: float
    pace_note: str
    wet_weather_backup: str = Field(description="What to swap if it rains, one sentence")


class Tradeoff(BaseModel):
    chosen: str
    alternative: str
    deciding_factor: str = Field(description="The single factor that decided it, in the user's terms")
    counterfactual: str = Field(description="What change to the user's settings would flip the decision")


class ItineraryOption(BaseModel):
    title: str
    summary: str = Field(description="Two sentences")
    hotel_lat: float
    hotel_lon: float
    days: list[Day]
    tradeoffs: list[Tradeoff] = Field(description="3-5 notable decisions with alternatives considered")
    group_balance_note: str = Field(
        description="How the plan balances the group. Refer to 'the group', never to an individual traveller"
    )
    warnings: list[str]


class ExtractedPlace(BaseModel):
    found: bool
    place_name: str
    area: str
    city: str
    matches_destination: bool
    category: str
    suggested_duration_min: int
    why_people_go: str
    confidence: Literal["high", "medium", "low"]
    notes: str


class Alternative(BaseModel):
    stop: Stop
    vs_current: str = Field(description="How it compares to the current stop, in the user's terms")


class SwapResult(BaseModel):
    alternatives: list[Alternative]


class Comparison(BaseModel):
    criterion: str
    chosen: str
    alternative: str


class ContrastiveExplanation(BaseModel):
    deciding_factor: str
    comparisons: list[Comparison]
    counterfactual: str
    verdict: Literal["keep_current", "alternative_is_comparable", "alternative_is_better"]


class ReplanResult(BaseModel):
    change_summary: list[str]
    updated_day: Day


class Place(BaseModel):
    name: str
    area: str
    tags: list[str]
    description: str
    crowd_level: Literal["low", "moderate", "high"]
    est_cost_per_person: float
    hidden_gem: bool
    best_time: str
    lat: float
    lon: float


class ExploreResult(BaseModel):
    places: list[Place]
