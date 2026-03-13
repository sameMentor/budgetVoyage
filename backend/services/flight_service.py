import os
import logging
from typing import List, Optional

import httpx
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

BASE_URL = "https://api.aviationstack.com/v1/"
API_KEY = os.environ.get("AVIATIONSTACK_KEY")
ENABLE_EXTERNAL = os.environ.get("ENABLE_FLIGHT_API", "0") == "1"

async def search_flights(
    source: Optional[str] = None,
    destination: Optional[str] = None,
    max_price: Optional[float] = None,
    stops: Optional[str] = None,
    limit: int = 20,
) -> Optional[List[dict]]:
    """Call Aviationstack and map results to the frontend schema.

    Returns a list of dictionaries suitable for the Hotel/Flight model
    or None if the external service could not be reached.
    """
    if not ENABLE_EXTERNAL:
        logger.info("Flight API disabled via ENABLE_FLIGHT_API=0; using seeded data")
        return None
    if not API_KEY:
        logger.warning("AVIATIONSTACK_KEY is not set; skipping external lookup")
        return None

    params = {"access_key": API_KEY, "limit": limit}
    if source:
        params["dep_iata"] = source  # crude; adjust per actual API
    if destination:
        params["arr_iata"] = destination
    # Aviationstack doesn't expose price/stops filters in free tier; we'll ignore for now

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(BASE_URL + "flights", params=params)
            resp.raise_for_status()
            data = resp.json().get("data", [])

        results = []
        now = datetime.now(timezone.utc)
        for item in data[:limit]:
            # mapping; many fields may not exist depending on subscription level
            dep = item.get("departure", {})
            arr = item.get("arrival", {})
            airline = item.get("airline", {}).get("name") or ""
            flight_no = item.get("flight", {}).get("number") or item.get("flight", {}).get("iata", "")
            dep_time = dep.get("scheduled") or ""
            arr_time = arr.get("scheduled") or ""
            # compute duration if possible
            duration = 0.0
            try:
                if dep_time and arr_time:
                    # aviationstack returns ISO strings with offset
                    dt1 = datetime.fromisoformat(dep_time)
                    dt2 = datetime.fromisoformat(arr_time)
                    duration = (dt2 - dt1).total_seconds() / 3600
            except Exception:
                pass

            days_left = 0
            try:
                if dep_time:
                    dep_dt = datetime.fromisoformat(dep_time)
                    days_left = max(0, (dep_dt - now).days)
            except Exception:
                pass

            results.append(
                {
                    "id": f"{item.get('flight_date','')}_{flight_no}",
                    "airline": airline,
                    "flight": flight_no,
                    "source_city": dep.get("airport") or dep.get("iata", ""),
                    "destination_city": arr.get("airport") or arr.get("iata", ""),
                    "departure_time": dep_time,
                    "arrival_time": arr_time,
                    "duration": duration,
                    "stops": item.get("stop", 0),
                    "class_type": "",
                    "days_left": days_left,
                    "price": 0.0,  # external APIs rarely provide price in free tier
                }
            )
        return results
    except Exception as exc:
        logger.error(f"flight_service error: {exc}")
        return None
