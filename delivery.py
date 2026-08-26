"""Route-based delivery cost calculation for Cindy Bakes."""

from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv

from business_rules import DELIVERY_ORIGIN, DELIVERY_RATE_PER_KM


def _response_json(response: Any) -> dict:
    if hasattr(response, "json"):
        return response.json() if callable(response.json) else {}
    if isinstance(response, dict):
        return response.get("json", {})
    return {}


def _response_status(response: Any) -> int:
    if hasattr(response, "status_code"):
        return int(response.status_code)
    if isinstance(response, dict):
        return int(response.get("status_code", 200))
    return 200


def _get_ors_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("ORS_API_KEY")
    if not api_key or not str(api_key).strip():
        raise RuntimeError("ORS_API_KEY is missing. Add it to .env before calculating delivery costs.")
    return str(api_key).strip()


def _geocode_location(location: str, api_key: str) -> tuple[float, float]:
    location_text = str(location).strip()
    if not location_text:
        raise ValueError("Please provide a delivery location.")

    params = {
        "api_key": api_key,
        "text": location_text,
        "boundary.country": "KE",
        "size": 5,
    }
    response = requests.get("https://api.openrouteservice.org/geocode/search", params=params, timeout=20)
    status_code = _response_status(response)
    if status_code != 200:
        raise RuntimeError("The maps service is currently unavailable. Please try again later or ask a human for help.")

    data = _response_json(response)
    features = data.get("features") or []
    if not features:
        raise ValueError("I couldn’t find that delivery location. Please provide a more specific area or address.")
    if len(features) > 1:
        raise ValueError("That delivery location is too vague or ambiguous. Please give a more specific area, suburb, or address.")

    coordinates = features[0].get("geometry", {}).get("coordinates")
    if not coordinates or len(coordinates) < 2:
        raise ValueError("I couldn’t find that delivery location. Please provide a more specific area or address.")

    longitude = float(coordinates[0])
    latitude = float(coordinates[1])
    return (latitude, longitude)


def _calculate_route_distance(origin: str, destination: str, api_key: str) -> float:
    origin_lat, origin_lon = _geocode_location(origin, api_key)
    destination_lat, destination_lon = _geocode_location(destination, api_key)

    payload = {
        "coordinates": [
            [origin_lon, origin_lat],
            [destination_lon, destination_lat],
        ]
    }
    response = requests.post(
        "https://api.openrouteservice.org/v2/directions/driving-car",
        json=payload,
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json, application/geo+json",
        },
        timeout=20,
    )
    status_code = _response_status(response)
    if status_code != 200:
        raise RuntimeError("The maps service is currently unavailable. Please try again later or ask a human for help.")

    data = _response_json(response)
    routes = data.get("routes") or []
    if not routes:
        raise ValueError("I couldn’t calculate a driving route for that delivery location. Please provide a more specific address.")

    route = routes[0]
    segments = route.get("segments") or []
    total_distance_m = 0.0
    for segment in segments:
        total_distance_m += float(segment.get("distance") or 0.0)
    if total_distance_m == 0.0:
        summary = route.get("summary") or {}
        total_distance_m = float(summary.get("distance") or 0.0)
    if total_distance_m == 0.0:
        raise ValueError("I couldn’t calculate a driving route for that delivery location. Please provide a more specific address.")

    return total_distance_m / 1000.0


def calculate_delivery_cost(delivery_location: str, origin: str = DELIVERY_ORIGIN) -> dict:
    """Return actual road-driving distance and delivery charge for the given location."""
    location = str(delivery_location).strip()
    if not location:
        raise ValueError("Please provide a delivery location.")

    api_key = _get_ors_api_key()
    driving_distance_km = _calculate_route_distance(origin, location, api_key)
    delivery_cost = round(driving_distance_km * DELIVERY_RATE_PER_KM, 2)

    return {
        "delivery_origin": origin,
        "delivery_location": location,
        "delivery_distance_km": round(driving_distance_km, 2),
        "delivery_rate_per_km": DELIVERY_RATE_PER_KM,
        "delivery_cost": delivery_cost,
    }
