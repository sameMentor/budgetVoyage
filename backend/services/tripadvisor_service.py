import os
import logging
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://tripadvisor16.p.rapidapi.com"
API_KEY = os.environ.get("RAPIDAPI_KEY")
API_HOST = os.environ.get("TRIPADVISOR_API_HOST", "tripadvisor16.p.rapidapi.com")
ENABLE_EXTERNAL = os.environ.get("ENABLE_RESTAURANT_API", "0") == "1"


async def _resolve_tripadvisor_location_id(city: str, headers: dict) -> Optional[str]:
    """Resolve city name into a TripAdvisor locationId."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                BASE_URL + "/api/v1/location/search",
                params={"query": city, "limit": 1, "language": "en_US"},
                headers=headers,
            )
            resp.raise_for_status()
            payload = resp.json()
        data = payload.get("data", [])
        if isinstance(data, list) and data:
            return str(data[0].get("locationId") or "")
    except Exception as exc:
        logger.error(f"tripadvisor_service location lookup error: {exc}")
    return None


async def search_restaurants(
    city: Optional[str] = None,
    cuisine: Optional[str] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    limit: int = 20,
) -> Optional[List[dict]]:
    """Query TripAdvisor via RapidAPI and map to our restaurant schema.

    Uses TripAdvisor `/api/v1/restaurant/searchRestaurants`.
    """
    if not ENABLE_EXTERNAL:
        logger.info("Restaurant API disabled via ENABLE_RESTAURANT_API=0; using seeded data")
        return None
    if not API_KEY:
        logger.warning("TRIPADVISOR_API_KEY not set; skipping restaurant lookup")
        return None

    params = {}
    if city:
        # TripAdvisor uses a numeric locationId; resolve from city name
        location_id = await _resolve_tripadvisor_location_id(city, headers={
            "x-rapidapi-key": API_KEY,
            "x-rapidapi-host": API_HOST,
        })
        if location_id:
            params["locationId"] = location_id
    if cuisine:
        params["cuisine"] = cuisine
    if max_price is not None:
        params["max_price"] = max_price
    if min_rating is not None:
        params["min_rating"] = min_rating
    params["limit"] = limit

    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": API_HOST,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(BASE_URL + "/api/v1/restaurant/searchRestaurants", params=params, headers=headers)
            if resp.status_code >= 400:
                logger.error(f"tripadvisor_service http {resp.status_code}: {resp.text}")
            resp.raise_for_status()
            payload = resp.json()

        raw_list = payload.get("data", {}).get("data", []) or payload.get("data", []) or payload.get("result", [])
        if not raw_list:
            msg = payload.get("message")
            logger.info(f"tripadvisor_service empty result; payload keys={list(payload.keys())}; message={msg}")
        restaurants = []
        for item in raw_list[:limit]:
            price_tag = item.get("priceTag", "")
            # convert $$$$ to a rough number e.g. len * 50
            avg_price = float(len(price_tag) * 50) if price_tag else 0.0
            restaurants.append(
                {
                    "id": str(item.get("locationId", "")),
                    "name": item.get("name", ""),
                    "location": item.get("parentGeoName", ""),
                    "city": item.get("parentGeoName", ""),
                    "cuisine": ", ".join(item.get("establishmentTypeAndCuisineTags", [])),
                    "avg_price": avg_price,
                    "rating": float(item.get("averageRating", 0)),
                    "platform": "TripAdvisor",
                    "deal_url": "",  # TripAdvisor doesn't provide direct booking link
                    "image_url": item.get("heroImgUrl", ""),
                    "description": "",  # could aggregate review snippets if desired
                }
            )
        return restaurants
    except Exception as exc:
        logger.error(f"tripadvisor_service error: {exc}")
        return None
