import os
import os
import json
import ast
import logging
from typing import List, Optional
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://api.railradar.org/api/v1"
API_KEY = os.environ.get("RAILRADAR_API_KEY")
ENABLE_TRAIN_API = os.environ.get("ENABLE_TRAIN_API", "0") == "1"
ROOT_DIR = Path(__file__).resolve().parent.parent
_TRAIN_JSON_CACHE = None


def _load_trains_json() -> List[dict]:
    global _TRAIN_JSON_CACHE
    if _TRAIN_JSON_CACHE is not None:
        return _TRAIN_JSON_CACHE
    path = ROOT_DIR / "trains.json"
    if not path.exists():
        logger.warning("trains.json not found")
        _TRAIN_JSON_CACHE = []
        return _TRAIN_JSON_CACHE
    with open(path, "r", encoding="utf-8") as f:
        _TRAIN_JSON_CACHE = json.load(f)
    return _TRAIN_JSON_CACHE


def _parse_station_list(raw: Optional[str]) -> List[dict]:
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        return ast.literal_eval(raw)
    except Exception:
        return []


def _station_name_contains(stations: List[dict], city: str) -> bool:
    city_l = city.strip().lower()
    if not city_l:
        return False
    for st in stations:
        name = str(st.get("stationName") or "").lower()
        if city_l in name:
            return True
    return False


async def search_trains(query: Optional[str] = None, limit: int = 20) -> Optional[List[dict]]:
    """Search trains by name or number using RailRadar."""
    if not query:
        return []
    if not API_KEY:
        logger.warning("RAILRADAR_API_KEY not set; skipping train lookup")
        return None

    headers = {"X-API-Key": API_KEY}
    params = {"query": query}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BASE_URL}/search/trains", params=params, headers=headers)
            if resp.status_code >= 400:
                logger.error(f"train_service http {resp.status_code}: {resp.text}")
            resp.raise_for_status()
            payload = resp.json()

        # API returns a list of train objects
        raw_list = payload if isinstance(payload, list) else payload.get("data", [])
        results = []
        for item in raw_list[:limit]:
            results.append(
                {
                    "id": str(item.get("trainNumber") or item.get("trainNo") or ""),
                    "train_number": str(item.get("trainNumber") or item.get("trainNo") or ""),
                    "train_name": item.get("trainName") or "",
                    "source_station_code": item.get("sourceStationCode") or "",
                    "destination_station_code": item.get("destinationStationCode") or "",
                }
            )
        return results
    except Exception as exc:
        logger.error(f"train_service error: {exc}")
        return None


