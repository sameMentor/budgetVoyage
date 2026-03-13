import json
import ast
import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import numpy as np
import xgboost as xgb

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent

_DATA_CACHE: Dict[str, pd.DataFrame] = {}
_MODEL_CACHE: Dict[str, xgb.Booster] = {}


def _safe_float(value) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _load_csv(name: str, filename: str) -> pd.DataFrame:
    if name in _DATA_CACHE:
        return _DATA_CACHE[name]
    path = ROOT_DIR / filename
    if not path.exists():
        logger.warning(f"{filename} not found")
        df = pd.DataFrame()
        _DATA_CACHE[name] = df
        return df
    df = pd.read_csv(path, low_memory=False)
    _DATA_CACHE[name] = df
    return df


def _load_trains_json() -> List[dict]:
    path = ROOT_DIR / "trains.json"
    if not path.exists():
        logger.warning("trains.json not found")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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


def _train_model(kind: str, df: pd.DataFrame, feature_cols: List[str], target_col: str) -> xgb.Booster:
    if kind in _MODEL_CACHE:
        return _MODEL_CACHE[kind]
    if df.empty:
        d = xgb.DMatrix(np.zeros((1, len(feature_cols))), label=np.zeros(1))
        booster = xgb.train({"objective": "reg:squarederror"}, d, num_boost_round=1)
        _MODEL_CACHE[kind] = booster
        return booster
    X = df[feature_cols].fillna(0.0).to_numpy()
    y = df[target_col].fillna(0.0).to_numpy()
    dtrain = xgb.DMatrix(X, label=y)
    params = {
        "max_depth": 4,
        "eta": 0.1,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "objective": "reg:squarederror",
        "seed": 42,
    }
    booster = xgb.train(params, dtrain, num_boost_round=80)
    _MODEL_CACHE[kind] = booster
    return booster


def _prepare_flights(from_city: str, to_city: str) -> pd.DataFrame:
    df = _load_csv("flights", "flights.csv")
    if df.empty:
        return df
    df = df.copy()
    df["price"] = df["price"].apply(_safe_float)
    df["duration"] = df["duration"].apply(_safe_float)
    df["stops"] = df["stops"].map({"zero": 0, "one": 1, "two_or_more": 2}).fillna(1)
    df = df[(df["source_city"].str.contains(from_city, case=False, na=False)) &
            (df["destination_city"].str.contains(to_city, case=False, na=False))]
    if df.empty:
        return df
    df["value_score"] = (10000 - df["price"]) - (df["duration"] * 200) - (df["stops"] * 500)
    return df


def _prepare_hotels(city: str) -> pd.DataFrame:
    df = _load_csv("hotels", "hotels.csv")
    if df.empty:
        return df
    df = df.copy()
    df = df[df["city"].str.contains(city, case=False, na=False)]
    df["hotel_star_rating"] = df["hotel_star_rating"].apply(_safe_float)
    df["site_review_rating"] = df["site_review_rating"].apply(_safe_float)
    df["review_count"] = df["site_review_count"].apply(_safe_float)
    df["estimated_price"] = (df["hotel_star_rating"].clip(lower=1) * 1500) + (df["site_review_rating"].clip(lower=0) * 200)
    df["value_score"] = (df["site_review_rating"] * 20) - (df["estimated_price"] / 100)
    return df


def _prepare_restaurants(city: str) -> pd.DataFrame:
    df = _load_csv("restaurants", "restaurants.csv")
    if df.empty:
        return df
    df = df.copy()
    df = df[df["location"].str.contains(city, case=False, na=False)]
    df["rating"] = df["rating"].apply(_safe_float)
    df["average_price"] = df["average_price"].apply(_safe_float)
    df["value_score"] = (df["rating"] * 20) - (df["average_price"] / 50)
    return df


def _prepare_attractions(city: str) -> pd.DataFrame:
    df = _load_csv("attractions", "attractions.csv")
    if df.empty:
        return df
    df = df.copy()
    df = df[df["City"].str.contains(city, case=False, na=False)]
    df["rating"] = df["Google review rating"].apply(_safe_float)
    df["fee"] = df["Entrance Fee in INR"].apply(_safe_float)
    df["time_needed"] = df["time needed to visit in hrs"].apply(_safe_float)
    df["value_score"] = (df["rating"] * 20) - (df["fee"] / 20)
    return df


