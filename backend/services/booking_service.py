import os
import logging
from typing import List, Optional
from datetime import date, timedelta

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://booking-com15.p.rapidapi.com"
API_KEY = os.environ.get("RAPIDAPI_KEY")
API_HOST = os.environ.get("BOOKING_API_HOST", "booking-com15.p.rapidapi.com")
ENABLE_EXTERNAL = os.environ.get("ENABLE_HOTEL_API", "0") == "1"


async def _resolve_booking_destination_id(city: str, headers: dict) -> Optional[str]:
    """Resolve a city name into a Booking.com destination ID (dest_id)."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Use the endpoint from the RapidAPI playground.
            resp = await client.get(
                BASE_URL + "/api/v1/hotels/searchDestination",
                params={"query": city, "search_type": "CITY", "languagecode": "en-us"},
                headers=headers,
            )
            resp.raise_for_status()
            payload = resp.json()
        data = payload.get("data") or payload.get("result") or []
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                return str(first.get("dest_id") or first.get("destId") or "")
    except Exception as exc:
        logger.error(f"booking_service location lookup error: {exc}")
    return None


async def search_hotels(
    city: Optional[str] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    limit: int = 20,
) -> Optional[List[dict]]:
    """Query the Booking.com RapidAPI endpoint and return mapped hotels.

    If the call fails, return None so callers can fall back to seeded data.
    """
    if not ENABLE_EXTERNAL:
        logger.info("Hotel API disabled via ENABLE_HOTEL_API=0; using seeded data")
        return None
    if not API_KEY:
        logger.warning("BOOKING_API_KEY not set; skipping hotel lookup")
        return None

    params = {}
    if city:
        dest_id = await _resolve_booking_destination_id(city, headers={
            "x-rapidapi-key": API_KEY,
            "x-rapidapi-host": API_HOST,
        })
        if dest_id:
            params["dest_id"] = dest_id
            params["search_type"] = "CITY"
        else:
            params["city_name"] = city
    if max_price is not None:
        # Best-effort: not all Booking endpoints accept max_price
        params["max_price"] = max_price
    if min_rating is not None:
        params["min_review_score"] = min_rating
    # Some Booking endpoints require dates; provide a sensible default window.
    today = date.today()
    params["checkin_date"] = today.isoformat()
    params["checkout_date"] = (today + timedelta(days=2)).isoformat()
    params["page_number"] = 1
    params["adults"] = 1
    params["children_age"] = "0,17"
    params["room_qty"] = 1
    params["units"] = "metric"
    params["temperature_unit"] = "c"
    params["languagecode"] = "en-us"
    params["currency_code"] = "AED"
    params["location"] = "US"

    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": API_HOST,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(BASE_URL + "/api/v1/hotels/searchHotels", params=params, headers=headers)
            if resp.status_code >= 400:
                logger.error(f"booking_service http {resp.status_code}: {resp.text}")
            resp.raise_for_status()
            payload = resp.json()

        # guessing at structure: payload['result'] or payload['data']; adjust when you have real sample
        # hotel-search endpoint returns { status, message, data: { hotels: [...] } }
        raw_parent = payload.get("data") or {}
        raw_list = raw_parent.get("hotels") if isinstance(raw_parent, dict) else None
        if not raw_list:
            # previous heuristics for generic list
            raw_list = payload.get("result") or payload.get("data") or []
        if not raw_list:
            msg = payload.get("message")
            logger.info(f"booking_service empty result; payload keys={list(payload.keys())}; message={msg}")

        # if we still have suggestions (destinations) rather than hotel items,
        # signal fallback by returning None
        if raw_list and isinstance(raw_list, list):
            first = raw_list[0]
            if isinstance(first, dict) and ("city_name" in first or "dest_id" in first):
                logger.info("booking_service received location suggestions instead of hotel list")
                return None

        hotels = []
        for entry in (raw_list or [])[:limit]:
            prop = entry.get("property") or {}
            # description can be the accessibilityLabel or empty
            description = entry.get("accessibilityLabel", "")
            # price block may be nested
            price_info = prop.get("priceBreakdown", {}).get("grossPrice", {})
            price_value = price_info.get("value", 0)
            currency = price_info.get("currency", "")

            # pick first photo if available
            photos = prop.get("photoUrls") or []
            image = photos[0] if photos else ""

            hotels.append(
                {
                    "id": str(prop.get("id", "")),
                    "name": prop.get("name", ""),
                    "location": prop.get("countryCode", ""),
                    "city": city or "",  # API doesn't echo city reliably
                    "rating": float(prop.get("reviewScore", 0)),
                    "price_per_night": float(price_value),
                    "amenities": [],
                    "platform": "Booking.com",
                    "deal_url": "",  # no direct link provided in sample
                    "image_url": image,
                    "description": description,
                }
            )
        return hotels
    except Exception as exc:
        logger.error(f"booking_service error: {exc}")
        return None