async def search_trains_between(
    from_station: Optional[str] = None,
    to_station: Optional[str] = None,
    travel_date: Optional[str] = None,
    limit: int = 50,
) -> Optional[List[dict]]:
    """Search trains between two stations with optional date."""
    if not from_station or not to_station:
        return []
    if not ENABLE_TRAIN_API:
        trains = _load_trains_json()
        results = []
        for item in trains:
            if item.get("errorMessage"):
                continue
            stations = _parse_station_list(item.get("stationList"))
            if not stations:
                continue
            codes = [str(st.get("stationCode") or "") for st in stations]
            if from_station not in codes or to_station not in codes:
                continue
            first = stations[0]
            last = stations[-1]
            results.append(
                {
                    "id": str(item.get("trainNumber") or ""),
                    "train_number": str(item.get("trainNumber") or ""),
                    "train_name": item.get("trainName") or "",
                    "source_station_code": first.get("stationCode") or item.get("stationFrom") or "",
                    "destination_station_code": last.get("stationCode") or item.get("stationTo") or "",
                    "departure_time": first.get("departureTime") or "",
                    "arrival_time": last.get("arrivalTime") or "",
                    "travel_time": "",
                    "run_days": [],
                    "available_classes": [],
                    "train_type": "",
                    "booking_url": "",
                }
            )
            if len(results) >= limit:
                break
        return results

    if not API_KEY:
        logger.warning("RAILRADAR_API_KEY not set; skipping train lookup")
        return None

    headers = {"X-API-Key": API_KEY}
    params = {"from": from_station, "to": to_station}
    if travel_date:
        params["date"] = travel_date

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BASE_URL}/trains/between", params=params, headers=headers)
            if resp.status_code >= 400:
                logger.error(f"train_service http {resp.status_code}: {resp.text}")
            resp.raise_for_status()
            payload = resp.json()

        trains = []
        if isinstance(payload, dict):
            trains = payload.get("trains") or []
            if not trains:
                data_block = payload.get("data")
                if isinstance(data_block, dict):
                    trains = data_block.get("trains") or data_block.get("results") or []
                elif isinstance(data_block, list):
                    trains = data_block
        if not trains and isinstance(payload, dict):
            msg = payload.get("message") or payload.get("error")
            data_block = payload.get("data")
            data_type = type(data_block).__name__
            data_keys = list(data_block.keys()) if isinstance(data_block, dict) else None
            logger.info(
                f"train_service between empty; payload keys={list(payload.keys())}; "
                f"data_type={data_type}; data_keys={data_keys}; message={msg}"
            )
        results = []
        for idx, item in enumerate((trains or [])[:limit]):
            segment = item.get("journeySegment") or {}
            seg_from = segment.get("from") or {}
            seg_to = segment.get("to") or {}
            train_number = str(
                item.get("number")
                or item.get("trainNumber")
                or item.get("trainNo")
                or ""
            )
            train_name = (
                item.get("name")
                or item.get("trainName")
                or item.get("train_name")
                or ""
            )
            if idx == 0 and not train_name:
                logger.info(f"train_service between mapping keys={list(item.keys())}")
            results.append(
                {
                    "id": train_number,
                    "train_number": train_number,
                    "train_name": train_name,
                    "source_station_code": (
                        seg_from.get("code")
                        or item.get("fromStationCode")
                        or item.get("from")
                        or ""
                    ),
                    "destination_station_code": (
                        seg_to.get("code")
                        or item.get("toStationCode")
                        or item.get("to")
                        or ""
                    ),
                    "departure_time": segment.get("departureTime") or "",
                    "arrival_time": segment.get("arrivalTime") or "",
                    "travel_time": segment.get("travelTime") or "",
                    "run_days": item.get("runDays") or [],
                    "available_classes": item.get("availableClasses") or [],
                    "train_type": item.get("type") or "",
                    "booking_url": item.get("bookingUrl") or "",
                }
            )
        return results
    except Exception as exc:
        logger.error(f"train_service error: {exc}")
        return None


async def search_stations(query: Optional[str] = None, limit: int = 20) -> Optional[List[dict]]:
    """Search stations by name or code."""
    if not query:
        return []
    if not API_KEY:
        logger.warning("RAILRADAR_API_KEY not set; skipping station lookup")
        return None

    headers = {"X-API-Key": API_KEY}
    params = {"query": query}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BASE_URL}/search/stations", params=params, headers=headers)
            if resp.status_code >= 400:
                logger.error(f"train_service http {resp.status_code}: {resp.text}")
            resp.raise_for_status()
            payload = resp.json()

        raw_list = []
        if isinstance(payload, list):
            raw_list = payload
        elif isinstance(payload, dict):
            for key in ("data", "stations", "results"):
                val = payload.get(key)
                if isinstance(val, list):
                    raw_list = val
                    break
                if isinstance(val, dict):
                    for subkey in ("stations", "results", "data"):
                        subval = val.get(subkey)
                        if isinstance(subval, list):
                            raw_list = subval
                            break
                    if raw_list:
                        break
        if not raw_list and isinstance(payload, dict):
            logger.info(f"train_service stations empty; payload keys={list(payload.keys())}")

        results = []
        for item in (raw_list or [])[:limit]:
            results.append(
                {
                    "code": item.get("code") or item.get("stationCode") or "",
                    "name": item.get("name") or item.get("stationName") or "",
                    "state": item.get("state") or "",
                }
            )
        return results
    except Exception as exc:
        logger.error(f"train_service error: {exc}")
        return None


async def _fetch_stations(client: httpx.AsyncClient, query: str, limit: int) -> List[dict]:
    headers = {"X-API-Key": API_KEY}
    params = {"query": query}
    resp = await client.get(f"{BASE_URL}/search/stations", params=params, headers=headers)
    if resp.status_code >= 400:
        logger.error(f"train_service http {resp.status_code}: {resp.text}")
    resp.raise_for_status()
    payload = resp.json()
    raw_list = []
    if isinstance(payload, list):
        raw_list = payload
    elif isinstance(payload, dict):
        for key in ("data", "stations", "results"):
            val = payload.get(key)
            if isinstance(val, list):
                raw_list = val
                break
            if isinstance(val, dict):
                for subkey in ("stations", "results", "data"):
                    subval = val.get(subkey)
                    if isinstance(subval, list):
                        raw_list = subval
                        break
                if raw_list:
                    break
    results = []
    for item in (raw_list or [])[:limit]:
        results.append(
            {
                "code": item.get("code") or item.get("stationCode") or "",
                "name": item.get("name") or item.get("stationName") or "",
                "state": item.get("state") or "",
            }
        )
    return results