def recommend_trip(
    from_city: Optional[str],
    to_city: str,
    budget: float,
    start_date: str,
    end_date: str,
    people: int,
    travel_mode: str,
    interests: Optional[List[str]] = None,
) -> dict:
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    days = int((end_dt.date() - start_dt.date()).days) + 1
    days = max(days, 1)

    transport_budget = budget * 0.2
    hotel_budget = budget * 0.4
    food_budget = budget * 0.25
    attraction_budget = budget * 0.15

    transport = None
    if from_city:
        if travel_mode.lower() == "flight":
            flights = _prepare_flights(from_city, to_city)
            if not flights.empty:
                model = _train_model("flights", flights, ["price", "duration", "stops"], "value_score")
                dtest = xgb.DMatrix(flights[["price", "duration", "stops"]].fillna(0.0).to_numpy())
                flights["score"] = model.predict(dtest)
                flights = flights.sort_values(by=["score", "price"], ascending=[False, True])
                top = flights.iloc[0]
                transport = {
                    "type": "flight",
                    "name": f"{top['airline']} {top['flight']}",
                    "price": float(top["price"]) * people,
                    "details": {
                        "from": top["source_city"],
                        "to": top["destination_city"],
                        "duration": float(top["duration"]),
                        "stops": int(top["stops"]),
                    },
                }
        elif travel_mode.lower() == "train":
            trains = _load_trains_json()
            for item in trains:
                if item.get("errorMessage"):
                    continue
                stations = _parse_station_list(item.get("stationList"))
                if not stations:
                    continue
                if _station_name_contains(stations, from_city) and _station_name_contains(stations, to_city):
                    transport = {
                        "type": "train",
                        "name": item.get("trainName") or "",
                        "price": 0.0,
                        "details": {
                            "from": from_city,
                            "to": to_city,
                            "train_number": item.get("trainNumber"),
                        },
                    }
                    break
        else:
            # Auto: prefer cheapest available flight; fallback to train
            flights = _prepare_flights(from_city, to_city)
            if not flights.empty:
                flights = flights.sort_values(by=["price", "duration"])
                top = flights.iloc[0]
                transport = {
                    "type": "flight",
                    "name": f"{top['airline']} {top['flight']}",
                    "price": float(top["price"]) * people,
                    "details": {
                        "from": top["source_city"],
                        "to": top["destination_city"],
                        "duration": float(top["duration"]),
                        "stops": int(top["stops"]),
                    },
                }

    hotel = None
    hotels = _prepare_hotels(to_city)
    if not hotels.empty:
        model = _train_model("hotels", hotels, ["hotel_star_rating", "site_review_rating", "review_count", "estimated_price"], "value_score")
        dtest = xgb.DMatrix(hotels[["hotel_star_rating", "site_review_rating", "review_count", "estimated_price"]].fillna(0.0).to_numpy())
        hotels["score"] = model.predict(dtest)
        per_night_budget = hotel_budget / max(days - 1, 1)
        candidates = hotels[hotels["estimated_price"] <= per_night_budget]
        if candidates.empty:
            candidates = hotels
        candidates = candidates.sort_values(by=["score", "estimated_price"], ascending=[False, True])
        top = candidates.iloc[0]
        hotel = {
            "name": top.get("property_name") or "",
            "city": top.get("city") or "",
            "price_per_night": float(top["estimated_price"]) * people,
            "total_price": float(top["estimated_price"]) * max(days - 1, 1) * people,
            "rating": float(top.get("site_review_rating") or 0.0),
        }

    restaurants = _prepare_restaurants(to_city)
    if not restaurants.empty:
        model = _train_model("restaurants", restaurants, ["rating", "average_price"], "value_score")
        dtest = xgb.DMatrix(restaurants[["rating", "average_price"]].fillna(0.0).to_numpy())
        restaurants["score"] = model.predict(dtest)
        restaurants = restaurants.sort_values(by=["score", "average_price"], ascending=[False, True])

    attractions = _prepare_attractions(to_city)
    if not attractions.empty:
        if interests:
            interests_l = [i.strip().lower() for i in interests if i.strip()]
            if interests_l:
                attractions = attractions[
                    attractions["Significance"].str.lower().str.contains("|".join(interests_l), na=False)
                    | attractions["Type"].str.lower().str.contains("|".join(interests_l), na=False)
                ]
        model = _train_model("attractions", attractions, ["rating", "fee", "time_needed"], "value_score")
        dtest = xgb.DMatrix(attractions[["rating", "fee", "time_needed"]].fillna(0.0).to_numpy())
        attractions["score"] = model.predict(dtest)
        attractions = attractions.sort_values(by=["score", "fee"], ascending=[False, True])

    plan = []
    total_cost = 0.0
    per_day_food = food_budget / days
    per_day_attr = attraction_budget / days

    attraction_idx = 0
    restaurant_idx = 0

    for d in range(days):
        day_date = (start_dt.date() + pd.Timedelta(days=d)).isoformat()
        day_restaurants = []
        day_attractions = []
        day_cost = 0.0

        if not restaurants.empty:
            picks = 0
            while picks < 2 and restaurant_idx < len(restaurants):
                r = restaurants.iloc[restaurant_idx]
                restaurant_idx += 1
                cost = float(r.get("average_price", 0)) * people
                if day_cost + cost <= per_day_food:
                    day_restaurants.append({
                        "name": r.get("restaurant_name") or "",
                        "price": float(r.get("average_price") or 0.0),
                        "rating": float(r.get("rating") or 0.0),
                    })
                    day_cost += cost
                    picks += 1

        if not attractions.empty:
            picks = 0
            while picks < 3 and attraction_idx < len(attractions):
                a = attractions.iloc[attraction_idx]
                attraction_idx += 1
                cost = float(a.get("fee") or 0.0) * people
                if day_cost + cost <= (per_day_food + per_day_attr):
                    day_attractions.append({
                        "name": a.get("Name") or "",
                        "price": float(a.get("fee") or 0.0),
                        "rating": float(a.get("rating") or 0.0),
                        "type": a.get("Type") or "",
                    })
                    day_cost += cost
                    picks += 1

        plan.append({
            "date": day_date,
            "restaurants": day_restaurants,
            "attractions": day_attractions,
            "estimated_cost": round(day_cost, 2),
        })
        total_cost += day_cost

    if transport:
        total_cost += float(transport.get("price", 0.0))
    if hotel:
        total_cost += float(hotel.get("total_price", 0.0))

    remaining = max(0.0, round(budget - total_cost, 2))

    return {
        "city": to_city,
        "budget": budget,
        "people": people,
        "days": days,
        "travel_mode": travel_mode,
        "transport": transport,
        "hotel": hotel,
        "plan": plan,
        "total_estimated_cost": round(total_cost, 2),
        "remaining_budget": remaining,
    }