async def _fetch_trains_between(
    client: httpx.AsyncClient,
    from_station: str,
    to_station: str,
    travel_date: Optional[str],
) -> List[dict]:
    headers = {"X-API-Key": API_KEY}
    params = {"from": from_station, "to": to_station}
    if travel_date:
        params["date"] = travel_date
    resp = await client.get(f"{BASE_URL}/trains/between", params=params, headers=headers)
    if resp.status_code >= 400:
        logger.error(f"train_service http {resp.status_code}: {resp.text}")
    resp.raise_for_status()
    payload = resp.json()
    trains = []
    if isinstance(payload, dict):
        trains = payload.get("trains") or []
        if not trains:
            data_block = payload.get("data")
            if isinstance(data_block, dict):
                trains = data_block.get("trains") or data_block.get("results") or []
            elif isinstance(data_block, list):
                trains = data_block
    return trains or []


async def search_trains_between_cities(
    from_city: Optional[str] = None,
    to_city: Optional[str] = None,
    travel_date: Optional[str] = None,
    station_limit: int = 3,
    limit: int = 50,
) -> Optional[List[dict]]:
    """Search trains between two city names by sampling top stations."""
    if not from_city or not to_city:
        return []

    # Prefer dataset fallback for stability
    if not ENABLE_TRAIN_API:
        trains = _load_trains_json()
        results = []
        for item in trains:
            if item.get("errorMessage"):
                continue
            stations = _parse_station_list(item.get("stationList"))
            if not stations:
                continue
            if not _station_name_contains(stations, from_city):
                continue
            if not _station_name_contains(stations, to_city):
                continue

            first = stations[0]
            last = stations[-1]
            results.append(
                {
                    "id": str(item.get("trainNumber") or ""),
                    "train_number": str(item.get("trainNumber") or ""),
                    "train_name": item.get("trainName") or "",
                    "source_station_code": first.get("stationCode") or item.get("stationFrom") or "",
                    "destination_station_code": last.get("stationCode") or item.get("stationTo") or "",
                    "departure_time": first.get("departureTime") or "",
                    "arrival_time": last.get("arrivalTime") or "",
                    "travel_time": "",
                    "run_days": [],
                    "available_classes": [],
                    "train_type": "",
                    "booking_url": "",
                }
            )
            if len(results) >= limit:
                break
        return results

    if not API_KEY:
        logger.warning("RAILRADAR_API_KEY not set; skipping train lookup")
        return None

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            from_stations = await _fetch_stations(client, from_city, station_limit)
            to_stations = await _fetch_stations(client, to_city, station_limit)

            if not from_stations or not to_stations:
                return []

            combined = []
            for fs in from_stations:
                for ts in to_stations:
                    trains = await _fetch_trains_between(client, fs["code"], ts["code"], travel_date)
                    combined.extend(trains)

        seen = set()
        results = []
        for item in combined:
            number = (
                item.get("number")
                or item.get("trainNumber")
                or item.get("trainNo")
                or ""
            )
            key = str(number)
            if key and key in seen:
                continue
            if key:
                seen.add(key)

            segment = item.get("journeySegment") or {}
            seg_from = segment.get("from") or {}
            seg_to = segment.get("to") or {}
            train_number = str(number)
            train_name = (
                item.get("name")
                or item.get("trainName")
                or item.get("train_name")
                or ""
            )
            results.append(
                {
                    "id": train_number,
                    "train_number": train_number,
                    "train_name": train_name,
                    "source_station_code": (
                        seg_from.get("code")
                        or item.get("fromStationCode")
                        or item.get("from")
                        or ""
                    ),
                    "destination_station_code": (
                        seg_to.get("code")
                        or item.get("toStationCode")
                        or item.get("to")
                        or ""
                    ),
                    "departure_time": segment.get("departureTime") or "",
                    "arrival_time": segment.get("arrivalTime") or "",
                    "travel_time": segment.get("travelTime") or "",
                    "run_days": item.get("runDays") or [],
                    "available_classes": item.get("availableClasses") or [],
                    "train_type": item.get("type") or "",
                    "booking_url": item.get("bookingUrl") or "",
                }
            )

        return results[:limit]
    except Exception as exc:
        logger.error(f"train_service error: {exc}")
        return None
